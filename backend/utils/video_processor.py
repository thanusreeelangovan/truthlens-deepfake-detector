"""
Video validation and temporary storage.
Path: backend/utils/video_processor.py

Day 2 scope: validate + save only. Frame extraction lands Day 3.
"""

import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
MAX_FILE_SIZE_MB = 100
UPLOAD_DIR = "storage/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_video(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


def save_video(file: UploadFile) -> dict:
    validate_video(file)

    case_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower()
    dest_path = os.path.join(UPLOAD_DIR, f"{case_id}{ext}")

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        os.remove(dest_path)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit ({size_mb:.1f}MB submitted).",
        )

    return {
        "case_id": case_id,
        "filename": file.filename,
        "path": dest_path,
        "size_mb": round(size_mb, 2),
    }