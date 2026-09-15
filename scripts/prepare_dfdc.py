"""Build a video-level DFDC manifest from Kaggle metadata.json files."""
import argparse
import csv
import json
import os
from pathlib import Path

from training.config import DEFAULT_DFDC_MANIFEST, DFDC_ROOT

LABELS = {"REAL": 0, "FAKE": 1}
REQUIRED_FIELDS = {"label"}


def find_metadata_files(raw_root: Path) -> list[Path]:
    files = sorted(raw_root.rglob("metadata.json"))
    if not files:
        raise FileNotFoundError(f"No metadata.json found under {raw_root}.")
    return files


def normalise_original(value: str | None) -> str | None:
    if not value:
        return None
    return Path(value).name


def read_metadata(metadata_path: Path) -> list[dict]:
    data = json.loads(metadata_path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {metadata_path}.")
    rows = []
    for filename, item in data.items():
        if not isinstance(item, dict) or not REQUIRED_FIELDS.issubset(item):
            raise ValueError(f"Invalid metadata entry for '{filename}' in {metadata_path}.")
        label = str(item["label"]).upper()
        if label not in LABELS:
            raise ValueError(f"Unsupported label '{item['label']}' for '{filename}' in {metadata_path}.")
        rows.append({
            "filename": filename,
            "label": label,
            "numeric_label": LABELS[label],
            "original": normalise_original(item.get("original")),
            "metadata_path": str(metadata_path.resolve()),
            "video_path": str((metadata_path.parent / filename).resolve()),
        })
    return rows


def assign_source_groups(rows: list[dict]) -> None:
    originals = {row["filename"] for row in rows if row["label"] == "REAL"}
    for row in rows:
        original = row["original"]
        group_name = original if original and original in originals else (original or row["filename"])
        row["source_group"] = group_name


def build_manifest(raw_root: Path, output: Path, strict: bool = False) -> dict:
    rows = []
    for metadata_path in find_metadata_files(raw_root):
        rows.extend(read_metadata(metadata_path))
    for row in rows:
        if not Path(row["video_path"]).is_file():
            candidates = list(raw_root.rglob(Path(row["filename"]).name))
            if len(candidates) == 1:
                row["video_path"] = str(candidates[0].resolve())
    assign_source_groups(rows)
    missing = [row["video_path"] for row in rows if not Path(row["video_path"]).is_file()]
    if strict and missing:
        raise FileNotFoundError(f"{len(missing)} videos listed in metadata are missing. First: {missing[0]}")
    present_rows = [row for row in rows if Path(row["video_path"]).is_file()]
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["video_path", "filename", "label", "numeric_label", "original", "source_group", "metadata_path"]
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(present_rows)
    stats = {
        "metadata_files": len(find_metadata_files(raw_root)), "listed_videos": len(rows),
        "present_videos": len(present_rows), "missing_files": missing,
        "real_videos": sum(row["label"] == "REAL" for row in present_rows),
        "fake_videos": sum(row["label"] == "FAKE" for row in present_rows),
    }
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=Path(os.getenv("TRUTHLENS_DFDC_ROOT", DFDC_ROOT)))
    parser.add_argument("--output", type=Path, default=DEFAULT_DFDC_MANIFEST)
    parser.add_argument("--strict", action="store_true", help="Fail if metadata lists any missing video files.")
    args = parser.parse_args()
    build_manifest(args.raw_root, args.output, args.strict)
