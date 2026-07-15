import os
import shutil

# 路径配置
dataset_dir = "dataset"
train_dir = "train"
val_dir = "val"

# 遍历每一类文件夹
for cls_name in os.listdir(dataset_dir):
    cls_path = os.path.join(dataset_dir, cls_name)
    # 只处理文件夹，跳过文件
    if not os.path.isdir(cls_path):
        continue

    # 自动创建train/val下对应的type文件夹
    target_train_cls = os.path.join(train_dir, cls_name)
    target_val_cls = os.path.join(val_dir, cls_name)
    os.makedirs(target_train_cls, exist_ok=True)
    os.makedirs(target_val_cls, exist_ok=True)

    # 获取当前类别所有图片并排序
    imgs = sorted(os.listdir(cls_path))
    train_imgs = imgs[:2]
    val_imgs = imgs[2:]

    # 复制训练图片
    for img in train_imgs:
        src = os.path.join(cls_path, img)
        dst = os.path.join(target_train_cls, img)
        shutil.copy(src, dst)
    # 复制验证图片
    for img in val_imgs:
        src = os.path.join(cls_path, img)
        dst = os.path.join(target_val_cls, img)
        shutil.copy(src, dst)

print("训练集、验证集划分完毕！每类2张训练，1张验证")