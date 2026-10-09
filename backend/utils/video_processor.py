"""Bounded video upload and timestamped frame sampling."""
import os
import uuid
from pathlib import Path

import cv2
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
MAX_FILE_SIZE_MB = 100
MAX_UPLOAD_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_DURATION_SECONDS = 120
MAX_SAMPLED_FRAMES = 120
SAMPLE_INTERVAL_SECONDS = 1.0
ROOT_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = str(ROOT_DIR / "storage" / "uploads")
FRAMES_DIR = str(ROOT_DIR / "storage" / "frames")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(FRAMES_DIR).mkdir(parents=True, exist_ok=True)


def validate_video(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(400, "A video filename is required.")
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported format '{extension}'.")


def save_video(file: UploadFile) -> dict:
    validate_video(file)
    case_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix.lower()
    dest_path = Path(UPLOAD_DIR) / f"{case_id}{extension}"
    size = 0
    try:
        with dest_path.open("wb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"File exceeds the {MAX_FILE_SIZE_MB} MB upload limit.")
                target.write(chunk)
        capture = cv2.VideoCapture(str(dest_path))
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            valid = capture.isOpened() and fps > 0 and frame_count > 0
            duration = frame_count / fps if valid else 0
        finally:
            capture.release()
        if not valid:
            raise HTTPException(400, "Uploaded file is not a readable video.")
        if duration > MAX_DURATION_SECONDS:
            raise HTTPException(413, f"Video duration must not exceed {MAX_DURATION_SECONDS} seconds.")
    except BaseException:
        dest_path.unlink(missing_ok=True)
        raise
    return {"case_id": case_id, "filename": file.filename, "path": str(dest_path), "size_mb": round(size / 1048576, 2)}


def find_video_path(case_id: str) -> str:
    try:
        if str(uuid.UUID(case_id)) != case_id:
            raise ValueError("Noncanonical UUID")
    except (TypeError, ValueError):
        raise HTTPException(400, "Invalid case ID.") from None
    for extension in ALLOWED_EXTENSIONS:
        candidate = Path(UPLOAD_DIR) / f"{case_id}{extension}"
        if candidate.is_file():
            return str(candidate)
    raise HTTPException(404, f"No uploaded video for case {case_id}.")


def extract_frames(case_id: str) -> dict:
    video_path = find_video_path(case_id)
    frame_dir = Path(FRAMES_DIR) / case_id
    frame_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(400, "Could not read uploaded video.")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        cap.release()
        raise HTTPException(400, "Could not determine video frame rate.")
    if total_frames > 0 and total_frames / fps > MAX_DURATION_SECONDS:
        cap.release()
        raise HTTPException(413, "Video duration limit exceeded.")
    frame_paths, timestamps = [], []
    decoded = 0
    next_sample_time = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            timestamp = decoded / fps
            if timestamp > MAX_DURATION_SECONDS:
                raise HTTPException(413, "Video duration limit exceeded.")
            if timestamp + 1 / fps >= next_sample_time:
                if len(frame_paths) >= MAX_SAMPLED_FRAMES:
                    break
                frame_path = frame_dir / f"frame_{len(frame_paths):04d}.jpg"
                if cv2.imwrite(str(frame_path), frame):
                    frame_paths.append(str(frame_path))
                    timestamps.append(round(timestamp, 3))
                next_sample_time += SAMPLE_INTERVAL_SECONDS
            decoded += 1
    finally:
        cap.release()
    return {"case_id": case_id, "fps": round(fps, 2), "total_frames": total_frames,
            "sampled_frames": len(frame_paths), "frame_paths": frame_paths, "frame_timestamps": timestamps}
