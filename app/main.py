# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import chat, threads, images, reports, export

app = FastAPI(title="RAG API", version="1.0.0")

app.include_router(chat.router)
app.include_router(threads.router)
app.include_router(images.router)
app.include_router(reports.router)
app.include_router(export.router)
# Mount static files
STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STORAGE_DIR, html=False), name="static")


@app.get("/")
async def root():
    return {"message": "RAG API is running", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
