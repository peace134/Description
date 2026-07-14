import cv2
import os
import numpy as np

# 路径配置
input_dir = "img"
output_dir = "card_out"

# 创建输出文件夹
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 遍历img文件夹所有图片
for img_name in os.listdir(input_dir):
    if img_name.endswith((".jpg", ".png", ".jpeg")):
        img_path = os.path.join(input_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            print(f"无法读取图片：{img_name}，跳过")
            continue

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # 霍夫圆检测参数
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=160,
            param1=50,
            param2=32,
            minRadius=75,
            maxRadius=110
        )

        if circles is None:
            print(f"{img_name} 未检测到圆形卡片，跳过")
            continue

        circles = np.uint16(np.around(circles))
        circle_list = circles[0, :]
        # 从上到下、从左到右排序
        circle_list = sorted(circle_list, key=lambda p: (p[1], p[0]))

        # 提取图片数字作为编号（1/2/3）
        pic_id = img_name.split(".")[0]
        idx = 0
        for circle in circle_list:
            x, y, r = circle
            # 计算裁剪边界，先转int避免无符号溢出
            offset = 10
            x1 = int(x) - int(r) - offset
            y1 = int(y) - int(r) - offset
            x2 = int(x) + int(r) + offset
            y2 = int(y) + int(r) + offset

            # 边界约束，保证坐标合法，不会出现负尺寸
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            # 校验裁剪区域有效，宽高必须大于0
            crop_w = x2 - x1
            crop_h = y2 - y1
            if crop_w <= 0 or crop_h <= 0:
                print(f"跳过边界无效圆形 {x},{y}")
                continue

            card_crop = img[y1:y2, x1:x2]
            save_name = f"{pic_id}_card_{idx}.png"
            save_full_path = os.path.join(output_dir, save_name)
            cv2.imwrite(save_full_path, card_crop)
            idx += 1

        print(f"图片 {img_name} 裁剪完成，共输出 {idx} 张卡牌")

print("===== 全部图片裁剪完成 =====")