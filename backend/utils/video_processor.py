import cv2
import os
from pathlib import Path

def extract_frames(video_path: str, max_frames: int = 60, sample_rate: int = 10) -> list[dict]:
    """
    Extract frames from video. Returns list of frame metadata dicts.
    sample_rate: extract 1 frame every N frames
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    frames = []
    frame_idx = 0
    saved = 0

    output_dir = Path(video_path).parent / (Path(video_path).stem + "_frames")
    output_dir.mkdir(exist_ok=True)

    while saved < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_rate == 0:
            frame_path = str(output_dir / f"frame_{saved:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            h, w = frame.shape[:2]
            frames.append({
                "index": saved,
                "original_frame": frame_idx,
                "path": frame_path,
                "width": w,
                "height": h,
            })
            saved += 1

        frame_idx += 1

    cap.release()
    return frames