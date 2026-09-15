"""Assign complete source videos to reproducible train/validation/test splits."""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from training.config import DEFAULT_SPLITS


def create_splits(input_csv: Path, output_csv: Path, seed: int = 42) -> None:
    with input_csv.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups = defaultdict(list)
    for row in rows:
        groups[row["source_video_id"]].append(row)
    source_ids = list(groups)
    random.Random(seed).shuffle(source_ids)
    train_end = int(len(source_ids) * 0.70)
    validation_end = train_end + int(len(source_ids) * 0.15)
    split_by_source = {source_id: "train" for source_id in source_ids[:train_end]}
    split_by_source.update({source_id: "validation" for source_id in source_ids[train_end:validation_end]})
    split_by_source.update({source_id: "test" for source_id in source_ids[validation_end:]})
    for row in rows:
        row["split"] = split_by_source[row["source_video_id"]]
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*rows[0].keys(), "split"])
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} videos across {len(source_ids)} source groups to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    create_splits(args.input, args.output, args.seed)
