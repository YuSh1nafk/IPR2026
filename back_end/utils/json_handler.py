import json
import os

def save_to_json(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"💾 Đã lưu dữ liệu JSON tại: {filename}")

def load_from_json(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ Không tìm thấy file: {filename}")
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)