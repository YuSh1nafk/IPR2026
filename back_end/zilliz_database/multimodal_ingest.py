import os, base64, time, json, re
from io import BytesIO
from typing import List, Dict, Tuple
from fitz import Document, Matrix
from PIL import Image
from google import genai
from google.genai import types
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from dotenv import load_dotenv

load_dotenv()

# ================== Cấu hình ==================
DOCX_PATH = "D:\\codecacthu\\IPR\\Book\\Global_Success_Book_1.pdf"
COL_NAME = "Global_Success_Book"
EMBED_MODEL = "gemini-embedding-2-preview"  # Model toán học (để tạo vector)
EMBED_DIM = 3072

MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")

# Sử dụng model Vision mới mạnh nhất của Google để nhìn và sắp xếp bố cục
LAYOUT_MODEL = "gemini-3.1-flash-lite-preview"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ================== Tiền xử lý (Text + Image) ==================

def render_page_to_image(page) -> bytes:
    """Render toàn trang PDF thành ảnh để AI nhìn bố cục (trong RAM)."""
    # Render với độ phân giải cao để AI nhìn rõ
    mat = Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("jpeg")
    return img_bytes


def compress_image(img_bytes: bytes, max_size=(600, 600)) -> tuple[bytes, str]:
    """Nén ảnh nhỏ lại để nhét vừa VARCHAR (max 65535 ký tự base64)."""
    try:
        img = Image.open(BytesIO(img_bytes))
        img.thumbnail(max_size)  # Thu nhỏ
        buffer = BytesIO()
        img.convert('RGB').save(buffer, format="JPEG", quality=75)
        compressed_bytes = buffer.getvalue()
        b64_str = base64.b64encode(compressed_bytes).decode("utf-8")

        if len(b64_str) < 65000:
            return compressed_bytes, b64_str
        else:
            return None, None
    except Exception as e:
        print(f"Bỏ qua 1 ảnh lỗi khi nén: {e}")
        return None, None


# ================== 1. TÌM TỌA ĐỘ ẢNH (BBOX) VÀ BỐ CỤC ==================
def analyze_page_layout(page_image_bytes: bytes) -> List[Dict]:
    """
    Agent 'nhìn' tấm ảnh to toàn trang và trả về JSON thứ tự và TOẠ ĐỘ ẢNH (BBOX).
    Đã được tinh chỉnh để gom nhóm theo bài tập và cắt bảng/hộp màu thành ảnh.
    """
    print("   [Agent 'Mắt AI' đang phân tích bố cục trang...]")

    prompt = (
        "Bạn là một chuyên gia phân tích bố cục sách giáo khoa Tiếng Anh. "
        "Hãy phân tích trang sách này và trả về kết quả theo một mảng JSON. "
        "BẠN PHẢI TUÂN THỦ NGHIÊM NGẶT 2 QUY TẮC SAU:\n\n"

        "QUY TẮC 1 - TRÌNH TỰ ĐỌC:\n"
        "Đọc nội dung theo đúng luồng logic của bài học. Hãy quét dứt điểm toàn bộ nội dung của bài tập 1, sau đó mới chuyển sang bài 2, rồi bài 3... Tuyệt đối không nhảy cóc giữa các cột nếu bài tập ở cột đó chưa kết thúc.\n\n"

        "QUY TẮC 2 - PHÂN LOẠI TEXT VÀ IMAGE:\n"
        "- Nếu nội dung là văn bản bình thường (tiêu đề, câu hỏi, đoạn văn nằm trên NỀN TRẮNG): trích xuất dưới dạng text.\n"
        "- Nếu nội dung là một BẢNG (Table), một HỘP LÝ THUYẾT (ví dụ: hộp 'Remember!' nền vàng), bất kỳ khối chữ nào nằm trên NỀN CÓ MÀU (xanh, vàng, v.v.), hoặc một bài tập có hình ảnh và chữ sắp xếp phức tạp (như Bài 3): KHÔNG trích xuất text. Hãy gộp toàn bộ khối đó lại và ĐÁNH DẤU NÓ LÀ MỘT BỨC ẢNH.\n\n"

        "Mỗi object trong mảng JSON trả về MUST có dạng:\n"
        "- Với văn bản thường: {\"type\": \"text\", \"content\": \"(nội dung văn bản)...\"}\n"
        "- Với ảnh, bảng biểu, hộp màu: {\"type\": \"image\", \"bbox\": [ymin, xmin, ymax, xmax]} "
        "(Tọa độ bbox được chuẩn hóa về dải [0, 1000] so với kích thước thật của ảnh trang sách).\n\n"

        "Lưu ý: Trả về ĐÚNG định dạng JSON mảng, không thêm chú thích hay ký tự markdown dư thừa nào khác."
    )

    # Gửi ảnh to lên model Gemini Vision
    image_part = types.Part.from_bytes(data=page_image_bytes, mime_type="image/jpeg")
    response = client.models.generate_content(
        model=LAYOUT_MODEL,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(response_mime_type="application/json")  # Ép trả JSON
    )

    try:
        # Parse chuỗi JSON
        structured_layout = json.loads(response.text)
        return structured_layout
    except json.JSONDecodeError as e:
        print(f"Bỏ qua trang này do lỗi parse JSON bố cục: {e}")
        return []


