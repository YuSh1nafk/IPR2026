import os
from dotenv import load_dotenv
from crewai import Crew, Process

from utils.json_handler import load_from_json
from agents.slide_agents import create_slide_designer_agent
from tasks.slide_tasks import create_slide_task
from utils.ppt_renderer import create_unified_ppt

load_dotenv()


def main(col_name: str, output_filename: str):
    print(f"▶️ BẮT ĐẦU TẠO SLIDE CHO: {col_name}")

    lesson_json = f"outputs/{col_name}_lesson_plan.json"
    image_json = f"outputs/{col_name}_image_cache.json"

    try:
        lesson_data = load_from_json(lesson_json)
        image_cache = load_from_json(image_json)
    except Exception as e:
        print(f"Lỗi load dữ liệu: {e}")
        return

    slide_agent = create_slide_designer_agent()
    all_slide_decks = []

    for idx, plan_dict in enumerate(lesson_data):
        lesson_name = plan_dict.get("lesson_name", f"Lesson {idx + 1}")
        print(f"\n🎨 AI đang thiết kế slide cho: {lesson_name}...")

        slide_task = create_slide_task(slide_agent, plan_dict)
        slide_crew = Crew(agents=[slide_agent], tasks=[slide_task], verbose=True)

        result = slide_crew.kickoff()
        all_slide_decks.append(result.pydantic)

    create_unified_ppt(
        all_slide_decks=all_slide_decks,
        image_cache=image_cache,
        output_filename=output_filename,
        template_path="templates/template_1.pptx"
    )
    print(f"✅ Đã tạo xong Slide cho {col_name} tại {output_filename}")