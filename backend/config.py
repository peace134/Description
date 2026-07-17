from pathlib import Path
import json


class Config:
    """应用配置"""
    BASE_DIR = Path(__file__).parent

    # 存储路径
    UPLOAD_FOLDER = BASE_DIR / 'storage' / 'uploads'
    ANNOTATED_FOLDER = BASE_DIR / 'storage' / 'annotated'
    RESULT_FOLDER = BASE_DIR / 'storage' / 'results'

    for folder in [UPLOAD_FOLDER, ANNOTATED_FOLDER, RESULT_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)

    # 文件限制
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True

    # ========== 模型配置 ==========
    # 使用 MobileNetV3 版本
    MODEL_TYPE = 'mobilenetv3'  # 或 'opencv'

    # MobileNetV3 配置
    MOBILENETV3_DIR = BASE_DIR / 'mobilenetv3'
    MODEL_PATH = MOBILENETV3_DIR / 'mobilenetv3_small.pth'
    CLASS_INDICES_PATH = MOBILENETV3_DIR / 'class_indices.json'

    # 类别数量
    NUM_CLASSES = 12

    # 加载类别映射
    with open(CLASS_INDICES_PATH, 'r', encoding='utf-8') as f:
        CLASS_INDICES = json.load(f)  # {"0": "class_name", ...}

    # 反转映射：name -> id
    CLASS_NAME_TO_ID = {v: int(k) for k, v in CLASS_INDICES.items()}

    # 标注配置
    ANNOTATION_COLOR = (246, 184, 61)
    THICKNESS = 2