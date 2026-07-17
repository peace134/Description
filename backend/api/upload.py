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

        file_id, file_path, original_name = file_manager.save_upload(file)

        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return error_response('图片解码失败')

        # ========== 1. 检测所有卡牌 ==========
        circles = visualizer.detect_cards(image)

        if not circles:
            logger.warning("⚠️ 未检测到卡牌，尝试整图识别")
            # 如果没有检测到卡牌，把整张图当作一张卡牌识别
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

                # 提取卡牌区域（扩大一点）
                margin = 10
                x1 = max(0, int(x) - int(r) - margin)
                y1 = max(0, int(y) - int(r) - margin)
                x2 = min(image.shape[1], int(x) + int(r) + margin)
                y2 = min(image.shape[0], int(y) + int(r) + margin)

                card_roi = image[y1:y2, x1:x2]

                if card_roi.size == 0:
                    continue

                # 识别单张卡牌
                class_id, class_name, confidence = model.predict(card_roi)

                results.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'center': [int(x), int(y)]
                })

        # ========== 3. 在图上标注所有卡牌 ==========
        annotated_image = draw_all_annotations(image, results, visualizer)
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

        # 构建返回结果（每张卡牌）
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


def draw_all_annotations(image, results, visualizer):
    """
    在图上标注所有卡牌
    """
    img = image.copy()
    h, w = img.shape[:2]

    # 使用 PIL 绘制
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("simhei.ttf", 20)
    except:
        font = ImageFont.load_default()

    for i, result in enumerate(results):
        x1, y1, x2, y2 = result['bbox']
        class_name = result['class_name']
        confidence = result['confidence']

        # 绘制边框（不同颜色）
        colors = [
            (246, 184, 61),  # 金色
            (167, 139, 250),  # 紫色
            (34, 197, 94),  # 绿色
            (239, 68, 68),  # 红色
            (59, 130, 246),  # 蓝色
            (236, 72, 153),  # 粉色
        ]
        color = colors[i % len(colors)]

        # 边框
        for j in range(3, 0, -1):
            offset = j * 2
            draw.rectangle(
                [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
                outline=(color[0], color[1], color[2], max(50, 255 - j * 60)),
                width=max(1, j)
            )

        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # 标签背景
        label = f"{i + 1}. {class_name} {int(confidence * 100)}%"
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 标签位置（在框上方）
        label_x = x1
        label_y = y1 - text_h - 10

        # 如果超出顶部，放在框内部
        if label_y < 0:
            label_y = y1 + 5

        draw.rectangle(
            [label_x - 5, label_y - 5, label_x + text_w + 5, label_y + text_h + 5],
            fill=(11, 17, 32, 220)
        )
        draw.text((label_x, label_y), label, fill=color, font=font)

        # 编号圆圈（左上角）
        circle_x = x1 + 20
        circle_y = y1 + 20
        draw.ellipse(
            [circle_x - 12, circle_y - 12, circle_x + 12, circle_y + 12],
            fill=color,
            outline=(255, 255, 255)
        )
        draw.text(
            (circle_x - 6, circle_y - 10),
            str(i + 1),
            fill=(255, 255, 255),
            font=font
        )

    # 转换回 OpenCV
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)