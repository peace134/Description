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
    在图上标注所有卡牌 - 不遮挡图案
    """
    img = image.copy()
    h, w = img.shape[:2]

    # 使用 PIL 绘制
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("simhei.ttf", 18)
        font_small = ImageFont.truetype("simhei.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_small = font

    for i, result in enumerate(results):
        x1, y1, x2, y2 = result['bbox']
        class_name = result['class_name']
        confidence = result['confidence']
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        radius = (x2 - x1) // 2

        # ========== 不同颜色的边框 ==========
        colors = [
            (246, 184, 61),  # 金色
            (167, 139, 250),  # 紫色
            (34, 197, 94),  # 绿色
            (59, 130, 246),  # 蓝色
            (236, 72, 153),  # 粉色
            (239, 68, 68),  # 红色
            (251, 191, 36),  # 黄色
            (52, 211, 153),  # 青色
        ]
        color = colors[i % len(colors)]

        # ========== 画圆形边框（不遮挡图案） ==========
        # 画在圆的外围，不覆盖图案内容
        for j in range(2, 0, -1):
            offset = j * 3
            draw.ellipse(
                [center_x - radius - offset, center_y - radius - offset,
                 center_x + radius + offset, center_y + radius + offset],
                outline=(color[0], color[1], color[2], max(80, 255 - j * 80)),
                width=max(1, j)
            )

        # 主圆形边框（虚线效果 - 用点画圆）
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            outline=color,
            width=2
        )

        # ========== 标签放在卡牌外部（不遮挡图案） ==========
        label = f"{i + 1}.{class_name[:8]} {int(confidence * 100)}%"

        # 测量文字宽度
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 标签位置：放在卡牌正下方
        label_x = center_x - text_w // 2
        label_y = y2 + 8

        # 如果下方空间不够，放在上方
        if label_y + text_h > h - 10:
            label_y = y1 - text_h - 8

        # 如果上方也不够，放在左右两侧
        if label_y < 0:
            # 放在右侧
            label_x = x2 + 8
            label_y = center_y - text_h // 2
            # 如果右侧不够，放在左侧
            if label_x + text_w > w - 10:
                label_x = x1 - text_w - 8

        # 半透明背景（让文字更清晰但不遮挡图案）
        bg_padding = 6
        draw.rectangle(
            [label_x - bg_padding, label_y - bg_padding,
             label_x + text_w + bg_padding, label_y + text_h + bg_padding],
            fill=(11, 17, 32, 180)  # 半透明深色背景
        )

        # 描边文字（更清晰）
        # 白色描边
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text(
                (label_x + dx, label_y + dy),
                label,
                fill=(0, 0, 0),
                font=font
            )
        # 主文字
        draw.text((label_x, label_y), label, fill=color, font=font)

        # ========== 编号小标签（卡牌角落，半透明） ==========
        num_label = str(i + 1)
        num_bbox = draw.textbbox((0, 0), num_label, font=font_small)
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]

        # 编号放在卡牌左上角（半透明，不遮挡图案）
        num_x = x1 + 6
        num_y = y1 + 6

        # 半透明圆形背景
        draw.ellipse(
            [num_x - 8, num_y - 8, num_x + num_w + 8, num_y + num_h + 8],
            fill=(11, 17, 32, 160)
        )
        draw.text((num_x, num_y), num_label, fill=(255, 255, 255), font=font_small)

    # 转换回 OpenCV
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)