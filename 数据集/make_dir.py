import os
import shutil

# 定义路径（之前缺失这两行，程序找不到文件夹）
src_dir = "card_out"
target_root = "dataset"

# 1. 批量创建 type01 ~ type55 文件夹
for i in range(55):
    folder_name = f"type{i+1:02d}"
    folder_path = os.path.join(target_root, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# 2. 遍历所有裁剪图片，自动分类
for filename in os.listdir(src_dir):
    if "_card_" not in filename:
        continue
    # 修复错误：删掉不存在的 old、new 变量
    idx_str = filename.split("_card_")[-1].replace(".png", "")
    idx = int(idx_str)
    target_folder = os.path.join(target_root, f"type{idx+1:02d}")
    src_file = os.path.join(src_dir, filename)
    dst_file = os.path.join(target_folder, filename)
    shutil.copy(src_file, dst_file)

print("图片分类完成，全部存入dataset文件夹！")