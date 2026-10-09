"""Extract consistent largest-face crops using the shared runtime detector."""
import argparse
import csv
import hashlib
from pathlib import Path

import cv2

from backend.utils.face_detector import make_detector, largest_face_crop
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
    detector = make_detector()
    # A source group can contain both authentic and manipulated videos.
    # Never share a face-crop directory between different videos.
    video_id = row.get("video_id") or hashlib.sha256(
        str(Path(row["video_path"]).resolve()).encode("utf-8")
    ).hexdigest()[:20]
    output_dir = output_root / row["split"] / video_id
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    decoded_index, sample_index, next_time = 0, 0, 0.0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = decoded_index / fps
            if timestamp + 1 / fps >= next_time:
                face = largest_face_crop(frame, detector)
                if face is not None:
                    face_path = output_dir / f"frame_{sample_index:05d}.jpg"
                    if cv2.imwrite(str(face_path), face):
                        rows.append({
                            **row,
                            "video_id": video_id,
                            "face_path": str(face_path.resolve()),
                            "frame_index": sample_index,
                            "timestamp_seconds": round(timestamp, 3),
                        })
                sample_index += 1
                next_time += config.frame_interval_seconds
            decoded_index += 1
    finally:
        capture.release()
    if not rows:
        print(f"NO FACES: {row['video_path']}")
    return rows


def extract(manifest: Path, output_root: Path, config: TrainingConfig):
    with manifest.open(newline="") as handle:
        videos = list(csv.DictReader(handle))
    if not videos:
        raise ValueError(f"Manifest {manifest} contains no video rows.")
    if config.frame_interval_seconds <= 0:
        raise ValueError("Frame interval must be positive.")
    output_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for video in videos:
        rows.extend(extract_video(video, output_root, config))
    output = output_root / "face_manifest.csv"
    fields = list(dict.fromkeys([*videos[0].keys(), "video_id", "face_path", "frame_index", "timestamp_seconds"]))
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} face crops to {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_DFDC_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_DFDC_FACE_MANIFEST.parent)
    parser.add_argument("--interval-seconds", type=float, default=TrainingConfig.frame_interval_seconds)
    args = parser.parse_args()
    extract(args.manifest, args.output_root, TrainingConfig(frame_interval_seconds=args.interval_seconds))
