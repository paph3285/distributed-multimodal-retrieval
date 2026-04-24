import shutil

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from db.postgres_helper import get_job_results
from db.postgres_helper import initialize_database
from api.processing import get_architecture_summary

from api.retrieval import (
    UPLOAD_DIR,
    load_curated_dataset,
    debug_images
)

from api.processing import (
    process_image_upload,
    process_text_query,
    get_job_history,
    get_processing_status,
    get_queue_debug_info
)


app = FastAPI()

from api.retrieval import UPLOAD_DIR, CURATED_DIR

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/curated", StaticFiles(directory=CURATED_DIR), name="curated")

@app.on_event("startup")
def startup_event():
    load_curated_dataset()
    initialize_database()


@app.get("/")
def root():
    return {"message": "A Distributed Multimodal Retrieval System Using CLIP Embeddings API is running"}


@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        assigned_label, image_embedding_shape = await process_image_upload(file_path, file.filename)

        return {
            "filename": file.filename,
            "assigned_label": assigned_label,
            "image_embedding_shape": image_embedding_shape,
            "message": "Image uploaded, embedded, and labeled successfully"
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/text-query/")
async def text_query(query: str):
    results, embedding_shape = await process_text_query(query)

    if len(results) == 0:
        return {
            "query": query,
            "results": [],
            "embedding_shape": embedding_shape,
            "message": "No images available for retrieval yet"
        }

    return {
        "query": query,
        "results": results,
        "embedding_shape": embedding_shape,
        "message": "Top matching images retrieved successfully with FAISS"
    }


@app.get("/debug/images/")
def get_debug_images():
    return debug_images()

@app.get("/debug/jobs/")
def get_debug_jobs():
    return get_job_history()

@app.get("/debug/status/")
def get_debug_status():
    return get_processing_status()

@app.get("/debug/queue/")
def get_debug_queue():
    return get_queue_debug_info()

@app.get("/debug/db/jobs/")
def get_db_jobs():
    return get_job_results()

@app.get("/debug/architecture/")
def get_architecture():
    return get_architecture_summary()
