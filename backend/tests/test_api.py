import requests
import os
import base64

BASE_URL = "http://127.0.0.1:5000/api"


def test_upload():
    """测试上传识别"""
    url = f"{BASE_URL}/upload"
    file_path = "test.jpg"

    if not os.path.exists(file_path):
        print("❌ 测试图片不存在，请创建 test.jpg")
        return

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        data = response.json()
        if data['code'] == 0:
            print("✅ 识别成功")
            print(f"  类别: {data['data']['category']}")
            print(f"  置信度: {data['data']['confidence']}")
            print(f"  下载链接: {data['data']['download_url']}")

            img_data = data['data']['annotated_image'].split(',')[1]
            with open('output.jpg', 'wb') as f:
                f.write(base64.b64decode(img_data))
            print("  标注图已保存: output.jpg")
        else:
            print(f"❌ 识别失败: {data['message']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")


def test_health():
    """测试健康检查"""
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    print(f"健康检查: {response.json()}")


if __name__ == "__main__":
    test_health()
    test_upload()