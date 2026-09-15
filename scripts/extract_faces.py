"""Extract one largest face crop per sampled video frame from a split manifest."""
import argparse
import csv
import os
from pathlib import Path

import cv2

from backend.utils.face_detector import CASCADE_PATH
from training.config import DEFAULT_DFDC_FACE_MANIFEST, DEFAULT_DFDC_MANIFEST, TrainingConfig


def extract_video(row, output_root: Path, config: TrainingConfig):
    capture = cv2.VideoCapture(row["video_path"])
    if not capture.isOpened():
        print(f"SKIP unreadable video: {row['video_path']}")
        return []
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print(f"SKIP video with invalid FPS: {row['video_path']}")
        capture.release()
        return []
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    output_dir = output_root / row["split"] / row["source_video_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []; frame_index = 0; next_time = 0.0; saved = 0
    while True:
        ok, frame = capture.read()
        if not ok: break
        timestamp = frame_index / fps
        if timestamp + 1 / fps >= next_time:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
            if len(faces):
                x, y, width, height = max(faces, key=lambda face: face[2] * face[3])
                margin = int(max(width, height) * 0.12)
                x0, y0 = max(0, x - margin), max(0, y - margin)
                x1, y1 = min(frame.shape[1], x + width + margin), min(frame.shape[0], y + height + margin)
                face_path = output_dir / f"frame_{saved:05d}.jpg"
                cv2.imwrite(str(face_path), frame[y0:y1, x0:x1])
                rows.append({**row, "face_path": str(face_path.resolve()), "frame_index": saved})
                saved += 1
            next_time += config.frame_interval_seconds
        frame_index += 1
    capture.release()
    if not rows:
        print(f"NO FACES: {row['video_path']}")
    return rows


def extract(manifest: Path, output_root: Path, config: TrainingConfig):
    with manifest.open(newline="") as handle:
        videos = list(csv.DictReader(handle))
    rows = []
    for video in videos:
        rows.extend(extract_video(video, output_root, config))
    if not videos:
        raise ValueError(f"Manifest {manifest} contains no video rows.")
    output = output_root / "face_manifest.csv"
    with output.open("w", newline="") as handle:
        fields = [*videos[0].keys(), "face_path", "frame_index"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} face crops to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, default=DEFAULT_DFDC_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_DFDC_FACE_MANIFEST.parent)
    parser.add_argument("--interval-seconds", type=float, default=TrainingConfig.frame_interval_seconds)
    args = parser.parse_args(); extract(args.manifest, args.output_root, TrainingConfig(frame_interval_seconds=args.interval_seconds))
