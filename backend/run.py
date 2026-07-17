#!/usr/bin/env python
import sys
from app import app
from config import Config

if __name__ == '__main__':
    print("🃏 卡牌大师后端服务")
    print("=" * 50)
    print(f"📍 地址: http://{Config.HOST}:{Config.PORT}")
    print(f"📡 接口: POST /api/upload")
    print(f"📥 下载: GET /api/download/{{file_id}}")
    print(f"📊 结果: GET /api/result/{{file_id}}")
    print("=" * 50)

    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)