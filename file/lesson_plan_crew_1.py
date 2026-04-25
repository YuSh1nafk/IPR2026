import os
import configparser
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

from toc_tools_t import milvus_content_search_t
from custom_tools_t import save_html_tool

load_dotenv()

# ==========================================
# 1. ĐỌC CẤU HÌNH TỪ FILE PROMPTS.INI
# ==========================================
config = configparser.ConfigParser(interpolation=None)
config.read('prompts.ini', encoding='utf-8')

agents_cfg = config['agents']
tasks_cfg = config['tasks']
tpl_cfg = config['templates']

# Khởi tạo LLM (Khuyến nghị dùng flash 2.0 hoặc pro cho tác vụ suy luận sư phạm)
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=os.getenv("GEMINI_API_KEY")
)
# ==========================================
# 2. KHỞI TẠO AGENTS
# ==========================================
curriculum_developer = Agent(
    role=agents_cfg['dev_role'],
    goal=agents_cfg['dev_goal'],
    backstory=agents_cfg['dev_backstory'],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[milvus_content_search_t]  # Cấp cho nó quyền chui vào Zilliz lấy data SGK
)

html_developer = Agent(
    role=agents_cfg['html_role'],
    goal=agents_cfg['html_goal'],
    backstory=agents_cfg['html_backstory'],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[save_html_tool]  # Cấp cho nó quyền lưu file HTML xuống máy
)


# ==========================================
# 3. HÀM CHẠY CREWAI CHÍNH
# ==========================================
def generate_lesson_plan(subject: str, unit_name: str, topic_name: str):
    print(f"🚀 Bắt đầu quy trình tạo giáo án cho: {unit_name} - {topic_name}...")

    # Task 1: Truy vấn Database và Soạn giáo án
    draft_task = Task(
        description=tasks_cfg['draft_desc'].format(
            subject=subject,
            unit=unit_name,
            topic=topic_name,
            template=tpl_cfg['lesson_plan']
        ),
        expected_output=tasks_cfg['draft_expected'],
        agent=curriculum_developer,
    )

    # Task 2: Chuyển giáo án thành bảng HTML và lưu file
    html_task = Task(
        description=tasks_cfg['html_desc'],
        expected_output=tasks_cfg['html_expected'],
        agent=html_developer,
    )

    # Lắp ráp dây chuyền (Crew) chạy tuần tự (Sequential)
    lesson_crew = Crew(
        agents=[curriculum_developer, html_developer],
        tasks=[draft_task, html_task],
        process=Process.sequential
    )

    # Kích hoạt (Kickoff)
    result = lesson_crew.kickoff()
    print("\n" + "=" * 50)
    print("✅ QUÁ TRÌNH HOÀN TẤT!")
    print("KẾT QUẢ TỪ CREWAI:")
    print(result)
    print("=" * 50)


if __name__ == "__main__":
    # Chạy thử với dữ liệu môn Tiếng Anh 8, Unit 1, phần A Closer Look 2
    generate_lesson_plan(
        subject="tieng_anh",
        unit_name="Unit 1: Leisure Time",
        topic_name="A Closer Look 1"
    )