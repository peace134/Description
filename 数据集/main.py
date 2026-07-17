import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

# 预处理
trans = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.RandomHorizontalFlip(0.5),
    transforms.ToTensor()
])

# 只加载训练、验证集，删除test相关代码
train_data = datasets.ImageFolder(root="train", transform=trans)
val_data = datasets.ImageFolder(root="val", transform=trans)

train_loader = DataLoader(train_data, batch_size=4, shuffle=True)
val_loader = DataLoader(val_data, batch_size=4, shuffle=False)

# 迁移学习ResNet18
model = models.resnet18(pretrained=True)
for param in model.parameters():
    param.requires_grad = False
in_dim = model.fc.in_features
model.fc = nn.Linear(in_dim, 55)

loss_fn = nn.CrossEntropyLoss()

# 训练主逻辑+早停
if __name__ == "__main__":
    optimizer = torch.optim.Adam(model.fc.parameters(), lr=0.0001)
    epoch_total = 20
    best_val_loss = float("inf")
    patience = 3
    stop_count = 0

    for epoch in range(epoch_total):
        model.train()
        train_loss = 0
        for imgs, labels in train_loader:
            optimizer.zero_grad()
            out = model(imgs)
            loss = loss_fn(out, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                out = model(imgs)
                val_loss += loss_fn(out, labels).item()
        print(f"Epoch {epoch+1} | Train Loss:{train_loss:.2f} | Val Loss:{val_loss:.2f}")

        # 早停判断
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            stop_count = 0
        else:
            stop_count += 1
            if stop_count >= patience:
                print("验证损失持续上升，提前终止训练！")
                break