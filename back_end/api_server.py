import os
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import shutil
from pymilvus import connections, utility
from zilliz_database.multimodal_ingest import main as run_ingest
from zilliz_database.export_zilliz_to_html import export_milvus_to_html
from main_lesson_plan import main as run_lesson_plan
from main_slide import main as run_slide_generator

app = FastAPI(title="EdTech AI Master API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("file", exist_ok=True)

MILVUS_URI = os.getenv("ZILLIZ_URI", "http://localhost:19530")
MILVUS_TOKEN = os.getenv("ZILLIZ_TOKEN", "")

# ==========================================
# 1. API UPLOAD SÁCH & CHẠY INGEST (ZILLIZ)
# ==========================================
@app.post("/api/upload-and-ingest")
async def api_upload_and_ingest(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        col_name: str = Form(...)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")

    try:
        connections.connect(alias="limit_check", uri=MILVUS_URI, token=MILVUS_TOKEN)
        existing_collections = utility.list_collections(using="limit_check")
        if col_name not in existing_collections and len(existing_collections) >= 5:
            connections.disconnect(alias="limit_check")
            raise HTTPException(
                status_code=400,
                detail=f"Zilliz đã đầy (hiện có {len(existing_collections)}/5 collections). Vui lòng xóa bớt trước khi tạo cuốn sách mới."
            )
        connections.disconnect(alias="limit_check")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối Zilliz: {str(e)}")

    save_path = os.path.join("file", file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_ingest, save_path, col_name)

    return {
        "status": "success",
        "message": f"Đã nhận file {file.filename}. Đang đẩy dữ liệu lên Zilliz (Collection: {col_name}) ngầm..."
    }


# ==========================================
# 2. API XUẤT DATABASE ĐỂ KIỂM TRA (ZILLIZ DUMP)
# ==========================================
@app.get("/api/database-preview", response_class=HTMLResponse)
async def api_database_preview(col_name: str):
    """
    Frontend gọi API này với tham số query: /api/database-preview?col_name=Tên_Collection
    """
    if not col_name:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp tham số col_name")

    filename = f"zilliz_database/database_dump_{col_name}.html"

    try:
        html_content = export_milvus_to_html(col_name, filename)

        if not html_content:
            raise HTTPException(status_code=404,
                                detail=f"Không tìm thấy dữ liệu hoặc collection '{col_name}' không tồn tại.")

        return html_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. API SOẠN GIÁO ÁN
# ==========================================
@app.post("/api/generate-lesson-plan")
async def api_generate_lesson_plan(
        background_tasks: BackgroundTasks,
        col_name: str = Form(...),
        unit_title: str = Form("FULL LESSON PLAN")
):
    if not col_name:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp col_name")

    output_filename = f"outputs/{col_name}_LessonPlan.html"

    background_tasks.add_task(run_lesson_plan, col_name, unit_title, output_filename)

    return {
        "status": "success",
        "message": f"Quá trình phân tích AI cho '{col_name}' đang chạy ngầm.",
        "expected_output": output_filename
    }


# ==========================================
# 4. API TẠO SLIDE POWERPOINT
# ==========================================
@app.post("/api/generate-slides")
async def api_generate_slides(
        background_tasks: BackgroundTasks,
        col_name: str = Form(...)
):
    lesson_json = f"outputs/{col_name}_lesson_plan.json"
    image_json = f"outputs/{col_name}_image_cache.json"
    output_ppt = f"outputs/{col_name}_Presentation.pptx"

    if not os.path.exists(lesson_json):
        raise HTTPException(
            status_code=400,
            detail=f"Chưa tìm thấy giáo án cho '{col_name}'. Vui lòng chạy Soạn giáo án trước."
        )

    background_tasks.add_task(run_slide_generator, col_name, output_ppt)

    return {
        "status": "success",
        "message": f"Đang thiết kế slide cho '{col_name}' dựa trên giáo án có sẵn.",
        "download_link": output_ppt
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)