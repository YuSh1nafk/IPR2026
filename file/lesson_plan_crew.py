import os
import pathlib
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from pymilvus import connections, Collection
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. KHỞI TẠO CÁC CÔNG CỤ (TOOLS)
# ==========================================

@tool("Fetch All Textbook Content")
def fetch_all_content_tool() -> str:
    """
    Công cụ này kết nối vào database (Milvus) và lấy TOÀN BỘ nội dung sách giáo khoa
    (bao gồm cả Text và chuỗi Base64 của Hình ảnh), được sắp xếp chuẩn xác theo số thứ tự (seq_id).
    """
    try:
        COL_NAME = "Global_Success_Book_4" # Tên collection bạn đang dùng
        MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
        MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")

        connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)
        col = Collection(COL_NAME)
        col.load()

        # Lấy tối đa 2000 block dữ liệu theo thứ tự
        results = col.query(
            expr="seq_id >= 0",
            output_fields=["seq_id", "data_type", "content"],
            limit=2000
        )

        if not results:
            return "Database trống."

        # Sắp xếp theo đúng luồng logic của sách
        sorted_results = sorted(results, key=lambda x: x["seq_id"])

        context_results = []
        for item in sorted_results:
            seq_id = item["seq_id"]
            data_type = item["data_type"]
            content = item["content"]

            if data_type == "text":
                context_results.append(f"[SEQ_ID: {seq_id}] [VĂN BẢN]:\n{content}")
            elif data_type == "image":
                context_results.append(f"[SEQ_ID: {seq_id}] [HÌNH ẢNH MINH HỌA]: <img src='data:image/jpeg;base64,{content}' style='max-width:100%; border:1px solid #ccc; margin:10px 0;' />")

        return "\n\n".join(context_results)
    except Exception as e:
        return f"Lỗi khi truy xuất Database: {e}"

@tool("Save HTML to File")
def save_html_tool(html_content: str, filename: str) -> str:
    """Lưu chuỗi HTML thành file trên máy tính."""
    try:
        filepath = pathlib.Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return f"Đã lưu thành công file HTML vào: {filename}"
    except Exception as e:
        return f"Lỗi lưu file: {e}"

# ==========================================
# 2. CẤU HÌNH LLM (GEMINI 1.5 FLASH)
# ==========================================
# Cú pháp chuẩn của CrewAI mới để nhận diện đúng Google API
llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=os.getenv("GEMINI_API_KEY")
)

# ==========================================
# 3. KHỞI TẠO 3 AGENTS CHUYÊN BIỆT
# ==========================================

context_extractor = Agent(
    role="Chuyên gia Trích xuất Dữ liệu SGK",
    goal="Lấy toàn bộ dữ liệu từ Database và trích xuất chính xác, KHÔNG ĐƯỢC SÓT một chữ hay một hình ảnh nào của bài học được yêu cầu.",
    backstory="Bạn là một chuyên gia phân tích dữ liệu SGK. Bạn biết cách tìm điểm bắt đầu của một Lesson và điểm kết thúc của nó từ một lượng lớn văn bản thô.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[fetch_all_content_tool]
)

