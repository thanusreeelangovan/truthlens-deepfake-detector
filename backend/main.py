"""
TruthLens AI — Backend Entry Point
Path: backend/main.py
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from utils.video_processor import save_video

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "engine": "TruthLens AI",
        "version": "0.2.0",
    }


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Accepts a video file, validates it, and opens a case file.
    Returns a case_id used by all subsequent pipeline calls.
    """
    result = save_video(file)
    return {
        "status": "received",
        "case_id": result["case_id"],
        "filename": result["filename"],
        "size_mb": result["size_mb"],
        "next_stage": "frame_extraction",
    }