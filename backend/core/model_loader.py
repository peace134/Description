import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# 导入 MobileNetV3 模型
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'mobilenetv3'))
from mobilenetv3 import MobileNetV3_Small


class CardClassifier:
    """卡牌分类器 - MobileNetV3"""

    def __init__(self, model_path, class_indices_path, num_classes=12, device='cpu'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.num_classes = num_classes

        # 加载类别映射
        with open(class_indices_path, 'r', encoding='utf-8') as f:
            self.class_indices = json.load(f)

        # 创建模型
        self.model = MobileNetV3_Small(num_classes=num_classes)

        # 加载权重
        if model_path and model_path.exists():
            try:
                # 加载整个文件
                checkpoint = torch.load(model_path, map_location=self.device)

                # 检查是否是字典格式
                if isinstance(checkpoint, dict):
                    # 如果有 model_state_dict，提取它
                    if 'model_state_dict' in checkpoint:
                        state_dict = checkpoint['model_state_dict']
                        logger.info(f"📦 从 checkpoint 中提取 model_state_dict")
                        logger.info(f"   epoch: {checkpoint.get('epoch', 'unknown')}")
                        logger.info(f"   num_classes: {checkpoint.get('num_classes', 'unknown')}")
                    else:
                        # 直接使用整个字典作为 state_dict
                        state_dict = checkpoint
                else:
                    state_dict = checkpoint

                # 加载权重
                self.model.load_state_dict(state_dict)
                logger.info(f"✅ 模型加载成功: {model_path}")

            except Exception as e:
                logger.error(f"❌ 模型加载失败: {e}")
                raise
        else:
            logger.warning(f"⚠️ 模型文件不存在: {model_path}")
            raise FileNotFoundError(f"模型文件未找到: {model_path}")

        self.model.to(self.device)
        self.model.eval()

        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def predict(self, image):
        """
        预测单张图片
        Returns:
            (class_id, class_name, confidence)
        """
        # 转换为 PIL Image
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        elif isinstance(image, str):
            image = Image.open(image)

        # 预处理
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 推理
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, class_id = torch.max(probabilities, 1)

        class_id = class_id.item()
        confidence = confidence.item()

        # 从映射中获取类别名称
        class_name = self.class_indices.get(str(class_id), f"class_{class_id}")

        logger.info(f"🎯 识别结果: {class_name} (ID: {class_id}), 置信度: {confidence:.3f}")
        return class_id, class_name, confidence


# 单例模式
_model_instance = None


def get_model():
    global _model_instance
    if _model_instance is None:
        from config import Config
        _model_instance = CardClassifier(
            model_path=Config.MODEL_PATH,
            class_indices_path=Config.CLASS_INDICES_PATH,
            num_classes=Config.NUM_CLASSES
        )
    return _model_instance