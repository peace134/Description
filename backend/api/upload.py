from flask import request
import cv2
import base64
import numpy as np
import logging

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

        # 模型推理
        class_id, class_name, confidence = model.predict(image)

        # 检测卡牌位置
        circles = visualizer.detect_cards(image)
        metadata = {'bbox': None}
        if circles:
            x, y, r = circles[0]
            metadata['bbox'] = (x - r, y - r, x + r, y + r)

        # 可视化标注
        annotated_image = visualizer.annotate(image, class_name, confidence, metadata)
        annotated_path = file_manager.save_annotated(annotated_image, file_id)

        # 保存结果
        result_data = {
            'class_id': class_id,
            'class_name': class_name,
            'confidence': confidence,
            'original_file': original_name,
            'upload_path': str(file_path),
            'annotated_path': str(annotated_path)
        }
        file_manager.save_result(file_id, result_data)

        # 返回 Base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        data_url = f'data:image/jpeg;base64,{img_base64}'

        return success_response({
            'file_id': file_id,
            'category': class_name,
            'confidence': confidence,
            'annotated_image': data_url,
            'download_url': f'/api/download/{file_id}'
        })

    except Exception as e:
        logger.error(f"识别失败: {str(e)}", exc_info=True)
        return error_response(f'识别失败: {str(e)}', status_code=500)