# ================== 2. Python CẮT ẢNH ==================
def python_crop_image(full_image_bytes: bytes, bbox: List[int]) -> bytes:
    """
    Lấy tọa độ Bbox [ymin, xmin, ymax, xmax] (dải 1000) và 'cắt' ảnh (crop)
    từ tấm ảnh to (trong RAM) using Pillow.
    """
    # --- CHỐT CHẶN AN TOÀN NÂNG CAO ---
    if not isinstance(bbox, list):
        return None

    # 1. Gỡ lớp mảng thừa nếu AI lỡ bọc thêm (vd: [[ymin, xmin, ymax, xmax]])
    if len(bbox) == 1 and isinstance(bbox[0], list):
        bbox = bbox[0]

    # 2. Kiểm tra độ dài có đúng 4 điểm tọa độ không
    if len(bbox) != 4:
        print(f"   -> [Cảnh báo] AI trả về tọa độ bbox sai độ dài: {bbox}. Bỏ qua.")
        return None

    # 3. Ép kiểu toàn bộ về số thực (float) để tránh lỗi mảng/chữ bị lọt vào
    try:
        ymin, xmin, ymax, xmax = [float(x) for x in bbox]
    except (ValueError, TypeError):
        print(f"   -> [Cảnh báo] Tọa độ chứa dữ liệu rác (không phải số): {bbox}. Bỏ qua.")
        return None
    # -----------------------------------

    # 1. Mở tấm ảnh to từ bytes
    full_img = Image.open(BytesIO(full_image_bytes))
    full_w, full_h = full_img.size

    # 2. Giải nén tọa độ: nhân tọa độ dải 1000 với kích thước thực
    left = int(xmin * full_w / 1000)
    top = int(ymin * full_h / 1000)
    right = int(xmax * full_w / 1000)
    bottom = int(ymax * full_h / 1000)

    # Chặn tọa độ vượt quá giới hạn ảnh
    left, top = max(0, left), max(0, top)
    right, bottom = min(full_w, right), min(full_h, bottom)

    if left >= right or top >= bottom:
        print("   -> [Cảnh báo] Tọa độ ảnh sau khi tính toán bị lỗi (chiều rộng/cao <= 0). Bỏ qua.")
        return None

    # 3. Cắt (Crop) tấm ảnh nhỏ
    small_img = full_img.crop((left, top, right, bottom))

    # 4. Trả về bytes của tấm ảnh nhỏ
    buffer = BytesIO()
    small_img.convert('RGB').save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


# ================== Tương tác AI & Database ==================
def gemini_embed_text(texts: List[str]) -> List[List[float]]:
    out = []
    # Rút gọn batch xuống 20 để tránh lỗi Quota
    for i in range(0, len(texts), 20):
        batch = texts[i:i + 20]
        response = client.models.embed_content(model=EMBED_MODEL, contents=batch)
        out.extend([emb.values for emb in response.embeddings])
    return out


def gemini_embed_image(image_bytes: bytes) -> List[float]:
    """
    <-- THAY ĐỔI: Dùng model Geminí Embedding (Gemini toán học) để nhúng ảnh,
    không dùng model Chat nhúng ảnh.
    """
    part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=part
    )
    return response.embeddings[0].values


