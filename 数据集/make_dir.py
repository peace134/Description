import os
import shutil

base = os.path.dirname(os.path.abspath(__file__))
card_out_path = os.path.join(base, "card_out")
dataset_path = os.path.join(base, "dataset")

rows = 5
cols = 11
class_id = 1
# 10张原图全部参与分类
pic_nums = [1,2,3,4,5,6,7,8,9,10]

# 遍历5行11列共55类卡牌
for r in range(rows):
    for c in range(cols):
        # 创建当前类别文件夹 type01 ~ type55
        cls_folder = os.path.join(dataset_path, f"type{class_id:02d}")
        os.makedirs(cls_folder, exist_ok=True)
        # 循环10张原图同位置卡牌复制进对应分类
        for pic in pic_nums:
            src_file = os.path.join(card_out_path, f"{pic}_r{r}_c{c}.png")
            dst_file = os.path.join(cls_folder, f"{pic}_r{r}_c{c}.png")
            if os.path.exists(src_file):
                shutil.copy(src_file, dst_file)
            else:
                print(f"缺失文件：{src_file}")
        class_id += 1
print("全部type文件夹填充图片完成！同坐标图案归为一类，色差忽略")