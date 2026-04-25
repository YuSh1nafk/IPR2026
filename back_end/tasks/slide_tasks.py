from crewai import Task
from back_end.utils import prompts
from back_end.tasks.slide_models import SlideDeck
import json


def create_slide_task(agent, lesson_plan_dict):
    plan_json_str = json.dumps(lesson_plan_dict, ensure_ascii=False, indent=2)

    return Task(
        description=f"{prompts.SLIDE_CREATOR_DESC}\n\nHere is the Lesson Plan JSON:\n{plan_json_str}",
        expected_output="A structured JSON representing the slide deck.",
        agent=agent,
        output_pydantic=SlideDeck
    )