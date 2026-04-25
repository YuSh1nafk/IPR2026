import os
import re
from dotenv import load_dotenv
from crewai import Crew, Process
from openai import OpenAI

from agents.lesson_plan_agents import create_context_analyzer_agent, create_planner_agent
from tasks.lesson_plan_tasks import create_analyze_task, create_lesson_plan_task
from utils.html_renderer import render_full_unit_to_html
from pymilvus import connections, Collection

from utils.json_handler import save_to_json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

IMAGE_CACHE = {}

# Danh sách các "Đề mục to" tiêu chuẩn trong sách Global Success
BIG_HEADINGS = [
    "GETTING STARTED",
    "A CLOSER LOOK 1",
    "A CLOSER LOOK 2",
    "COMMUNICATION",
    "SKILLS 1",
    "SKILLS 2",
    "LOOKING BACK",
    "PROJECT"
]


def split_context_by_headings(raw_context: str):
    """
    Hàm này chia một đoạn text dài thòong thành các phần tử từ khóa.
    Ví dụ: Nó sẽ tách text từ "GETTING STARTED" cho đến khi gặp "A CLOSER LOOK 1".
    """
    # Tạo Regex pattern
    pattern = r"(?i)\b(" + "|".join(BIG_HEADINGS) + r")\b"

    # Tìm tất cả các vị trí xuất hiện của Đề mục to
    matches = list(re.finditer(pattern, raw_context))

    sections = []
    for i in range(len(matches)):
        heading_name = matches[i].group(1).upper()
        start_idx = matches[i].end()

        # Nếu là đề mục cuối cùng thì lấy đến hết chuỗi, nếu không thì lấy đến đề mục tiếp theo
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(raw_context)

        content = raw_context[start_idx:end_idx].strip()
        sections.append({
            "lesson_name": heading_name,
            "content": content
        })

    return sections


def analyze_image_with_vision(seq_id, base64_str):
    """
    Dùng GPT-4o-mini soi ảnh. Nếu có chữ/bảng biểu -> Trả về text.
    Nếu chỉ là người/cảnh vật -> Trả về None.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "If this image contains readable text, tables, grammar rules, or exercises, reply 'YES' followed by a transcription of the text. If it is purely a decorative picture (like people, landscape, objects without text), reply 'NO'."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}}
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.0
        )
        result = response.choices[0].message.content.strip()

        if result.startswith("YES"):
            transcription = result[3:].strip()
            return transcription
        return None
    except Exception as e:
        print(f"Lỗi khi soi ảnh {seq_id}: {e}")
        return None


def get_real_context_from_zilliz(collection_name="Global_Success_Book"):
    print(f"🔄 Đang kết nối tới Zilliz database: {collection_name}...")
    connections.connect(alias="default", uri=os.getenv("ZILLIZ_URI"), token=os.getenv("ZILLIZ_TOKEN"))

    col = Collection(collection_name)
    col.load()

    results = col.query(
        expr="seq_id >= 0",
        output_fields=["seq_id", "data_type", "content"],
        limit=10000
    )
    results.sort(key=lambda x: x['seq_id'])

    full_text_context = ""

    for item in results:
        if item['data_type'] == 'text':
            full_text_context += f"\n[ID: {item['seq_id']}] - TEXT:\n{item['content']}\n"

        elif item['data_type'] == 'image':
            seq_id = item['seq_id']
            base64_str = item['content']

            print(f"👀 Đang soi ảnh ID {seq_id}...")
            transcription = analyze_image_with_vision(seq_id, base64_str)

            if transcription:
                print(f"   -> Ảnh {seq_id} có chứa bài học. Đã đánh dấu.")
                IMAGE_CACHE[seq_id] = base64_str
                tag = f"[IMAGE_TAG_{seq_id}]"
                full_text_context += f"\n[ID: {seq_id}] - IMAGE CONTENT:\n{transcription}\n(Note for Planner: To display this image in the lesson plan, use the exact string {tag} in the action field).\n"
            else:
                print(f"   -> Ảnh {seq_id} chỉ là minh họa. Bỏ qua.")

    return full_text_context



def main():
    raw_context = get_real_context_from_zilliz("Global_Success_Book_4")



    lessons = split_context_by_headings(raw_context)


    if not lessons:
        print("❌ Không tìm thấy 'Đề mục to' nào. Có thể raw_context bị rỗng.")
        return

    analyzer_agent = create_context_analyzer_agent()
    planner_agent = create_planner_agent()

    all_lesson_plans = []

    for idx, lesson in enumerate(lessons):
        print(f"\n==================================================")
        print(f"📚 Đang xử lý bài học ({idx + 1}/{len(lessons)}): {lesson['lesson_name']}")
        print(f"==================================================")

        analyze_task = create_analyze_task(analyzer_agent, lesson["lesson_name"], lesson["content"])
        plan_task = create_lesson_plan_task(planner_agent, lesson["lesson_name"], lesson["content"])

        lesson_crew = Crew(
            agents=[analyzer_agent, planner_agent],
            tasks=[analyze_task, plan_task],
            process=Process.sequential,
            verbose=True
        )

        result = lesson_crew.kickoff()

        all_lesson_plans.append(result.pydantic.model_dump())
        print(f"✅ Đã soạn xong {lesson['lesson_name']} và lưu vào bộ nhớ tạm.")

        save_to_json(all_lesson_plans, "outputs/lesson_plan.json")

        save_to_json(IMAGE_CACHE, "outputs/image_cache.json")



    # MỚI: Sau khi vòng lặp for kết thúc (tức là đã chạy xong cả Unit)
    # Ta mới gọi hàm render ra 1 file HTML duy nhất
    print("\n⏳ Đang tiến hành gộp và render file HTML tổng...")
    render_full_unit_to_html(
        all_plans_dict_list=all_lesson_plans,
        unit_title="UNIT 1: LEISURE TIME - FULL LESSON PLAN",
        image_cache=IMAGE_CACHE,
        output_filename="outputs/Full_Unit1_LessonPlan_2.html"
    )


if __name__ == "__main__":
    main()