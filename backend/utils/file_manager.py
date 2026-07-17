import os
import uuid
from datetime import datetime
from pathlib import Path
import json
import logging
import cv2

logger = logging.getLogger(__name__)


class FileManager:
    def __init__(self, upload_folder, annotated_folder, result_folder):
        self.upload_folder = Path(upload_folder)
        self.annotated_folder = Path(annotated_folder)
        self.result_folder = Path(result_folder)

        for folder in [self.upload_folder, self.annotated_folder, self.result_folder]:
            folder.mkdir(parents=True, exist_ok=True)

    def save_upload(self, file):
        file_id = self._generate_id()
        original_name = file.filename
        ext = os.path.splitext(original_name)[1]
        filename = f"{file_id}{ext}"
        file_path = self.upload_folder / filename
        file.save(str(file_path))
        logger.info(f"📁 文件已保存: {filename}")
        return file_id, file_path, original_name

    def save_annotated(self, image_array, file_id):
        filename = f"{file_id}_annotated.jpg"
        file_path = self.annotated_folder / filename
        cv2.imwrite(str(file_path), image_array)
        logger.info(f"🏷️ 标注图已保存: {filename}")
        return file_path

    def save_result(self, file_id, result_data):
        filename = f"{file_id}_result.json"
        file_path = self.result_folder / filename
        result_data['file_id'] = file_id
        result_data['timestamp'] = datetime.now().isoformat()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 结果已保存: {filename}")
        return file_path

    def get_file_path(self, file_id, file_type='annotated'):
        folders = {
            'upload': self.upload_folder,
            'annotated': self.annotated_folder,
            'result': self.result_folder
        }
        folder = folders.get(file_type)
        if not folder:
            return None

        patterns = {
            'upload': [f"{file_id}.jpg", f"{file_id}.jpeg", f"{file_id}.png", f"{file_id}.webp"],
            'annotated': [f"{file_id}_annotated.jpg"],
            'result': [f"{file_id}_result.json"]
        }

        for pattern in patterns.get(file_type, []):
            path = folder / pattern
            if path.exists():
                return path
        return None

    def _generate_id(self):
        # 使用微秒级时间戳 + UUID 确保唯一性
        import time
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # %f 是微秒
        unique_id = uuid.uuid4().hex[:6]
        return f"{timestamp}_{unique_id}"