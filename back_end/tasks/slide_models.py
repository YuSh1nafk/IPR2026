from pydantic import BaseModel
from typing import List

class Slide(BaseModel):
    title: str
    content_lines: List[str]
    notes: str

class SlideDeck(BaseModel):
    unit_title: str
    lesson_name: str
    slides: List[Slide]