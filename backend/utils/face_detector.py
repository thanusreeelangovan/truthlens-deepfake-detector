"""Consistent face cropping for dataset preparation and runtime inference."""
from pathlib import Path

import cv2

CASCADE_PATH = str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
FACE_MARGIN = 0.12


def make_detector():
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    if detector.empty():
        raise RuntimeError("OpenCV face detector could not be loaded.")
    return detector


def largest_face_crop(frame, detector):
    """Return the same padded largest-face crop used at training and inference."""
    if frame is None or frame.size == 0:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    if not len(faces):
        return None
    x, y, width, height = max(faces, key=lambda f: f[2] * f[3])
    margin = int(max(width, height) * FACE_MARGIN)
    x0, y0 = max(0, x - margin), max(0, y - margin)
    x1, y1 = min(frame.shape[1], x + width + margin), min(frame.shape[0], y + height + margin)
    return frame[y0:y1, x0:x1]


def detect_faces(frame_paths: list[str], output_dir: str, timestamps=None) -> dict:
    """Extract one dominant face per sampled frame (not multi-person tracking)."""
    detector = make_detector()
    face_crops, frames_with_faces = [], []
    for frame_index, frame_path in enumerate(frame_paths):
        frame = cv2.imread(frame_path)
        crop = largest_face_crop(frame, detector)
        if crop is None:
            continue
        crop_path = str(Path(output_dir) / f"face_{frame_index:04d}.jpg")
        if not cv2.imwrite(crop_path, crop):
            continue
        frames_with_faces.append(frame_index)
        face_crops.append({
            "frame_index": frame_index,
            "timestamp_seconds": round(float(timestamps[frame_index]), 3) if timestamps is not None else None,
            "path": crop_path,
        })
    return {
        "faces_detected": len(face_crops),
        "frames_with_faces": frames_with_faces,
        "face_crops": face_crops,
    }
