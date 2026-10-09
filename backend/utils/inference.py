"""Batched, checkpoint-backed inference on consistently preprocessed face crops."""
import os
from pathlib import Path

import cv2
import torch
from PIL import Image
from torchvision import transforms

from training.model import IMAGENET_MEAN, IMAGENET_STD, load_checkpoint

DEFAULT_CHECKPOINT = Path(__file__).resolve().parents[2] / "models" / "truthlens_efficientnet_b0.pt"
MODEL_CHECKPOINT = os.getenv("TRUTHLENS_CHECKPOINT", str(DEFAULT_CHECKPOINT))
MODEL_NAME = "EfficientNet-B0 (checkpoint-trained video face classifier)"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
INFERENCE_BATCH_SIZE = max(1, int(os.getenv("TRUTHLENS_BATCH_SIZE", "8")))


class InferenceEngine:
    def __init__(self, checkpoint: str = MODEL_CHECKPOINT):
        if not os.path.exists(checkpoint):
            raise RuntimeError(f"Trained checkpoint not found at '{checkpoint}'.")
        try:
            self.model = load_checkpoint(checkpoint, DEVICE)
        except torch.cuda.OutOfMemoryError as exc:
            raise RuntimeError("Insufficient GPU memory to load the model.") from exc
        except Exception as exc:
            raise RuntimeError(f"Could not load trained checkpoint '{checkpoint}'.") from exc
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    def predict(self, face_crops: list[dict]) -> list[dict]:
        output = []
        tensors, metadata = [], []

        def flush_batch():
            if not tensors:
                return
            batch = torch.stack(tensors).to(DEVICE)
            try:
                with torch.inference_mode():
                    probabilities = torch.softmax(self.model(batch), dim=1)[:, 1].cpu().tolist()
            except torch.cuda.OutOfMemoryError as exc:
                raise RuntimeError("GPU memory exhausted during inference.") from exc
            for crop, score in zip(metadata, probabilities):
                output.append({
                    "frame_index": crop["frame_index"],
                    "timestamp_seconds": crop.get("timestamp_seconds"),
                    "fake_probability": round(float(score), 4),
                })
            tensors.clear()
            metadata.clear()

        for crop in face_crops:
            image = cv2.imread(crop["path"])
            if image is None:
                continue
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            tensors.append(self.transform(Image.fromarray(rgb)))
            metadata.append(crop)
            if len(tensors) >= INFERENCE_BATCH_SIZE:
                flush_batch()
        flush_batch()
        return sorted(output, key=lambda item: item["frame_index"])
