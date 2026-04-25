import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview", contents="tell me how does facebook so popular"
)
print(response.text)