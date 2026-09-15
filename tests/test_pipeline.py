import csv
import json
from pathlib import Path

from backend.utils.aggregation import aggregate_probabilities, longest_consecutive
from backend.main import app
from fastapi.testclient import TestClient
from scripts.create_splits import create_splits
from scripts.prepare_dfdc import build_manifest


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


def test_dfdc_metadata_mapping_and_original_group(tmp_path):
    root = tmp_path / "dfdc"
    root.mkdir()
    video_dir = root / "train_sample_videos"
    video_dir.mkdir()
    for filename in ("real.mp4", "fake.mp4"):
        (video_dir / filename).write_bytes(b"video")
    (root / "metadata.json").write_text(json.dumps({
        "real.mp4": {"label": "REAL", "original": None},
        "fake.mp4": {"label": "FAKE", "original": "real.mp4"},
    }))
    output = tmp_path / "manifest.csv"
    stats = build_manifest(root, output)
    rows = list(csv.DictReader(output.open()))
    assert stats["real_videos"] == 1
    assert stats["fake_videos"] == 1
    assert {row["numeric_label"] for row in rows} == {"0", "1"}
    assert rows[0]["source_group"] == rows[1]["source_group"]


def test_dfdc_missing_video_is_reported(tmp_path, capsys):
    (tmp_path / "metadata.json").write_text(json.dumps({"missing.mp4": {"label": "REAL"}}))
    output = tmp_path / "manifest.csv"
    stats = build_manifest(tmp_path, output)
    assert stats["missing_files"]
    assert stats["present_videos"] == 0
    assert "missing_files" in capsys.readouterr().out


def test_health_reports_missing_checkpoint_without_fake_model():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is False
