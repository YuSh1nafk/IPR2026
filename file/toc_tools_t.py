import os
from typing import List, Dict
from pymilvus import connections, Collection
from google import genai
from dotenv import load_dotenv
from crewai.tools import tool
import unicodedata

# ====== Cấu hình ======
load_dotenv()
COL_NAME_SGK = "Global_Success_Book_4"
EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072

MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)


def connect_milvus():
    connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)
    try:
        connections.get_connection_addr("default")
    except Exception as e:
        raise RuntimeError(f"Lỗi kết nối Milvus: {e}")


def get_content_skg(query: str) -> str:
    """Hàm lõi: Tìm kiếm nội dung và ảnh minh họa trong Zilliz"""
    print(f"[Debug] Đang truy vấn Zilliz Collection: {COL_NAME_SGK}")
    connect_milvus()
    col = Collection(COL_NAME_SGK)
    col.load()

    print(f"\nTÌM KIẾM TỪ KHÓA: {query!r}")

    # 1. Embed câu hỏi bằng Gemini Toán Học
    qvec = client.models.embed_content(model=EMBED_MODEL, contents=query).embeddings[0].values

    # 2. Tìm kiếm ngữ nghĩa trong Zilliz
    hits = col.search(
        data=[qvec],
        anns_field="vector",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=6,  # Lấy 6 khối dữ liệu liên quan nhất
        output_fields=["seq_id", "data_type", "content"]
    )

    if not hits or not hits[0]:
        return "Không tìm thấy nội dung nào liên quan trong sách."

    context_results = []
    processed_seq_ids = set()  # Dùng để tránh bị lặp lại data

    # 3. Duyệt kết quả và gắp thêm ảnh liền kề (nếu có)
    for hit in hits[0]:
        seq_id = hit.entity.get("seq_id")
        data_type = hit.entity.get("data_type")
        content = hit.entity.get("content")

        if seq_id in processed_seq_ids:
            continue

        if data_type == "text":
            context_results.append(f"[VĂN BẢN BÀI HỌC]:\n{content}")
            processed_seq_ids.add(seq_id)

            # Logic Thông Minh: Thấy Text thì dò xem ID ngay sau nó có phải là Ảnh/Bảng không
            try:
                adjacent_hits = col.query(
                    expr=f"seq_id == {seq_id + 1}",
                    output_fields=["data_type", "content"]
                )
                if adjacent_hits and adjacent_hits[0]["data_type"] == "image":
                    adj_seq = seq_id + 1
                    b64_content = adjacent_hits[0]["content"]
                    context_results.append(
                        f"[BẢNG BIỂU / HÌNH ẢNH MINH HỌA ĐI KÈM]: <br><img src='data:image/jpeg;base64,{b64_content}' style='max-width:100%; border: 1px solid #ccc; margin: 10px 0;' />")
                    processed_seq_ids.add(adj_seq)
            except Exception as e:
                pass

        elif data_type == "image":
            context_results.append(
                f"[BẢNG BIỂU / HÌNH ẢNH MINH HỌA]: <br><img src='data:image/jpeg;base64,{content}' style='max-width:100%; border: 1px solid #ccc; margin: 10px 0;' />")
            processed_seq_ids.add(seq_id)

    context_str = "\n\n".join(context_results)
    print(f"-> Đã lấy được {len(context_results)} khối dữ liệu gửi cho Agent.")
    return context_str


@tool("Milvus Content Search")
def milvus_content_search_t(query: str, subject: str) -> str:
    """
    Tìm kiếm nội dung bài học chi tiết (chữ và hình ảnh/bảng biểu) trong Database Sách Giáo Khoa.
    Đầu vào: query (chủ đề cần tìm, vd: 'Unit 1 Getting Started') và subject (môn học).
    """
    print("-------------------------------------------")
    print(f"[Tool Kích Hoạt] Môn: {subject} | Tìm kiếm: {query}")
    return get_content_skg(query)