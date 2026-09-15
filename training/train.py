"""Train EfficientNet-B0 on face crops from a video-level split manifest."""
import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader

from training.config import DEFAULT_CHECKPOINT, PROCESSED_ROOT, TrainingConfig
from training.data import FaceCropDataset
from training.model import build_model


def seed_everything(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def evaluate(model, loader, device):
    model.eval(); losses = []; labels = []; scores = []
    criterion = nn.CrossEntropyLoss()
    with torch.inference_mode():
        for images, target in loader:
            logits = model(images.to(device)); target = target.to(device)
            losses.append(criterion(logits, target).item()); labels.extend(target.cpu().tolist())
            scores.extend(torch.softmax(logits, 1)[:, 1].cpu().tolist())
    predicted = [int(score >= 0.5) for score in scores]
    metrics = {"loss": float(np.mean(losses)), "accuracy": accuracy_score(labels, predicted), "precision": precision_score(labels, predicted, zero_division=0), "recall": recall_score(labels, predicted, zero_division=0), "f1": f1_score(labels, predicted, zero_division=0)}
    metrics["roc_auc"] = roc_auc_score(labels, scores) if len(set(labels)) == 2 else None
    return metrics


def train(manifest: Path, checkpoint: Path, config: TrainingConfig):
    seed_everything(config.seed); device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_set = FaceCropDataset(manifest, "train", config); validation_set = FaceCropDataset(manifest, "validation", config)
    if not len(train_set) or not len(validation_set): raise ValueError("Train and validation splits must contain face crops.")
    train_loader = DataLoader(train_set, config.batch_size, shuffle=True, num_workers=config.num_workers, pin_memory=device.type == "cuda")
    validation_loader = DataLoader(validation_set, config.batch_size, shuffle=False, num_workers=config.num_workers)
    model = build_model(True).to(device); optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=1, factor=0.3)
    class_counts = np.bincount([int(row["numeric_label"] if "numeric_label" in row else row["label"]) for row in train_set.rows.to_dict("records")], minlength=2)
    weights = torch.tensor(len(train_set) / (2 * np.maximum(class_counts, 1)), dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=weights); scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    best_f1 = -1; stale = 0; history = []
    for epoch in range(1, config.epochs + 1):
        model.train(); losses = []
        for images, target in train_loader:
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                loss = criterion(model(images.to(device)), target.to(device))
            scaler.scale(loss).backward(); scaler.step(optimizer); scaler.update(); losses.append(loss.item())
        metrics = evaluate(model, validation_loader, device); metrics.update(epoch=epoch, train_loss=float(np.mean(losses)), validation_loss=metrics.pop("loss"))
        history.append(metrics); print(json.dumps(metrics)); scheduler.step(metrics["validation_loss"])
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]; stale = 0; checkpoint.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"model_state": model.state_dict(), "config": config.__dict__, "validation_metrics": metrics}, checkpoint)
        else: stale += 1
        if stale >= config.patience: break
    checkpoint.with_suffix(".history.json").write_text(json.dumps(history, indent=2))
    print(f"Best checkpoint: {checkpoint} (validation F1={best_f1:.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, default=PROCESSED_ROOT / "dfdc/faces/face_manifest.csv"); parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args(); train(args.manifest, args.checkpoint, TrainingConfig())
