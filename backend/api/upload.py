from flask import request
import cv2
import base64
import numpy as np
import logging
from PIL import Image, ImageDraw, ImageFont

from utils.response import success_response, error_response
from utils.file_manager import FileManager
from core.model_loader import get_model
from core.visualizer import CardVisualizer
from config import Config

logger = logging.getLogger(__name__)

file_manager = FileManager(
    Config.UPLOAD_FOLDER,
    Config.ANNOTATED_FOLDER,
    Config.RESULT_FOLDER
)
model = get_model()
visualizer = CardVisualizer(Config)


def handle_upload():
    try:
        if 'file' not in request.files:
            return error_response('没有上传文件')

        file = request.files['file']
        if file.filename == '':
            return error_response('文件名为空')

        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in Config.ALLOWED_EXTENSIONS:
            return error_response(f'不支持的文件类型: {ext}')

        # 先读取文件内容
        img_bytes = file.read()
        logger.info(f"📥 接收到文件: {file.filename}, 大小: {len(img_bytes)} bytes")
        
        # 验证图片数据唯一性
        import hashlib
        img_hash = hashlib.md5(img_bytes).hexdigest()[:8]
        logger.info(f"🔑 图片MD5: {img_hash}")
        
        # 重置文件指针，以便 save_upload 可以再次读取
        file.seek(0)
        
        file_id, file_path, original_name = file_manager.save_upload(file)
        logger.info(f"🆔 生成 file_id: {file_id}")

        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            logger.error(f"❌ 图片解码失败: {file.filename}")
            return error_response('图片解码失败')
        
        logger.info(f"🖼️ 图片尺寸: {image.shape[1]}x{image.shape[0]}, 文件名: {file.filename}")
        logger.info(f"📊 图片数据摘要: {img_bytes[:20].hex()}")  # 打印前20字节的hex用于对比

        # ========== 1. 检测所有卡牌 ==========
        circles = visualizer.detect_cards(image)

        if not circles:
            logger.warning("⚠️ 未检测到卡牌，尝试整图识别")
            class_id, class_name, confidence = model.predict(image)
            results = [{
                'class_id': class_id,
                'class_name': class_name,
                'confidence': confidence,
                'bbox': [0, 0, image.shape[1], image.shape[0]]
            }]
        else:
            # ========== 2. 逐个识别每张卡牌 ==========
            results = []
            for circle in circles:
                x, y, r = circle

                # 提取卡牌区域（稍微扩大一点确保完整）
                margin = 5
                x1 = max(0, int(x) - int(r) - margin)
                y1 = max(0, int(y) - int(r) - margin)
                x2 = min(image.shape[1], int(x) + int(r) + margin)
                y2 = min(image.shape[0], int(y) + int(r) + margin)

                card_roi = image[y1:y2, x1:x2]

                if card_roi.size == 0:
                    continue

                # 识别单张卡牌
                class_id, class_name, confidence = model.predict(card_roi)
                logger.info(f"🎴 卡牌识别: {class_name} ({confidence:.2%}) at ({x1},{y1})-({x2},{y2})")

                results.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'center': [int(x), int(y)],
                    'radius': int(r)
                })

        # ========== 3. 在图上标注所有卡牌（不遮挡图案） ==========
        annotated_image = draw_clean_annotations(image, results)
        annotated_path = file_manager.save_annotated(annotated_image, file_id)

        # ========== 4. 保存结果 ==========
        result_data = {
            'total_cards': len(results),
            'results': results,
            'original_file': original_name,
            'upload_path': str(file_path),
            'annotated_path': str(annotated_path)
        }
        file_manager.save_result(file_id, result_data)

        # ========== 5. 返回 Base64 ==========
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        data_url = f'data:image/jpeg;base64,{img_base64}'

        # 构建返回结果
        card_results = []
        for r in results:
            card_results.append({
                'category': r['class_name'],
                'confidence': r['confidence'],
                'bbox': r['bbox']
            })

        return success_response({
            'file_id': file_id,
            'total_cards': len(results),
            'cards': card_results,
            'annotated_image': data_url,
            'download_url': f'/api/download/{file_id}'
        })

    except Exception as e:
        logger.error(f"识别失败: {str(e)}", exc_info=True)
        return error_response(f'识别失败: {str(e)}', status_code=500)


def draw_clean_annotations(image, results):
    """
    在图上标注所有卡牌 - 矩形边框样式
    """
    img = image.copy()
    h, w = img.shape[:2]

    # 使用 PIL 绘制
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("simhei.ttf", 14)
    except:
        font = ImageFont.load_default()

    # 简洁配色方案
    colors = [
        (0, 255, 0),     # 绿色
        (255, 0, 0),     # 红色
        (0, 0, 255),     # 蓝色
        (255, 255, 0),   # 黄色
        (255, 0, 255),   # 紫色
        (0, 255, 255),   # 青色
        (255, 165, 0),   # 橙色
        (128, 0, 128),   # 深紫
    ]

    for i, result in enumerate(results):
        x1, y1, x2, y2 = result['bbox']
        class_name = result['class_name']
        confidence = result['confidence']
        color = colors[i % len(colors)]

        # ========== 1. 绘制矩形边框 ==========
        draw.rectangle(
            [x1, y1, x2, y2],
            outline=color,
            width=2
        )

        # ========== 2. 类别标签（边框上方） ==========
        label = f"{class_name[:10]} ({confidence:.2f})"

        # 测量文字宽度
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 标签位置：边框上方
        label_x = x1
        label_y = y1 - text_h - 4

        # 如果上方空间不够，放在边框内部上方
        if label_y < 0:
            label_y = y1 + 2

        # 白色描边（让文字在任何背景上都清晰）
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text(
                (label_x + dx, label_y + dy),
                label,
                fill=(0, 0, 0),
                font=font
            )
        # 彩色文字
        draw.text((label_x, label_y), label, fill=color, font=font)

    # 转换回 OpenCV
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)