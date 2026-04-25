import os
import pathlib


def generate_debug_html(context_data: list, output_filename="outputs/debug_context.html"):
    """
    Hàm này nhận danh sách dữ liệu (text và ảnh base64) và xuất ra file HTML để kiểm tra.
    """
    print(f"-> Đang tạo file Debug HTML tại: {output_filename} ...")

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Debug Context - Sách Giáo Khoa</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
            .container { max-width: 800px; margin: auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .item { border-bottom: 2px dashed #ddd; padding: 15px 0; }
            .tag { font-weight: bold; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
            .tag-text { background-color: #d1ecf1; color: #0c5460; }
            .tag-image { background-color: #d4edda; color: #155724; }
            .text-content { font-size: 16px; line-height: 1.6; white-space: pre-wrap; }
            .image-content { max-width: 100%; height: auto; border: 1px solid #ccc; padding: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Dữ liệu Thô trích xuất từ PDF (Debug Mode)</h2>
            <hr>
    """

    for i, item in enumerate(context_data):
        html_content += f'<div class="item">\n'

        if item["type"] == "text":
            html_content += f'  <span class="tag tag-text">[SEQ: {i}] - VĂN BẢN</span>\n'
            html_content += f'  <div class="text-content">{item["content"]}</div>\n'
        elif item["type"] == "image":
            html_content += f'  <span class="tag tag-image">[SEQ: {i}] - HÌNH ẢNH / BẢNG BIỂU</span><br>\n'
            html_content += f'  <img class="image-content" src="data:image/jpeg;base64,{item["content"]}" alt="Ảnh cắt từ PDF">\n'

        html_content += f'</div>\n'

    html_content += """
        </div>
    </body>
    </html>
    """

    # Tạo thư mục outputs nếu chưa có
    filepath = pathlib.Path(output_filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Đã lưu file kiểm tra thành công! Hãy mở file {output_filename} để xem.")