"""Evaluate a real checkpoint with frame metrics and explicit video abstentions."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader

from training.config import DEFAULT_CHECKPOINT, PROCESSED_ROOT, TrainingConfig
from training.data import FaceCropDataset
from training.model import load_checkpoint
from backend.utils.aggregation import aggregate_probabilities


def binary_metrics(labels, predictions, scores=None):
    labels, predictions = list(labels), list(predictions)
    if not labels:
        return {"samples": 0, "accuracy": None, "precision": None, "recall": None, "f1": None,
                "confusion_matrix": [[0, 0], [0, 0]], "false_positive_rate": None, "false_negative_rate": None,
                "roc_auc": None}
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    result = {
        "samples": len(labels),
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "false_positive_rate": float(matrix[0, 1] / max(1, matrix[0].sum())),
        "false_negative_rate": float(matrix[1, 0] / max(1, matrix[1].sum())),
        "roc_auc": float(roc_auc_score(labels, scores)) if scores is not None and len(set(labels)) == 2 else None,
    }
    return result


def evaluate(manifest: Path, checkpoint: Path, split: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = TrainingConfig()
    dataset = FaceCropDataset(manifest, split, config)
    if not len(dataset):
        raise ValueError(f"No face crops available in the {split} split.")
    loader = DataLoader(dataset, config.batch_size, shuffle=False)
    model = load_checkpoint(checkpoint, device)
    labels, scores = [], []
    with torch.inference_mode():
        for images, target in loader:
            scores.extend(torch.softmax(model(images.to(device)), 1)[:, 1].cpu().tolist())
            labels.extend(target.tolist())

    result = {
        "split": split,
        "level": "frame",
        **binary_metrics(labels, [int(v >= 0.5) for v in scores], scores),
    }

    by_video = defaultdict(list)
    video_labels = {}
    for row, score in zip(dataset.rows.to_dict("records"), scores):
        video_id = str(row.get("video_id") or row.get("video_path") or row.get("source_video_id"))
        frame_index = int(row.get("frame_index", len(by_video[video_id])))
        by_video[video_id].append((frame_index, float(score)))
        label = row.get("numeric_label", row.get("label"))
        numeric_label = int(label) if str(label).isdigit() else int(str(label).upper() == "FAKE")
        if video_id in video_labels and video_labels[video_id] != numeric_label:
            raise ValueError(f"Conflicting labels for video {video_id}.")
        video_labels[video_id] = numeric_label

    decided_truth, decided_predictions = [], []
    outcomes = []
    for video_id, samples in sorted(by_video.items()):
        ordered = sorted(samples)
        aggregated = aggregate_probabilities(
            [score for _, score in ordered], frame_indices=[index for index, _ in ordered]
        )
        verdict = aggregated["verdict"]
        outcomes.append({"video_id": video_id, "ground_truth": video_labels[video_id], "verdict": verdict})
        if verdict == "INCONCLUSIVE":
            continue
        decided_truth.append(video_labels[video_id])
        decided_predictions.append(int(verdict == "LIKELY_MANIPULATED"))

    video_total = len(outcomes)
    abstentions = video_total - len(decided_truth)
    result["video_level"] = {
        "videos": video_total,
        "decided_videos": len(decided_truth),
        "abstentions": abstentions,
        "coverage": len(decided_truth) / video_total if video_total else 0.0,
        "abstention_rate": abstentions / video_total if video_total else 0.0,
        "metrics_on_decided_videos": binary_metrics(decided_truth, decided_predictions),
        "outcomes": outcomes,
        "warning": "Abstentions excluded from decided-video metrics; evaluate coverage alongside accuracy.",
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=PROCESSED_ROOT / "dfdc/faces/face_manifest.csv")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    args = parser.parse_args()
    evaluate(args.manifest, args.checkpoint, args.split)
