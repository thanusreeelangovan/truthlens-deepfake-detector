"""Reproducibility and abstention-safe evaluation regression tests."""
import csv
import json
from pathlib import Path

import pytest

from scripts.build_eval_manifest import build_eval_manifest
from scripts.evaluate_live_videos import read_manifest, summarize


def _record(label, score, verdict="INCONCLUSIVE", static=False):
    return {
        "status": "complete", "label": label, "raw_mean_score": score,
        "verdict": verdict, "frames_analyzed": 6, "near_static_video": static,
    }


def test_all_abstentions_have_undefined_accuracy_not_fake_zero():
    report = summarize([
        _record("REAL", 0.95),
        _record("FAKE", 0.30),
    ])
    assert report["decided_videos"] == 0
    assert report["abstentions"] == 2
    assert report["coverage"] == 0
    assert report["accuracy_on_decided_videos"] is None
    assert report["exploratory_raw_mean_score"]["roc_auc"] == 0.0
    assert report["exploratory_raw_mean_score"]["candidate_thresholds_NOT_CALIBRATED"]["0.65"]["false_alarm_rate_on_real"] == 1.0


def test_fixed_threshold_research_rates_not_confused_with_decisions():
    r = summarize([
        _record("REAL", 0.20, verdict="LIKELY_AUTHENTIC"),
        _record("REAL", 0.70, verdict="INCONCLUSIVE"),
        _record("FAKE", 0.90, verdict="LIKELY_MANIPULATED"),
        _record("FAKE", 0.50, verdict="INCONCLUSIVE"),
    ])
    assert r["decided_videos"] == 2
    assert r["accuracy_on_decided_videos"] == 1.0
    assert r["coverage"] == 0.5
    assert r["exploratory_raw_mean_score"]["candidate_thresholds_NOT_CALIBRATED"]["0.65"]["real_count"] == 2
    assert r["exploratory_raw_mean_score"]["candidate_thresholds_NOT_CALIBRATED"]["0.65"]["false_alarm_rate_on_real"] == 0.5


def test_static_frames_excluded_from_score_auc_but_count_toward_abstention():
    r = summarize([
        _record("REAL", 0.99, static=True),
        _record("FAKE", 0.80),
    ])
    assert r["abstentions"] == 2
    assert r["exploratory_raw_mean_score"]["eligible_videos"] == 1
    assert r["exploratory_raw_mean_score"]["roc_auc"] is None


def test_missing_or_invalid_manifest_fails_fast(tmp_path):
    path = tmp_path / "videos.csv"
    path.write_text("video_path,label\nnot-present.mp4,REAL\n")
    with pytest.raises(FileNotFoundError):
        read_manifest(path)
    path.write_text("video_path,label\nnot-present.mp4,MADEUP\n")
    with pytest.raises(ValueError, match="Unknown label"):
        read_manifest(path)


def test_build_dfdc_paired_manifest_matches_true_labels(tmp_path):
    root = tmp_path / "train_sample_videos"
    root.mkdir()
    metadata = {}
    for i in range(4):
        real = f"real{i}.mp4"
        fake = f"fake{i}.mp4"
        (root / real).write_bytes(b"real bytes")
        (root / fake).write_bytes(b"fake bytes")
        metadata[real] = {"label": "REAL", "original": None}
        metadata[fake] = {"label": "FAKE", "original": real}
    (root / "metadata.json").write_text(json.dumps(metadata))
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    rows = build_eval_manifest(root, first, pairs=3, seed=7)
    build_eval_manifest(root, second, pairs=3, seed=7)
    assert first.read_text() == second.read_text()
    assert len(rows) == 6
    assert sum(r["label"] == "REAL" for r in rows) == 3
    groups = {r["source_group"] for r in rows}
    assert len(groups) == 3
    for group in groups:
        assert {r["label"] for r in rows if r["source_group"] == group} == {"REAL", "FAKE"}
    assert len(read_manifest(first)) == 6


def test_pair_builder_rejects_only_unpaired_videos(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "real.mp4").write_bytes(b"video")
    (root / "metadata.json").write_text(json.dumps({"real.mp4":{"label":"REAL","original":None}}))
    with pytest.raises(ValueError, match="No matched"):
        build_eval_manifest(root, tmp_path / "result.csv")
