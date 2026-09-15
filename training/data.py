import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from training.config import TrainingConfig
from training.model import IMAGENET_MEAN, IMAGENET_STD


class FaceCropDataset(Dataset):
    def __init__(self, csv_path, split: str, config: TrainingConfig):
        manifest = pd.read_csv(csv_path)
        self.rows = manifest[manifest["split"] == split].reset_index(drop=True)
        self.transform = transforms.Compose([
            transforms.Resize((config.image_size, config.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows.iloc[index]
        image = Image.open(row["face_path"]).convert("RGB")
        return self.transform(image), torch.tensor(int(row["label"]), dtype=torch.long)
