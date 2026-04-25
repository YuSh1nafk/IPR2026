from crewai import Agent, LLM

llm_mini = LLM(model="gpt-4o-mini", temperature=0.3)

def create_slide_designer_agent():
    return Agent(
        role='Expert Presentation Designer',
        goal='Convert detailed educational lesson plans into concise, student-friendly presentation slides.',
        backstory='You are a master at visual communication, knowing exactly how to summarize long texts into punchy, easy-to-read bullet points for students.',
        verbose=True,
        allow_delegation=False,
        llm=llm_mini
    )