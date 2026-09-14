"""
Video validation, storage, and frame extraction.
Path: backend/utils/video_processor.py
"""

import os
import uuid
import shutil
import cv2
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
MAX_FILE_SIZE_MB = 100
UPLOAD_DIR = "storage/uploads"
FRAMES_DIR = "storage/frames"
SAMPLE_INTERVAL_SECONDS = 1.0

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)


def validate_video(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A video filename is required.")
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

    capture = cv2.VideoCapture(dest_path)
    valid = capture.isOpened() and capture.get(cv2.CAP_PROP_FRAME_COUNT) > 0
    capture.release()
    if not valid:
        os.remove(dest_path)
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable video.")

    return {
        "case_id": case_id,
        "filename": file.filename,
        "path": dest_path,
        "size_mb": round(size_mb, 2),
    }


def find_video_path(case_id: str) -> str:
    for ext in ALLOWED_EXTENSIONS:
        candidate = os.path.join(UPLOAD_DIR, f"{case_id}{ext}")
        if os.path.exists(candidate):
            return candidate
    raise HTTPException(status_code=404, detail=f"No case file found for {case_id}")


def extract_frames(case_id: str) -> dict:
    """
    Samples at a time interval so sampling is independent of source FPS.
    """
    video_path = find_video_path(case_id)
    case_frame_dir = os.path.join(FRAMES_DIR, case_id)
    os.makedirs(case_frame_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Could not read video file — it may be corrupted.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        cap.release()
        raise HTTPException(status_code=400, detail="Could not determine the video's frame rate.")

    frame_paths = []
    idx = 0
    saved = 0
    next_sample_time = 0.0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp = idx / fps
        if timestamp + (1 / fps) >= next_sample_time:
            frame_path = os.path.join(case_frame_dir, f"frame_{saved:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            saved += 1
            next_sample_time += SAMPLE_INTERVAL_SECONDS
        idx += 1
    cap.release()

    return {
        "case_id": case_id,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "sampled_frames": saved,
        "frame_paths": frame_paths,
    }