def setup_milvus() -> Collection:
    connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)

    if utility.has_collection(COL_NAME):
        utility.drop_collection(COL_NAME)  # Luôn xóa collection cũ để test cho sạch
        print(f"Đã xóa collection cũ '{COL_NAME}'.")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="seq_id", dtype=DataType.INT64),  # Thứ tự từ trên xuống dưới
        FieldSchema(name="data_type", dtype=DataType.VARCHAR, max_length=10),  # "text" hoặc "image"
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),  # Chữ hoặc Base64 ảnh
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBED_DIM),
    ]
    col = Collection(name=COL_NAME, schema=CollectionSchema(fields))
    col.create_index(field_name="vector",
                     index_params={"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}})
    return col


# ================== Luồng chạy chính ==================
def main():
    import time

    print("1. Đọc PDF và trích xuất dữ liệu...")
    if not os.path.exists(DOCX_PATH):
        print("Lỗi: Không tìm thấy file PDF.")
        return

    print("2. Khởi tạo Milvus...")
    col = setup_milvus()

    seq_id = 0  # Đánh số thứ tự toàn project

    with Document(DOCX_PATH) as doc:
        for page_num, page in enumerate(doc):
            print(f"\n--- Bắt đầu TRANG {page_num + 1} ---")

            # Khâu 1: Render toàn trang thành 1 ảnh to (để AI nhìn bố cục)
            # Giữ lại tấm ảnh to này trong RAM
            full_page_image_bytes = render_page_to_image(page)

            # Khâu 2: Agent 'nhìn' tấm ảnh to và phân tích bố cục, trả về JSON kèm tọa độ (Bbox)
            structured_layout = analyze_page_layout(full_page_image_bytes)

            print(f"   -> Đã xếp được {len(structured_layout)} gạch đầu dòng theo logic bài học.")

            for item in structured_layout:
                data_item = None

                # Nếu là "Văn bản"
                if item["type"] == "text" and item["content"].strip():
                    text = item["content"].strip()
                    try:
                        vector = gemini_embed_text([text])[0]  # Nhúng text
                        data_item = {"seq_id": seq_id, "data_type": "text", "content": text, "vector": vector}
                    except Exception as e:
                        print(f"Bỏ qua 1 đoạn text ở seq {seq_id} do lỗi API Quota: {e}")

                # Nếu là "Hình ảnh nhỏ"
                elif item["type"] == "image":
                    # Khâu 3:Python lấy Tọa độ Bbox và 'cắt' (crop) tấm ảnh nhỏ từ tấm ảnh to
                    small_image_bytes = python_crop_image(full_page_image_bytes, item["bbox"])

                    if small_image_bytes:
                        # Nén tấm ảnh nhỏ
                        compressed_bytes, b64_str = compress_image(small_image_bytes)

                        if compressed_bytes and b64_str:
                            try:
                                # Khâu 4: Dùng Gemini Embedding (model toán học) để nhúng ảnh
                                vector = gemini_embed_image(compressed_bytes)
                                data_item = {"seq_id": seq_id, "data_type": "image", "content": b64_str,
                                             "vector": vector}

                                # Nghỉ 15 giây sau mỗi lần nhúng để tránh lỗi API Limit 429
                                print(f"   (Đã nhúng xong 1 ảnh nhỏ seq {seq_id}, nghỉ 15s để né API limit...)")
                                time.sleep(1)
                            except Exception as e:
                                print(f"Bỏ qua 1 ảnh ở seq {seq_id} do lỗi API Quota: {e}")

                # Chèn dữ liệu (Insert) THEO ĐÚNG THỨ TỰ vào Database
                if data_item:
                    col.insert([[data_item["seq_id"]], [data_item["data_type"]], [data_item["content"]],
                                [data_item["vector"]]])
                    seq_id += 1  # Tăng số thứ tự project

            # Kết thúc một trang, flush và nghỉ
            col.flush()
            print(f"--- Hoàn tất chèn dữ liệu TRANG {page_num + 1} ---")

            # Nên nghỉ khoảng 30s sau khi nhúng xong 1 trang để tài khoản Free Tier (5 requests/phút) không bị khoá
            time.sleep(10)

    print("\nHOÀN TẤT DỰ ÁN INGEST! Dữ liệu của bạn giờ đã có cả TEXT và ẢNH nhỏ chuẩn xác.")


if __name__ == "__main__":
    # Đừng quên Drop collection cũ trên web Zilliz trước khi chạy nhé!
    main()