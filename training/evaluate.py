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
from backend.utils.aggregation import aggregate_probabilities


def evaluate(manifest: Path, checkpoint: Path, split: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu"); config = TrainingConfig()
    dataset = FaceCropDataset(manifest, split, config); loader = DataLoader(dataset, config.batch_size, shuffle=False)
    model = load_checkpoint(checkpoint, device); labels = []; scores = []
    with torch.inference_mode():
        for images, target in loader:
            scores.extend(torch.softmax(model(images.to(device)), 1)[:, 1].cpu().tolist()); labels.extend(target.tolist())
    predicted = [int(value >= .5) for value in scores]
    result = {"split": split, "level": "frame", "samples": len(labels), "accuracy": accuracy_score(labels, predicted), "precision": precision_score(labels, predicted, zero_division=0), "recall": recall_score(labels, predicted, zero_division=0), "f1": f1_score(labels, predicted, zero_division=0), "confusion_matrix": confusion_matrix(labels, predicted).tolist()}
    result["roc_auc"] = roc_auc_score(labels, scores) if len(set(labels)) == 2 else None
    result["false_positive_rate"] = result["confusion_matrix"][0][1] / max(1, sum(result["confusion_matrix"][0]))
    result["false_negative_rate"] = result["confusion_matrix"][1][0] / max(1, sum(result["confusion_matrix"][1]))
    video_scores = {}
    video_labels = {}
    for row, score in zip(dataset.rows.to_dict("records"), scores):
        video_id = row.get("video_path") or row.get("source_video_id")
        video_scores.setdefault(video_id, []).append(score)
        label = row.get("numeric_label", row.get("label"))
        video_labels[video_id] = int(label) if str(label).isdigit() else int(str(label).upper() == "FAKE")
    video_predictions = [int(aggregate_probabilities(values)["verdict"] == "LIKELY_MANIPULATED") for values in video_scores.values()]
    video_truth = [video_labels[video_id] for video_id in video_scores]
    video_matrix = confusion_matrix(video_truth, video_predictions, labels=[0, 1]).tolist()
    result["video_level"] = {
        "videos": len(video_truth), "accuracy": accuracy_score(video_truth, video_predictions),
        "precision": precision_score(video_truth, video_predictions, zero_division=0),
        "recall": recall_score(video_truth, video_predictions, zero_division=0),
        "f1": f1_score(video_truth, video_predictions, zero_division=0),
        "confusion_matrix": video_matrix,
        "false_positive_rate": video_matrix[0][1] / max(1, sum(video_matrix[0])),
        "false_negative_rate": video_matrix[1][0] / max(1, sum(video_matrix[1])),
    }
    print(json.dumps(result, indent=2)); return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, default=PROCESSED_ROOT / "dfdc/faces/face_manifest.csv"); parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT); parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    args = parser.parse_args(); evaluate(args.manifest, args.checkpoint, args.split)
