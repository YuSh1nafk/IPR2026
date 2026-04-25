import os, re, base64
from io import BytesIO
from typing import List, Dict
from fitz import Document
from PIL import Image  # Thư viện xử lý ảnh
from openai import OpenAI
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from dotenv import load_dotenv

load_dotenv()

# ================== Cấu hình ==================
PDF_PATH = "D:\\codecacthu\\IPR\\Book\\Global_Success_Book_1.pdf"
COL_NAME = "Global_Success_Book"

EMBED_MODEL = "text-embedding-3-large"
VISION_MODEL = "gpt-4o"
EMBED_DIM = 3072

MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)


def extract_and_chunk_sequentially(path: str) -> List[Dict]:
    """Đọc PDF, lọc ảnh nền/icon rác và giữ nguyên khối text cấu trúc."""
    items = []
    seq_id = 0

    with Document(path) as doc:
        for page in doc:
            # Tính tổng diện tích của cả trang
            page_area = page.rect.width * page.rect.height

            raw_blocks = page.get_text("dict")["blocks"]

            # Sắp xếp các khối từ trên xuống dưới một cách tương đối
            sorted_blocks = sorted(raw_blocks, key=lambda b: b["bbox"][1])

            for b in sorted_blocks:
                if b["type"] == 0:  # Khối Text
                    # Lấy text, giữ lại các dấu cách hợp lý, không ép dính vào nhau
                    block_text = "".join([span["text"] + " " for line in b["lines"] for span in line["spans"]]).strip()

                    if block_text and len(block_text) > 5:  # Bỏ qua các block chỉ có 1-2 ký tự rác
                        items.append({"seq_id": seq_id, "type": "text", "content": block_text, "bytes": None})
                        seq_id += 1

                elif b["type"] == 1:  # Khối Ảnh
                    # Tính diện tích bức ảnh
                    img_width = b["bbox"][2] - b["bbox"][0]
                    img_height = b["bbox"][3] - b["bbox"][1]
                    img_area = img_width * img_height

                    # LỌC ẢNH RÁC:
                    # Nếu ảnh chiếm quá 60% trang -> Đích thị là ảnh nền (Background), BỎ QUA!
                    # Nếu ảnh chiếm ít hơn 1.5% trang -> Thường là icon/chấm bi trang trí, BỎ QUA!
                    if img_area > page_area * 0.6 or img_area < page_area * 0.015:
                        continue

                    try:
                        img = Image.open(BytesIO(b["image"]))
                        img.thumbnail((600, 600))  # Tăng size lên một chút cho GPT-4o nhìn cho rõ nét
                        buffer = BytesIO()
                        img.convert('RGB').save(buffer, format="JPEG", quality=85)
                        compressed_bytes = buffer.getvalue()
                        b64_str = base64.b64encode(compressed_bytes).decode("utf-8")

                        # Chỉ lưu nếu dung lượng Base64 an toàn cho Zilliz
                        if len(b64_str) < 65000:
                            items.append(
                                {"seq_id": seq_id, "type": "image", "content": b64_str, "bytes": compressed_bytes})
                            seq_id += 1
                    except Exception as e:
                        print(f"Bỏ qua ảnh lỗi: {e}")
                        pass

    return items

def openai_embed_text(text: str) -> List[float]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def openai_caption_image(img_b64: str) -> str:
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail. CRITICAL: If there are any text, tables, grammar rules, or exercises in the image, you MUST transcribe them word-for-word. This text will be used for semantic search."
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }],
    )
    return resp.choices[0].message.content


def setup_milvus() -> Collection:
    connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)

    if utility.has_collection(COL_NAME):
        utility.drop_collection(COL_NAME)
        print(f"Đã xóa bảng cũ '{COL_NAME}'.")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="seq_id", dtype=DataType.INT64),  # <-- Thêm dòng này
        FieldSchema(name="data_type", dtype=DataType.VARCHAR, max_length=10),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBED_DIM),
    ]
    col = Collection(name=COL_NAME, schema=CollectionSchema(fields))
    col.create_index(field_name="vector",
                     index_params={"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}})
    return col


# ================== Kịch bản chạy chính ==================
def main():
    import time

    print("1. Đọc và xếp hàng dữ liệu từ PDF...")
    items = extract_and_chunk_sequentially(PDF_PATH)
    print(f"   -> Đã xếp được {len(items)} khối (gồm cả Text và Ảnh) theo đúng thứ tự.")

    if not items:
        return

    print("2. Khởi tạo Milvus...")
    col = setup_milvus()

    print("3. Bắt đầu Embedding và lưu vào Zilliz...")

    seq_ids = []
    data_types = []
    contents = []
    vectors = []

    for item in items:
        try:
            if item["type"] == "text":
                # Nhúng Text
                vector = openai_embed_text(item["content"])
                content_to_store = item["content"]

            elif item["type"] == "image":
                caption = openai_caption_image(item["content"])
                print(f"   (Caption ảnh seq_id={item['seq_id']}: {caption[:80]}...)")

                vector = openai_embed_text(caption)

                content_to_store = item["content"]


            else:
                continue

            seq_ids.append(item["seq_id"])
            data_types.append(item["type"])
            contents.append(content_to_store)
            vectors.append(vector)

        except Exception as e:
            print(f"Lỗi khi embed item số {item['seq_id']}: {e}")

    print(f"4. Chèn {len(vectors)} bản ghi vào Database...")
    if vectors:
        batch_size = 100  # Cứ 100 dòng thì đẩy lên Zilliz 1 lần
        for i in range(0, len(vectors), batch_size):
            end = i + batch_size
            col.insert([
                seq_ids[i:end],
                data_types[i:end],
                contents[i:end],
                vectors[i:end]
            ])
            print(f"   -> Đã insert lô {i} đến {min(end, len(vectors))}")
        col.flush()
    print("HOÀN TẤT! Dữ liệu đã được xếp hàng ngay ngắn trong Database.")


if __name__ == "__main__":
    main()