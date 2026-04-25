import pathlib
from crewai.tools import tool


@tool("Save HTML to File")
def save_html_tool(html_content: str, filename: str) -> str:
    """
    Lưu chuỗi mã HTML vào một file cụ thể trên máy tính.
    Args:
        html_content (str): Mã HTML hoàn chỉnh của giáo án (đã bao gồm ảnh Base64).
        filename (str): Đường dẫn đầy đủ để lưu file (ví dụ: './outputs/lesson_plan.html').
    Returns:
        str: Thông báo lưu thành công.
    """
    try:
        # Noi luu file
        filepath = pathlib.Path('./lesson_plan_1.html')
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ghi file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return f"THÀNH CÔNG! Đã lưu file HTML vào đường dẫn: {'./lesson_plan.html'}. Người dùng có thể mở file này lên để xem giáo án."
    except Exception as e:
        return f"LỖI khi lưu HTML: {e}"