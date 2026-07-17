from flask import Blueprint
from api.upload import handle_upload
from api.download import handle_download, handle_result

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/upload', methods=['POST'])
def upload():
    return handle_upload()

@api_bp.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    return handle_download(file_id)

@api_bp.route('/result/<file_id>', methods=['GET'])
def get_result(file_id):
    return handle_result(file_id)

@api_bp.route('/health', methods=['GET'])
def health():
    from utils.response import success_response
    return success_response({'status': 'ok'}, '服务运行正常')