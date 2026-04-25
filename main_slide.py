# main_slide.py
import os
from dotenv import load_dotenv
from crewai import Crew, Process

from utils.json_handler import load_from_json
from agents.slide_agents import create_slide_designer_agent
from tasks.slide_tasks import create_slide_task
from utils.ppt_renderer import create_unified_ppt

load_dotenv()


def main():
    print("▶️ BẮT ĐẦU LUỒNG 2: TẠO SLIDE POWERPOINT")

    lesson_data = load_from_json("outputs/lesson_plan.json")
    image_cache = load_from_json("outputs/image_cache.json")  # MỚI

    slide_agent = create_slide_designer_agent()
    all_slide_decks = []

    for idx, plan_dict in enumerate(lesson_data):
        lesson_name = plan_dict.get("lesson_name", f"Lesson {idx + 1}")
        print(f"\n🎨 Đang thiết kế slide cho bài: {lesson_name}...")

        slide_task = create_slide_task(slide_agent, plan_dict)
        slide_crew = Crew(agents=[slide_agent], tasks=[slide_task], verbose=True)

        result = slide_crew.kickoff()
        all_slide_decks.append(result.pydantic)

    create_unified_ppt(
        all_slide_decks=all_slide_decks,
        image_cache=image_cache,
        output_filename="outputs/Full_Unit_Presentation_1.pptx",
        template_path="templates/template_1.pptx"
    )


if __name__ == "__main__":
    main()