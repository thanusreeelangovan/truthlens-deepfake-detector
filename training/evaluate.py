"""Evaluate a saved checkpoint without inventing metrics."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import confusion_matrix, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from torch.utils.data import DataLoader

from training.config import DEFAULT_CHECKPOINT, PROCESSED_ROOT, TrainingConfig
from training.data import FaceCropDataset
from training.model import load_checkpoint


def evaluate(manifest: Path, checkpoint: Path, split: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu"); config = TrainingConfig()
    dataset = FaceCropDataset(manifest, split, config); loader = DataLoader(dataset, config.batch_size, shuffle=False)
    model = load_checkpoint(checkpoint, device); labels = []; scores = []
    with torch.inference_mode():
        for images, target in loader:
            scores.extend(torch.softmax(model(images.to(device)), 1)[:, 1].cpu().tolist()); labels.extend(target.tolist())
    predicted = [int(value >= .5) for value in scores]
    result = {"split": split, "samples": len(labels), "accuracy": accuracy_score(labels, predicted), "precision": precision_score(labels, predicted, zero_division=0), "recall": recall_score(labels, predicted, zero_division=0), "f1": f1_score(labels, predicted, zero_division=0), "confusion_matrix": confusion_matrix(labels, predicted).tolist()}
    result["roc_auc"] = roc_auc_score(labels, scores) if len(set(labels)) == 2 else None
    result["false_positive_rate"] = result["confusion_matrix"][0][1] / max(1, sum(result["confusion_matrix"][0]))
    result["false_negative_rate"] = result["confusion_matrix"][1][0] / max(1, sum(result["confusion_matrix"][1]))
    print(json.dumps(result, indent=2)); return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, default=PROCESSED_ROOT / "faces/face_manifest.csv"); parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT); parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    args = parser.parse_args(); evaluate(args.manifest, args.checkpoint, args.split)
