import os
import base64
from typing import List, Dict
import fitz  # Thư viện PyMuPDF

# Import hàm tạo HTML từ file helper
from utils_supporter import generate_debug_html


def is_inside(rect1: fitz.Rect, rect2: fitz.Rect) -> bool:
    """Kiểm tra xem rect1 có nằm phần lớn bên trong rect2 hay không (để chống lặp chữ)"""
    intersection = rect1.intersect(rect2)
    if intersection.is_empty:
        return False
    # Nếu phần giao nhau chiếm > 60% diện tích của chữ thì coi như nằm trong hộp
    return (intersection.get_area() / rect1.get_area()) > 0.6


def process_pdf(pdf_path: str, start_page: int, end_page: int) -> List[Dict]:
    """
    Trạm 1: Đọc PDF bằng thuật toán Smart Native.
    - Lọc bỏ ảnh nền toàn trang.
    - Tự động phát hiện và chụp các hộp màu (Remember box, Table).
    """
    print(f"🚀 BẮT ĐẦU XỬ LÝ PDF (SMART NATIVE): {pdf_path} (Trang {start_page} đến {end_page})")

    context_data = []

    if not os.path.exists(pdf_path):
        print("❌ Lỗi: Không tìm thấy file PDF!")
        return context_data

    with fitz.open(pdf_path) as doc:
        for page_num in range(start_page - 1, end_page):
            print(f"\n--- Đang quét Trang số {page_num + 1} ---")
            page = doc[page_num]
            page_w, page_h = page.rect.width, page.rect.height

            elements = []  # Lưu các phần tử để cuối cùng sắp xếp từ trên xuống dưới (theo y0)

            # ==========================================
            # BƯỚC 1: QUÉT TÌM CÁC HỘP/BẢNG CÓ MÀU NỀN
            # ==========================================
            raw_boxes = []
            for p in page.get_drawings():
                fill_color = p.get("fill")
                # Nếu có màu nền và không phải màu trắng tinh
                if fill_color is not None and fill_color != (1.0, 1.0, 1.0) and fill_color != [1.0, 1.0, 1.0]:
                    rect = p["rect"]
                    # Lọc các hộp rác quá nhỏ hoặc nền toàn trang
                    if 40 < rect.width < page_w * 0.95 and 20 < rect.height < page_h * 0.95:
                        raw_boxes.append(rect)

            # Gộp các hộp màu bị đè lên nhau (do người thiết kế vẽ nhiều hình ghép lại)
            colored_boxes = []
            for box in raw_boxes:
                has_merged = False
                for i, m_box in enumerate(colored_boxes):
                    if box.intersects(m_box):
                        colored_boxes[i] = m_box.include_rect(box)
                        has_merged = True
                        break
                if not has_merged:
                    colored_boxes.append(box)

            # Chụp ảnh (Snapshot) các hộp màu vừa tìm được
            mat = fitz.Matrix(2, 2)  # Zoom x2 cho nét căng
            for box in colored_boxes:
                # Mở rộng vùng cắt ra 3 pixel để không bị lẹm viền
                expanded_box = box + (-3, -3, 3, 3)
                pix = page.get_pixmap(matrix=mat, clip=expanded_box, alpha=False)
                b64_str = base64.b64encode(pix.tobytes("jpeg")).decode("utf-8")
                elements.append({"y0": box.y0, "type": "image", "content": b64_str})
                print("   -> Đã bắt sống 1 Bảng/Hộp màu (Remember box).")

            # ==========================================
            # BƯỚC 2: QUÉT TEXT VÀ ẢNH GỐC
            # ==========================================
            dict_data = page.get_text("dict")
            for b in dict_data.get("blocks", []):
                bbox = fitz.Rect(b["bbox"])

                # Nếu block này nằm lọt thỏm trong hộp màu ở BƯỚC 1 -> Bỏ qua (để không bị lặp)
                if any(is_inside(bbox, cb) for cb in colored_boxes):
                    continue

                # Nếu là Văn bản
                if b["type"] == 0:
                    text_content = "".join([span.get("text", "") + " " for line in b.get("lines", []) for span in
                                            line.get("spans", [])]).strip()
                    if len(text_content) > 1:
                        elements.append({"y0": bbox.y0, "type": "text", "content": text_content})

                # Nếu là Hình ảnh nhúng
                elif b["type"] == 1:
                    # LỌC BỎ ẢNH NỀN: Nếu ảnh to hơn 80% trang sách -> Quăng đi!
                    if bbox.width > page_w * 0.8 and bbox.height > page_h * 0.8:
                        continue
                    # LỌC BỎ ICON NHỎ:
                    if bbox.width < 20 or bbox.height < 20:
                        continue

                    img_bytes = b.get("image")
                    if img_bytes:
                        b64_str = base64.b64encode(img_bytes).decode("utf-8")
                        elements.append({"y0": bbox.y0, "type": "image", "content": b64_str})
                        print("   -> Đã trích xuất 1 Hình ảnh minh họa.")

            # ==========================================
            # BƯỚC 3: SẮP XẾP THEO TRÌNH TỰ
            # ==========================================
            # Sắp xếp các phần tử từ trên xuống dưới theo trục Y
            elements.sort(key=lambda x: x["y0"])
            for el in elements:
                context_data.append({"type": el["type"], "content": el["content"]})

    print("\n🎉 HOÀN TẤT! DỮ LIỆU ĐÃ SẠCH SẼ 100%.")

    # Xuất ra file HTML cho bạn test
    generate_debug_html(context_data)
    return context_data


# ==========================================
# KHU VỰC TEST
# ==========================================
if __name__ == "__main__":
    # Đổi đường dẫn PDF của bạn vào đây nhé
    SAMPLE_PDF = "D:\\codecacthu\\IPR\\Book\\Global_Success_Book_1.pdf"

    if os.path.exists(SAMPLE_PDF):
        process_pdf(SAMPLE_PDF, start_page=1, end_page=10)
    else:
        print("Lỗi: Không tìm thấy file PDF.")