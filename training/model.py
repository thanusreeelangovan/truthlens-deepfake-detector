import torch
from torch import nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def build_model(pretrained: bool = True) -> nn.Module:
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    return model


def load_checkpoint(path, device: torch.device) -> nn.Module:
    model = build_model(pretrained=False)
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"] if "model_state" in checkpoint else checkpoint)
    model.to(device).eval()
    return model
