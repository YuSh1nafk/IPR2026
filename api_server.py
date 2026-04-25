import os
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import shutil

# Import các hàm main() từ 4 file lõi của bạn
from back_end.zilliz_database.multimodal_ingest import main as run_ingest
from back_end.zilliz_database.export_zilliz_to_html import export_milvus_to_html
from back_end.main_lesson_plan import main as run_lesson_plan
from back_end.main_slide import main as run_slide_generator

app = FastAPI(title="EdTech AI Master API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# thư mục lưu file upload
os.makedirs("file", exist_ok=True)


# ==========================================
# 1. API UPLOAD SÁCH & CHẠY INGEST (ZILLIZ)
# ==========================================
@app.post("/api/upload-and-ingest")
async def api_upload_and_ingest(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")

    save_path = "file/uploaded_book.pdf"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_ingest)

    return {
        "status": "success",
        "message": "Đã nhận file PDF. Đang tiến hành phân tích đa phương thức và đẩy lên Zilliz ngầm..."
    }


# ==========================================
# 2. API XUẤT DATABASE ĐỂ KIỂM TRA (ZILLIZ DUMP)
# ==========================================
@app.get("/api/database-preview", response_class=HTMLResponse)
async def api_database_preview():
    filename = "zilliz_database/database_dump_test.html"
    export_milvus_to_html(filename)

    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


# ==========================================
# 3. API SOẠN GIÁO ÁN
# ==========================================
@app.post("/api/generate-lesson-plan")
async def api_generate_lesson_plan(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_lesson_plan)
    return {
        "status": "success",
        "message": "Quá trình tạo Lesson Plan (CrewAI) đang được chạy ngầm."
    }


# ==========================================
# 4. API TẠO SLIDE POWERPOINT
# ==========================================
@app.post("/api/generate-slides")
async def api_generate_slides(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_slide_generator)
    return {
        "status": "success",
        "message": "Quá trình tạo Slide PowerPoint đang được chạy ngầm."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)