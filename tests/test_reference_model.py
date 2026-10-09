"""Reference mode stays opt-in and never pretends an ImageNet model is a detector."""
from io import BytesIO
from pathlib import Path

import pytest

from backend.utils.reference_model import download_reference_checkpoint, reference_enabled


def test_reference_model_is_opt_in(monkeypatch):
    monkeypatch.delenv("TRUTHLENS_REFERENCE_DEMO", raising=False)
    assert not reference_enabled()
    monkeypatch.setenv("TRUTHLENS_REFERENCE_DEMO", "1")
    assert reference_enabled()


def test_bounded_download_is_atomic(tmp_path, monkeypatch):
    import backend.utils.reference_model as reference

    class FakeResponse(BytesIO):
        headers = {"Content-Length": "1200000"}

    monkeypatch.setattr(reference, "urlopen", lambda url, timeout: FakeResponse(b"a" * 1200000))
    dest = tmp_path / "weights.pth"
    assert download_reference_checkpoint(dest) == dest
    assert dest.stat().st_size == 1200000
    assert not (tmp_path / "weights.downloading").exists()


def test_download_rejects_oversized_payload(tmp_path, monkeypatch):
    import backend.utils.reference_model as reference

    class FakeResponse(BytesIO):
        headers = {}

    monkeypatch.setattr(reference, "MAX_CHECKPOINT_BYTES", 1100000)
    monkeypatch.setattr(reference, "urlopen", lambda url, timeout: FakeResponse(b"a" * 1200000))
    dest = tmp_path / "weights.pth"
    with pytest.raises(RuntimeError):
        download_reference_checkpoint(dest)
    assert not dest.exists()
    assert not (tmp_path / "weights.downloading").exists()
