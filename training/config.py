from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingConfig:
    image_size: int = 224
    batch_size: int = 32
    epochs: int = 15
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    patience: int = 4
    seed: int = 42
    num_workers: int = 2
    frame_interval_seconds: float = 1.0


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw" / "FaceForensics++"
PROCESSED_ROOT = DATA_ROOT / "processed"
MODEL_ROOT = PROJECT_ROOT / "models"
DEFAULT_MANIFEST = PROCESSED_ROOT / "manifest.csv"
DEFAULT_SPLITS = PROCESSED_ROOT / "splits.csv"
DEFAULT_CHECKPOINT = MODEL_ROOT / "truthlens_efficientnet_b0.pt"
SUSPICIOUS_FRAME_THRESHOLD = 0.65
AUTHENTIC_MEDIAN_THRESHOLD = 0.30
AUTHENTIC_RATIO_MAX = 0.15
MANIPULATED_RATIO_MIN = 0.45
MANIPULATED_SEQUENCE_MIN = 3
