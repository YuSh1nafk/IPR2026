import os
from crewai import Agent, LLM
from back_end.utils import prompts

llm_mini = LLM(
    model="gpt-4o-mini",
    temperature=0.3
)

llm_pro = LLM(
    model="gpt-4o",
    temperature=0.5
)

def create_context_analyzer_agent():
    return Agent(
        role='Context Analyzer',
        goal='Read raw textbook context from Zilliz and extract key vocabulary, grammar, and topics.',
        backstory='You are a meticulous assistant who extracts core educational materials from raw texts.',
        verbose=True,
        allow_delegation=False,
        llm=llm_mini
    )

def create_planner_agent():
    return Agent(
        role='Senior Curriculum Developer',
        goal='Design structured and engaging English lesson plans.',
        backstory=prompts.PLANNER_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm_pro
    )