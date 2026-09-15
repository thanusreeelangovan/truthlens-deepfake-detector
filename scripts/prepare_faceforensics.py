"""Create a video-level manifest for a manually downloaded FaceForensics++ c23 set."""
import argparse
import csv
import hashlib
from pathlib import Path

from training.config import DEFAULT_SPLITS, RAW_ROOT

MANIPULATIONS = {"original": 0, "Deepfakes": 1, "FaceSwap": 1, "Face2Face": 1, "NeuralTextures": 1}


def source_id(path: Path) -> str:
    return hashlib.sha1(path.stem.encode()).hexdigest()[:16]


def build_manifest(raw_root: Path, output: Path) -> None:
    rows = []
    for video_path in sorted(raw_root.rglob("*.mp4")):
        parts = {part.lower() for part in video_path.parts}
        manipulation_type = next((name for name in MANIPULATIONS if name.lower() in parts), None)
        if "original_sequences" in parts:
            manipulation_type = "original"
        if manipulation_type is None:
            continue
        rows.append({
            "video_path": str(video_path.resolve()), "label": MANIPULATIONS[manipulation_type],
            "manipulation_type": manipulation_type, "source_video_id": source_id(video_path),
        })
    if not rows:
        raise SystemExit(f"No .mp4 files found under {raw_root}. Obtain FaceForensics++ c23 through its official access process.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video_path", "label", "manipulation_type", "source_video_id"])
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} videos to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_SPLITS)
    args = parser.parse_args()
    build_manifest(args.raw_root, args.output)
