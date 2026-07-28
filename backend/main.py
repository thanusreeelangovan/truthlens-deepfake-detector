from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil, uuid, os, asyncio
from pathlib import Path

app = FastAPI(title="TruthLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "TruthLens API"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    allowed = {".mp4", ".mov", ".avi", ".webm"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}")

    job_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{job_id}{ext}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size_mb = dest.stat().st_size / 1_000_000
    return {"job_id": job_id, "filename": file.filename, "size_mb": round(size_mb, 2), "status": "uploaded"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    # Week 1 stub — real pipeline wired in Week 2
    return {"job_id": job_id, "status": "queued", "progress": 0}
@app.get("/")
async def root():
    return {
        "message": "TruthLens API is running",
        "docs": "/docs",
        "health": "/health"
    }