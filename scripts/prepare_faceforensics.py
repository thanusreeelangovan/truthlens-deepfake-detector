"""Build FaceForensics++ manifests without splitting source-paired manipulations."""
import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from training.config import DEFAULT_SPLITS, RAW_ROOT

MANIPULATIONS = {"original": 0, "Deepfakes": 1, "FaceSwap": 1, "Face2Face": 1, "NeuralTextures": 1}


def build_manifest(raw_root: Path, output: Path) -> None:
    rows = []
    parents = {}

    def find(x):
        parents.setdefault(x, x)
        if parents[x] != x:
            parents[x] = find(parents[x])
        return parents[x]

    def union(a, b):
        parents[find(a)] = find(b)

    for video_path in sorted(raw_root.rglob("*.mp4")):
        parts = {part.lower() for part in video_path.parts}
        manipulation_type = next((name for name in MANIPULATIONS if name.lower() in parts), None)
        if "original_sequences" in parts:
            manipulation_type = "original"
        if manipulation_type is None:
            continue
        # A file named 000_003.mp4 can depend on BOTH originals.
        original_names = video_path.stem.split("_") if manipulation_type != "original" else [video_path.stem]
        if len(original_names) > 1:
            for source in original_names[1:]:
                union(original_names[0], source)
        else:
            find(original_names[0])
        rows.append({
            "video_path": str(video_path.resolve()),
            "label": MANIPULATIONS[manipulation_type],
            "manipulation_type": manipulation_type,
            "video_id": hashlib.sha256(str(video_path.resolve()).encode()).hexdigest()[:20],
            "_original_name": original_names[0],
        })
    if not rows:
        raise ValueError(f"No FaceForensics++ MP4 videos found under {raw_root}.")
    for row in rows:
        row["source_video_id"] = hashlib.sha256(find(row.pop("_original_name")).encode()).hexdigest()[:20]
    # Some source-pair graphs can form one giant connected component.
    # Do not silently break these components across splits.
    groups = defaultdict(int)
    for row in rows:
        groups[row["source_video_id"]] += 1
    if max(groups.values()) > len(rows) // 2:
        print("WARNING: Largest connected source group comprises more than half the data.")
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["video_path", "label", "manipulation_type", "video_id", "source_video_id"]
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} videos to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_SPLITS)
    args = parser.parse_args()
    build_manifest(args.raw_root, args.output)