lesson_plan_designer = Agent(
    role="Chuyên gia Soạn Giáo án Tiếng Anh",
    goal="Soạn giáo án chuẩn sư phạm dựa trên dữ liệu thô, tuân thủ 100% cấu trúc biểu mẫu (Master Template).",
    backstory="Bạn là giáo viên Tiếng Anh xuất sắc. Bạn biết cách chia các bài tập thành các Task trong mục PRACTICE, và luôn giữ nguyên các thẻ <img src=...> để minh họa vào đúng cột Content.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

html_developer = Agent(
    role="Kỹ sư Lập trình Web HTML/CSS",
    goal="Chuyển đổi giáo án Markdown thành file HTML có giao diện bảng (table) đẹp mắt, chuyên nghiệp.",
    backstory="Bạn là chuyên gia UI/UX. Bạn luôn bọc phần 'Organization of implementation' vào các thẻ <table> với 2 cột 'Teacher’s and Ss’ activities' và 'Content'.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[save_html_tool]
)

# ==========================================
# 4. MASTER TEMPLATE & TASKS
# ==========================================

MASTER_TEMPLATE = """
I. OBJECTIVES:
1. Knowledge: (Tự điền dựa vào nội dung bài)
2. Core competence: Develop communication skills, creativity, be collaborative in pair/team work, actively join in class activities.
3. Personal qualities: Develop self-study skills.

II. MATERIALS:
- Grade 8 textbook
- Computer connected to the internet
- Projector/ TV/ pictures

III. PROCEDURES:
1. WARM-UP (5 mins)
* Aim: To activate students' prior knowledge and engage their interest.
* Content: (Tự đề xuất 1 trò chơi hoặc câu hỏi gợi mở liên quan đến bài)
* Products: Students' answers or participation.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content]

2. PRESENTATION (5 mins)
* Aim: To help students understand the new concept/vocabulary/grammar.
* Content: (Giải thích lý thuyết mới của bài học)
* Products: Students note down the lesson content.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content]

3. PRACTICE (8 mins)
(LƯU Ý: VỚI MỖI BÀI TẬP TÌM THẤY TRONG SGK, TẠO MỘT TASK RIÊNG)
Task 1: (Tên bài tập 1)
* Aims: To check students’ understanding.
* Content: (Yêu cầu bài tập)
* Products: Students' answers.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content (BẮT BUỘC chèn toàn bộ câu hỏi, đáp án gợi ý và các thẻ <img src=...> minh họa của bài tập này vào cột Content)]

Task 2: (Tên bài tập 2)...
(Tiếp tục lặp lại form Task trên cho đến hết các bài tập)

4. PRODUCTION (10 mins)
* Aim: To help students apply what they have learnt into real life.
* Content: (Hoạt động giao tiếp, làm việc nhóm hoặc nói)
* Products: Students' performance.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content]

5. WRAP-UP (3 mins)
* Aim: To summarize the lesson.
* Content: The use of the target language.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content]

6. HOMEWORK (1 min)
* Aim: To revise the lesson and prepare for the next one.
* Content: Review the lesson, do exercises in the workbook.
* Products: Students’ textbook and workbook.
* Organization of implementation:
[TẠO BẢNG 2 CỘT: Teacher’s and Ss’ activities | Content]
"""

def generate_lesson_plan(unit_name: str, topic_name: str):
    print(f"🚀 Bắt đầu quy trình tạo giáo án cho: {unit_name} - {topic_name}...")

    extract_task = Task(
        description=(
            f"Sử dụng công cụ 'Fetch All Textbook Content' để lấy toàn bộ dữ liệu sách.\n"
            f"1. Hãy quét toàn bộ dữ liệu từ trên xuống dưới.\n"
            f"2. Trích xuất TOÀN BỘ văn bản và hình ảnh thuộc về bài học: '{unit_name} - {topic_name}'.\n"
            f"3. Lấy sạch sành sanh các bài tập 1, 2, 3, 4... thuộc bài học này.\n"
            f"4. TUYỆT ĐỐI GIỮ NGUYÊN mọi thẻ <img src=...>. Không được bỏ sót bất kỳ hình ảnh nào."
        ),
        expected_output="Một đoạn văn bản chứa toàn bộ nội dung thô (text + ảnh) của bài học được yêu cầu, không sót một chữ.",
        agent=context_extractor
    )

    design_task = Task(
        description=(
            f"Sử dụng dữ liệu thô từ Context Extractor.\n"
            f"Hãy soạn một giáo án chi tiết bằng Markdown, tuân thủ NGHIÊM NGẶT 100% cấu trúc Master Template sau:\n\n"
            f"{MASTER_TEMPLATE}\n\n"
            f"QUAN TRỌNG: Trong phần '3. PRACTICE', bạn phải trình bày ĐẦY ĐỦ tất cả các bài tập tìm được trong dữ liệu thô. "
            f"Các thẻ <img src=...> phải được giữ nguyên vẹn và nhét vào cột 'Content' của bảng Organization of implementation."
        ),
        expected_output="Giáo án hoàn chỉnh định dạng Markdown, chia rõ các phần Warm-up, Presentation, Practice (gồm đầy đủ các Task), Production, Wrap-up, Homework.",
        agent=lesson_plan_designer
    )

    html_task = Task(
        description=(
            f"Nhận giáo án Markdown từ Lesson Plan Designer.\n"
            f"Chuyển đổi giáo án thành một trang HTML hoàn chỉnh.\n"
            f"YÊU CẦU CSS:\n"
            f"- Thêm CSS để trang web đẹp, font chữ Times New Roman hoặc Arial, cỡ chữ 16px, dễ đọc.\n"
            f"- Ở MỌI mục 'Organization of implementation', BẮT BUỘC phải dùng thẻ <table>, có viền nét liền (border: 1px solid black; border-collapse: collapse), padding rõ ràng.\n"
            f"- Bảng gồm đúng 2 cột: 'Teacher’s and Ss’ activities' (chiếm 30% chiều rộng) và 'Content' (chiếm 70% chiều rộng).\n"
            f"- Hình ảnh <img> phải có CSS `max-width: 100%; height: auto;` để không bị tràn ra khỏi bảng.\n"
            f"Cuối cùng, dùng tool 'Save HTML to File' để lưu kết quả vào thư mục './outputs/lesson_plan.html'."
        ),
        expected_output="Thông báo lưu thành công file HTML.",
        agent=html_developer
    )

    lesson_crew = Crew(
        agents=[context_extractor, lesson_plan_designer, html_developer],
        tasks=[extract_task, design_task, html_task],
        process=Process.sequential,
        max_rpm=10
    )

    result = lesson_crew.kickoff()
    print("\n" + "="*50)
    print("✅ QUÁ TRÌNH HOÀN TẤT! HÃY MỞ THƯ MỤC OUTPUTS ĐỂ XEM FILE HTML.")
    print("="*50)

if __name__ == "__main__":
    # Bạn có thể thay đổi Unit và Topic ở đây để test các bài khác
    generate_lesson_plan(
        unit_name="Unit 1: Leisure Time",
        topic_name="A Closer Look 2"
    )