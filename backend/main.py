"""
TruthLens AI — Backend Entry Point
Path: backend/main.py
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from utils.video_processor import save_video, extract_frames

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.3.0",
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
    return {"status": "online", "engine": "TruthLens AI", "version": "0.3.0"}


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    result = save_video(file)
    return {
        "status": "received",
        "case_id": result["case_id"],
        "filename": result["filename"],
        "size_mb": result["size_mb"],
        "next_stage": "frame_extraction",
    }


@app.post("/api/analyze/{case_id}")
async def analyze_case(case_id: str):
    """
    Day 3 scope: frame extraction only.
    Face detection + inference stages plug in here on Day 4.
    """
    extraction = extract_frames(case_id)
    return {
        "status": "frames_extracted",
        "case_id": case_id,
        "fps": extraction["fps"],
        "total_frames": extraction["total_frames"],
        "sampled_frames": extraction["sampled_frames"],
        "next_stage": "face_detection",
    }