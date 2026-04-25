from pydantic import BaseModel
from typing import List

class Activity(BaseModel):
    role: str
    action: str

class Stage(BaseModel):
    name: str
    time: str
    aim: str
    target_language: str
    content: str
    activities: List[Activity]

class LessonPlan(BaseModel):
    unit_name: str
    lesson_name: str
    objectives: List[str]
    materials: List[str]
    stages: List[Stage]