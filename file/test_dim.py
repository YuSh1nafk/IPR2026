import os
from google import genai
from dotenv import load_dotenv
# Điền API Key của bạn vào đây

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Thử dùng model ổn định nhất của Google hiện tại
model_name = "gemini-embedding-2-preview"

response = client.models.embed_content(
    model=model_name,
    contents="Hello"
)

# Đếm độ dài của mảng vector trả về
vector_length = len(response.embeddings[0].values)
print(f"Model '{model_name}' có EMBED_DIM là: {vector_length}")