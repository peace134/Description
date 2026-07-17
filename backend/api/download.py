from flask import send_file
import logging

from utils.response import error_response
from utils.file_manager import FileManager
from config import Config

logger = logging.getLogger(__name__)

file_manager = FileManager(
    Config.UPLOAD_FOLDER,
    Config.ANNOTATED_FOLDER,
    Config.RESULT_FOLDER
)

def handle_download(file_id):
    try:
        annotated_path = file_manager.get_file_path(file_id, 'annotated')
        if not annotated_path or not annotated_path.exists():
            return error_response('文件不存在', status_code=404)
        return send_file(annotated_path, as_attachment=True, download_name=f"{file_id}_annotated.jpg")
    except Exception as e:
        logger.error(f"下载失败: {str(e)}", exc_info=True)
        return error_response(f'下载失败: {str(e)}', status_code=500)

def handle_result(file_id):
    try:
        result_path = file_manager.get_file_path(file_id, 'result')
        if not result_path or not result_path.exists():
            return error_response('结果不存在', status_code=404)
        import json
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        from utils.response import success_response
        return success_response(data)
    except Exception as e:
        logger.error(f"获取结果失败: {str(e)}", exc_info=True)
        return error_response(f'获取结果失败: {str(e)}', status_code=500)