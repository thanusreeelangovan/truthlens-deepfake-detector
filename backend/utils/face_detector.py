import cv2
import numpy as np
from pathlib import Path

# Download haarcascade XML once: OpenCV ships it, this path finds it
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def detect_faces(frame_path: str) -> dict:
    """Returns face count and bounding boxes for a single frame."""
    img = cv2.imread(frame_path)
    if img is None:
        return {"faces": 0, "boxes": []}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    boxes = []
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

    return {
        "faces": len(boxes),
        "boxes": boxes,
        "frame_path": frame_path,
    }