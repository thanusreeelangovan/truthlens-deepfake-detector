import csv
from pathlib import Path

from backend.utils.aggregation import aggregate_probabilities, longest_consecutive
from scripts.create_splits import create_splits


def test_video_split_has_no_source_leakage(tmp_path):
    source = tmp_path / "videos.csv"; output = tmp_path / "splits.csv"
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video_path", "label", "manipulation_type", "source_video_id"])
        writer.writeheader()
        for index in range(20):
            writer.writerow({"video_path": str(index), "label": index % 2, "manipulation_type": "x", "source_video_id": f"source-{index}"})
    create_splits(source, output)
    rows = list(csv.DictReader(output.open()))
    seen = {}
    for row in rows:
        assert row["source_video_id"] not in seen or seen[row["source_video_id"]] == row["split"]
        seen[row["source_video_id"]] = row["split"]


def test_aggregation_verdicts_and_sequence():
    assert aggregate_probabilities([0.1, 0.2, 0.3])["verdict"] == "LIKELY_AUTHENTIC"
    assert aggregate_probabilities([0.7, 0.8, 0.9, 0.75])["verdict"] == "LIKELY_MANIPULATED"
    assert aggregate_probabilities([0.1, 0.8, 0.2])["verdict"] == "INCONCLUSIVE"
    assert longest_consecutive([1, 2, 3, 7]) == 3


def test_threshold_boundary_requires_consistency():
    result = aggregate_probabilities([0.65, 0.1, 0.1, 0.1])
    assert result["verdict"] != "LIKELY_MANIPULATED"
    assert result["suspicious_frame_count"] == 1
