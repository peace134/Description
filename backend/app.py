from flask import Flask
from flask_cors import CORS
import logging

from config import Config
from api.routes import api_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    CORS(app, origins=['http://localhost:8080', 'http://127.0.0.1:8080', '*'])
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(error):
        from utils.response import error_response
        return error_response('接口不存在', status_code=404)

    @app.errorhandler(500)
    def internal_error(error):
        from utils.response import error_response
        return error_response('服务器内部错误', status_code=500)

    logger.info("🚀 卡牌大师后端服务启动")
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)