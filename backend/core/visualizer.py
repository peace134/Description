import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class CardVisualizer:
    """卡牌标注可视化工具"""

    def __init__(self, config):
        self.config = config
        self.color = config.ANNOTATION_COLOR
        self.thickness = config.THICKNESS

        # 加载类别映射
        with open(config.CLASS_INDICES_PATH, 'r', encoding='utf-8') as f:
            self.class_indices = json.load(f)

    def annotate(self, image, class_name, confidence, metadata=None):
        """
        在图片上绘制标注
        """
        img = image.copy()
        h, w = img.shape[:2]

        # 绘制边框
        margin = int(min(h, w) * 0.05)
        for i in range(8, 0, -2):
            offset = i
            cv2.rectangle(
                img,
                (margin - offset, margin - offset),
                (w - margin + offset, h - margin + offset),
                self.color,
                max(1, i // 4),
                lineType=cv2.LINE_AA
            )

        cv2.rectangle(
            img,
            (margin, margin),
            (w - margin, h - margin),
            self.color,
            self.thickness + 1,
            lineType=cv2.LINE_AA
        )

        # 使用 PIL 绘制文字
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        try:
            font = ImageFont.truetype("simhei.ttf", 28)
        except:
            font = ImageFont.load_default()

        # 类别标签（左上角）
        label_x, label_y = margin + 10, margin + 10
        draw.text((label_x, label_y), class_name, fill=(246, 184, 61), font=font)

        # 置信度标签（右上角）
        conf_text = f"{int(confidence * 100)}%"
        conf_bbox = draw.textbbox((0, 0), conf_text, font=font)
        conf_w = conf_bbox[2] - conf_bbox[0]
        conf_h = conf_bbox[3] - conf_bbox[1]
        conf_x = w - margin - conf_w - 20
        conf_y = margin + 10

        draw.rectangle(
            [conf_x - 10, conf_y - 5, conf_x + conf_w + 10, conf_y + conf_h + 5],
            fill=(34, 197, 94, 180)
        )
        draw.text((conf_x, conf_y), conf_text, fill=(255, 255, 255), font=font)

        img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        # 检测框（可选）
        if metadata and 'bbox' in metadata:
            x1, y1, x2, y2 = metadata['bbox']
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return img

    def detect_cards(self, image):
        """检测卡牌位置（使用霍夫圆）"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        h, w = image.shape[:2]
        min_radius = int(min(h, w) * 0.08)
        max_radius = int(min(h, w) * 0.15)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max_radius * 1.5,
            param1=50,
            param2=30,
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            return circles[0, :].tolist()
        return []