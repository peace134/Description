import requests
import os
import base64
import glob
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000/api"

# 支持的图片格式
IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp']


def upload_single_image(file_path, output_dir="output"):
    """上传单张图片并识别"""
    url = f"{BASE_URL}/upload"
    filename = Path(file_path).name
    
    print(f"\n{'='*50}")
    print(f"📤 正在上传: {filename}")
    print(f"{'='*50}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(url, files=files, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return False
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            print(f"❌ 响应解析失败: {response.text[:200]}")
            return False
        
        if data.get('code') == 0:
            print(f"✅ 识别成功")
            print(f"  卡牌数量: {data['data']['total_cards']}")
            
            for i, card in enumerate(data['data']['cards'], 1):
                print(f"\n  卡牌 {i}:")
                print(f"    类别: {card['category']}")
                print(f"    置信度: {card['confidence']}")
                print(f"    位置: {card['bbox']}")
            
            # 保存标注图（同名文件直接覆盖）
            os.makedirs(output_dir, exist_ok=True)
            img_data = data['data']['annotated_image'].split(',')[1]
            output_path = os.path.join(output_dir, f"annotated_{filename}")
            
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(img_data))
            print(f"\n  🖼️ 标注图已保存: {output_path}")
            print(f"  🔗 下载链接: {data['data']['download_url']}")
            return True
        else:
            print(f"❌ 识别失败: {data.get('message', '未知错误')}")
            print(f"   完整响应: {data}")
            return False
    else:
        print(f"❌ HTTP 请求失败: {response.status_code}")
        print(f"   响应内容: {response.text[:500]}")
        return False


def test_upload_batch(image_dir="test_images", output_dir="output"):
    """批量上传识别指定目录下的所有图片"""
    print("\n" + "="*50)
    print("🚀 批量图片识别测试")
    print("="*50)
    
    # 收集所有图片文件（使用 set 去重，避免 Windows 大小写不敏感导致重复）
    image_files = set()
    for ext in IMAGE_EXTENSIONS:
        for f in glob.glob(os.path.join(image_dir, ext)):
            image_files.add(os.path.abspath(f))
    
    image_files = sorted(list(image_files))
    
    if not image_files:
        print(f"❌ 在目录 '{image_dir}' 中未找到图片文件")
        print(f"   支持的格式: {', '.join(IMAGE_EXTENSIONS)}")
        print(f"   请将图片放入 '{image_dir}' 目录后重试")
        return
    
    print(f"\n📁 找到 {len(image_files)} 张图片:")
    for i, f in enumerate(image_files, 1):
        print(f"  {i}. {Path(f).name}")
    
    # 批量处理
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(image_files, 1):
        print(f"\n📊 进度: {i}/{len(image_files)}")
        if upload_single_image(file_path, output_dir):
            success_count += 1
        else:
            fail_count += 1
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("📊 批量识别结果汇总")
    print(f"{'='*50}")
    print(f"  总计: {len(image_files)} 张")
    print(f"  ✅ 成功: {success_count} 张")
    print(f"  ❌ 失败: {fail_count} 张")
    print(f"  📈 成功率: {success_count/len(image_files)*100:.1f}%")
    print(f"{'='*50}")


def test_upload_single():
    """测试上传单张图片（兼容旧版）"""
    file_path = "test_images/test.jpg"
    
    if not os.path.exists(file_path):
        print(f"❌ 测试图片不存在: {file_path}")
        print(f"   请创建 test.jpg 或使用批量测试模式")
        return
    
    upload_single_image(file_path)


def test_health():
    """测试健康检查"""
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    print(f"健康检查: {response.json()}")


if __name__ == "__main__":
    test_health()
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 单张图片测试 (test.jpg)")
    print("2. 批量图片测试 (test_images/ 目录)")
    
    choice = input("\n请输入选项 (1/2) [默认2]: ").strip() or "2"
    
    if choice == "1":
        test_upload_single()
    else:
        test_upload_batch()