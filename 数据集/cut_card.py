from PIL import Image
import os

# 获取脚本所在文件夹路径
base = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(base, "img")
out_dir = os.path.join(base, "card_out")

# 创建文件夹
os.makedirs(img_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

rows = 5
cols = 11
img_names = [f"{i}.jpg" for i in range(1, 11)]

for name in img_names:
    full_path = os.path.join(img_dir, name)
    if not os.path.exists(full_path):
        print(f"文件不存在：{full_path}")
        continue
    try:
        img = Image.open(full_path)
    except Exception as e:
        print(f"图片读取失败 {full_path}，错误：{e}")
        continue
    w, h = img.size
    cell_h = h // rows
    cell_w = w // cols
    for r in range(rows):
        for c in range(cols):
            x1 = c * cell_w
            y1 = r * cell_h
            x2 = x1 + cell_w
            y2 = y1 + cell_h
            crop = img.crop((x1, y1, x2, y2))
            save_name = f"{name[:-4]}_r{r}_c{c}.png"
            crop.save(os.path.join(out_dir, save_name))
print("全部原图裁剪完成！")