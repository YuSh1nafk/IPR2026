from crewai import Task
from back_end.utils import prompts
from back_end.tasks.lesson_plan_models import LessonPlan

def create_analyze_task(agent, lesson_name, context_text):
    return Task(
        description=f"Analyze the content for the section '{lesson_name}'. Extract the main grammar, vocabulary, and summarize the numbered tasks from this text:\n{context_text}",
        expected_output="A summary of target language and a list of numbered tasks found in the text.",
        agent=agent
    )

def create_lesson_plan_task(agent, lesson_name, context_text):
    return Task(
        description=prompts.LESSON_PLAN_TASK_DESC.format(
            lesson_name=lesson_name,
            context=context_text
        ),
        expected_output="A structured JSON representing the lesson plan.",
        agent=agent,
        output_pydantic=LessonPlan
    )