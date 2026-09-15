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
    for manipulation_type, label in MANIPULATIONS.items():
        folder = raw_root / manipulation_type
        if not folder.exists():
            continue
        for video_path in sorted(folder.rglob("*.mp4")):
            rows.append({
                "video_path": str(video_path.resolve()), "label": label,
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
