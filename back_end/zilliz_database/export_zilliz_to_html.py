import os
from pymilvus import connections, Collection
from dotenv import load_dotenv
from pymilvus.orm import utility

load_dotenv()

# ================== Cấu hình ==================
# COL_NAME = "Global_Success_Book_4"  # Đảm bảo đúng tên collection
MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")


def export_milvus_to_html(col_name:str ,output_filename="database_dump_test_1.html"):
    print("1. Đang kết nối tới Zilliz...")
    connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)

    if not utility.has_collection(col_name):
        print(f"Lỗi: Collection '{col_name}' không tồn tại trên Zilliz.")
        connections.disconnect("default")
        return None

    col = Collection(col_name)
    col.load()

    print(f"2. Đang truy vấn toàn bộ dữ liệu từ collection '{col_name}'...")
    # Lấy tối đa 10.000 dòng (nếu sách dài hơn, bạn có thể tăng limit)
    # Dùng expr="seq_id >= 0" để lấy tất cả các record có seq_id
    results = col.query(
        expr="seq_id >= 0",
        output_fields=["seq_id", "data_type", "content"],
        limit=10000
    )

    if not results:
        print("Bảng của bạn hiện đang trống không có dữ liệu nào!")
        return

    print(f"3. Tìm thấy {len(results)} bản ghi. Đang sắp xếp theo thứ tự (seq_id)...")
    sorted_results = sorted(results, key=lambda x: x["seq_id"])

    print("4. Đang tạo file HTML...")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zilliz Database Dump</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
            .container { max-width: 800px; margin: auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .item { border-bottom: 1px solid #ddd; padding: 15px 0; }
            .seq-id { font-weight: bold; color: #d9534f; margin-bottom: 10px; display: block; }
            .text-content { font-size: 16px; line-height: 1.6; white-space: pre-wrap; }
            .image-content { max-width: 100%; height: auto; border: 1px solid #ccc; padding: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Dữ liệu thực tế đang lưu trong Zilliz</h2>
            <hr>
    """

    for item in sorted_results:
        seq_id = item["seq_id"]
        data_type = item["data_type"]
        content = item["content"]

        html_content += f'<div class="item">\n'
        html_content += f'  <span class="seq-id">[ID: {seq_id}] - {data_type.upper()}</span>\n'

        if data_type == "text":
            # Nếu là text, in thẳng chữ ra
            html_content += f'  <div class="text-content">{content}</div>\n'
        elif data_type == "image":
            # Nếu là ảnh, ghép chuỗi Base64 vào thẻ img của HTML
            html_content += f'  <img class="image-content" src="data:image/jpeg;base64,{content}" alt="Image seq {seq_id}">\n'

        html_content += f'</div>\n'

    html_content += """
        </div>
    </body>
    </html>
    """

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    connections.disconnect("default")
    print(f"HOÀN TẤT! Đã trả về dữ liệu HTML.")
    return html_content


if __name__ == "__main__":
    export_milvus_to_html("Global_Success_Book_4")