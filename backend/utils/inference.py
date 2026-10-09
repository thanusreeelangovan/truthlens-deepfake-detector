import cv2
import os
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from training.model import IMAGENET_MEAN, IMAGENET_STD, load_checkpoint

DEFAULT_CHECKPOINT = Path(__file__).resolve().parents[2] / "models" / "truthlens_efficientnet_b0.pt"
MODEL_CHECKPOINT = os.getenv("TRUTHLENS_CHECKPOINT", str(DEFAULT_CHECKPOINT))
MODEL_NAME = "EfficientNet-B0 trained checkpoint; dataset not yet independently verified"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class InferenceEngine:
    def __init__(self, checkpoint: str = MODEL_CHECKPOINT):
        if not os.path.exists(checkpoint):
            raise RuntimeError(f"Trained checkpoint not found at '{checkpoint}'. Train the model before analysis.")
        try:
            self.model = load_checkpoint(checkpoint, DEVICE)
        except torch.cuda.OutOfMemoryError as exc:
            raise RuntimeError("Not enough GPU memory to load the trained detector.") from exc
        except Exception as exc:
            raise RuntimeError(f"Could not load trained checkpoint '{checkpoint}'.") from exc
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)), transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    def predict(self, face_crops: list[dict]) -> list[dict]:
        by_frame = {}
        for crop in face_crops:
            image = cv2.imread(crop["path"])
            if image is None:
                continue
            tensor = self.transform(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))).unsqueeze(0).to(DEVICE)
            try:
                with torch.inference_mode():
                    probability = torch.softmax(self.model(tensor), dim=1)[0, 1].item()
            except torch.cuda.OutOfMemoryError as exc:
                raise RuntimeError("GPU memory was exhausted during inference.") from exc
            by_frame.setdefault(crop["frame_index"], []).append(probability)
        timestamps = {crop["frame_index"]: crop.get("timestamp_seconds") for crop in face_crops}
        return [{"frame_index": index, "timestamp_seconds": timestamps.get(index), "fake_probability": round(sum(values) / len(values), 4)} for index, values in sorted(by_frame.items())]
