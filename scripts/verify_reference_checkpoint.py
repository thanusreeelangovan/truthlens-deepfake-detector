"""Explicit integration test for third-party academic baseline.

This is not evidence of detection accuracy. It checks binary compatibility and
the ability to run a real neural-network forward pass, not image classification.
"""
from backend.utils.reference_model import download_reference_checkpoint
from backend.utils.inference import InferenceEngine
import torch


if __name__ == "__main__":
    checkpoint = download_reference_checkpoint()
    engine = InferenceEngine(str(checkpoint), reference=True)
    with torch.inference_mode():
        result = engine.model(torch.zeros(1, 3, 224, 224))
    assert tuple(result.shape) == (1, 2), result.shape
    print("Research model downloaded, loaded with weights_only=True, and produced 2 logits.")
