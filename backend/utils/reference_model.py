"""Opt-in educational research checkpoint loader.

The external FF++ C23 checkpoint was trained by Himanshu Kashyap (Xicor9),
NOT by the TruthLens project. See its Hugging Face model card and license.
Never claim its third-party benchmark scores as TruthLens evaluation results.
"""
import os
from pathlib import Path
from urllib.request import urlopen

SOURCE_NAME = "Xicor9/efficientnet-b0-ffpp-c23"
SOURCE_URL = "https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23"
CHECKPOINT_URL = SOURCE_URL + "/resolve/main/efficientnet_b0_ffpp_c23.pth"
CHECKPOINT_PATH = Path(__file__).resolve().parents[2] / "model-cache" / "ffpp_c23_reference.pth"
MAX_CHECKPOINT_BYTES = 40 * 1024 * 1024


def reference_enabled():
    return os.getenv("TRUTHLENS_REFERENCE_DEMO", "").strip().lower() in {"1", "true", "yes"}


def download_reference_checkpoint(destination: Path = CHECKPOINT_PATH):
    """Download only the specified external model; atomically persist bounded bytes."""
    destination = Path(destination)
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".downloading")
    size = 0
    try:
        with urlopen(CHECKPOINT_URL, timeout=90) as response, temporary.open("wb") as output:
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_CHECKPOINT_BYTES:
                raise RuntimeError("External checkpoint exceeds download limit.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_CHECKPOINT_BYTES:
                    raise RuntimeError("External checkpoint exceeds download limit.")
                output.write(chunk)
        if size < 1_000_000:
            raise RuntimeError("External model weights were not downloaded completely.")
        temporary.replace(destination)
        return destination
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
