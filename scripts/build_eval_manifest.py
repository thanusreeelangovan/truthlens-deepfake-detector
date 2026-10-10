"""Make a small, reproducible REAL/FAKE evaluation set from authorized DFDC files.

Select pairs by shared source_group, never by random filenames or competition
test_videos.zip (which has no public ground-truth labels).
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from scripts.prepare_dfdc import assign_source_groups, find_metadata_files, read_metadata

FIELDS = ("video_path", "label", "dataset", "source_group", "original", "filename")


def build_eval_manifest(raw_root: Path, output: Path, pairs: int = 10, seed: int = 42) -> list[dict]:
    raw_root = Path(raw_root)
    output = Path(output)
    if pairs < 1:
        raise ValueError("Requested pair count must be positive.")

    rows = []
    for metadata in find_metadata_files(raw_root):
        rows.extend(read_metadata(metadata))
    # Kaggle archives occasionally place metadata.json one directory above MP4 files.
    # If a basename is ambiguous, refuse to guess which video metadata references.
    for row in rows:
        path = Path(row["video_path"])
        if not path.is_file():
            candidates = list(raw_root.rglob(Path(row["filename"]).name))
            if len(candidates) == 1:
                row["video_path"] = str(candidates[0].resolve())
            else:
                row["video_path"] = ""
    rows = [row for row in rows if row["video_path"] and Path(row["video_path"]).is_file()]
    assign_source_groups(rows)
    groups = defaultdict(lambda: {"REAL": [], "FAKE": []})
    for row in rows:
        groups[row["source_group"]][row["label"]].append(row)

    eligible = [key for key, group in groups.items() if group["REAL"] and group["FAKE"]]
    rng = random.Random(seed)
    rng.shuffle(eligible)
    chosen = eligible[:pairs]
    if not chosen:
        raise ValueError("No matched REAL/FAKE source pairs found. Check metadata and file paths.")

    selected = []
    for source_group in chosen:
        source = groups[source_group]
        for label in ("REAL", "FAKE"):
            sample = rng.choice(sorted(source[label], key=lambda item: item["video_path"]))
            selected.append({
                "video_path": sample["video_path"],
                "label": label,
                "dataset": "DFDC_train_sample",
                "source_group": source_group,
                "original": sample["original"] or "",
                "filename": sample["filename"],
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(selected)
    print(f"Wrote {len(selected)} labelled clips ({len(chosen)} matched source pairs) to {output}")
    if len(chosen) < pairs:
        print(f"Only {len(chosen)} matched pairs available; requested {pairs}.")
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dfdc-root", type=Path, required=True,
                        help="Extracted DFDC train_sample_videos folder or parent directory.")
    parser.add_argument("--output", type=Path, default=Path("data/processed/eval/dfdc_pairs.csv"))
    parser.add_argument("--pairs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    build_eval_manifest(args.dfdc_root, args.output, pairs=args.pairs, seed=args.seed)
