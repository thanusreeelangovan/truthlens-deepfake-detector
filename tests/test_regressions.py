"""Regression tests for the real data and inference contracts."""
import csv
import io
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi import HTTPException, UploadFile

from backend.utils.aggregation import aggregate_probabilities
from backend.utils.video_processor import find_video_path, save_video
from scripts.create_splits import create_splits
from scripts.prepare_dfdc import build_manifest
from scripts.prepare_faceforensics import build_manifest as ff_manifest


def test_heuristic_does_not_return_fake_confidence():
    outcome = aggregate_probabilities([0.1, 0.8, 0.2])
    assert outcome["verdict"] == "INCONCLUSIVE"
    assert outcome["confidence"] is None
    assert outcome["confidence_calibrated"] is False


def test_missing_sample_positions_do_not_create_fake_temporal_sequence():
    outcome = aggregate_probabilities([0.9, 0.9, 0.9], frame_indices=[0, 2, 4])
    assert outcome["longest_suspicious_sequence"] == 1
    assert outcome["verdict"] == "INCONCLUSIVE"


def test_too_few_faces_is_inconclusive():
    assert aggregate_probabilities([])["verdict"] == "INCONCLUSIVE"
    assert aggregate_probabilities([0.1])["verdict"] == "INCONCLUSIVE"


def test_dfdc_manifest_has_unique_video_ids_and_linked_source_groups(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()
    for name in ("real.mp4", "fake.mp4"):
        (root / name).write_bytes(b"placeholder")
    (root / "metadata.json").write_text(json.dumps({
        "real.mp4": {"label": "REAL", "original": None},
        "fake.mp4": {"label": "FAKE", "original": "real.mp4"},
    }))
    output = tmp_path / "manifest.csv"
    build_manifest(root, output)
    rows = list(csv.DictReader(output.open()))
    assert len({row["video_id"] for row in rows}) == 2
    assert len({row["source_group"] for row in rows}) == 1
    create_splits(output, output)
    create_splits(output, output)  # rerunning must not duplicate split columns
    with output.open() as handle:
        assert handle.readline().count("split") == 1


def test_faceforensics_pairs_and_originals_share_source_group(tmp_path):
    root = tmp_path / "ff"
    original = root / "original_sequences" / "youtube" / "c23" / "videos"
    manipulated = root / "manipulated_sequences" / "Deepfakes" / "c23" / "videos"
    original.mkdir(parents=True)
    manipulated.mkdir(parents=True)
    for name in ("000.mp4", "003.mp4"):
        (original / name).write_bytes(b"file")
    (manipulated / "000_003.mp4").write_bytes(b"file")
    manifest = tmp_path / "ff.csv"
    ff_manifest(root, manifest)
    rows = list(csv.DictReader(manifest.open()))
    assert len({row["source_video_id"] for row in rows}) == 1
    assert len({row["video_id"] for row in rows}) == 3


def test_invalid_case_identifier_is_rejected():
    with pytest.raises(HTTPException) as exc:
        find_video_path("../../other-file")
    assert exc.value.status_code == 400


def test_oversized_upload_removed_before_decoding(tmp_path, monkeypatch):
    import backend.utils.video_processor as processor
    monkeypatch.setattr(processor, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(processor, "MAX_UPLOAD_BYTES", 1024)
    file = UploadFile(file=io.BytesIO(b"a" * 1500), filename="video.mp4")
    with pytest.raises(HTTPException) as exc:
        save_video(file)
    assert exc.value.status_code == 413
    assert not list(tmp_path.iterdir())


def test_extracted_crops_are_unique_per_video_with_shared_source(tmp_path, monkeypatch):
    import scripts.extract_faces as extractor

    class Capture:
        def __init__(self, path):
            self.position = 0
        def isOpened(self):
            return True
        def get(self, prop):
            return 1.0
        def read(self):
            self.position += 1
            return (True, np.zeros((100, 100, 3), dtype=np.uint8)) if self.position <= 3 else (False, None)
        def release(self):
            pass

    monkeypatch.setattr(extractor.cv2, "VideoCapture", Capture)
    monkeypatch.setattr(extractor, "make_detector", lambda: object())
    monkeypatch.setattr(extractor, "largest_face_crop", lambda frame, detector: frame)
    common = {"split": "train", "source_group": "shared", "numeric_label": "1"}
    first = extractor.extract_video({**common, "video_path": str(tmp_path / "a.mp4")}, tmp_path, extractor.TrainingConfig())
    second = extractor.extract_video({**common, "video_path": str(tmp_path / "b.mp4")}, tmp_path, extractor.TrainingConfig())
    assert first and second
    assert Path(first[0]["face_path"]).parent != Path(second[0]["face_path"]).parent
    assert first[0]["timestamp_seconds"] == 0.0
