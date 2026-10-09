"""Basic frame-quality diagnostics, not forensic manipulation evidence.

Near-identical sequential frames do not give independent temporal evidence.
A static image encoded as a video must not trigger a deepfake verdict.
"""
from pathlib import Path

import cv2
import numpy as np

# A deliberately conservative screen for essentially unchanged image content.
NEAR_IDENTICAL_MAD_MAX = 0.004


def assess_frame_motion(frame_paths: list[str]) -> dict:
    previous = None
    differences = []
    for file_path in frame_paths:
        frame = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
        if frame is None:
            continue
        small = cv2.resize(frame, (96, 96), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        if previous is not None:
            differences.append(float(np.mean(np.abs(small - previous))))
        previous = small
    near_identical = sum(diff < NEAR_IDENTICAL_MAD_MAX for diff in differences)
    ratio = near_identical / len(differences) if differences else None
    return {
        "compared_pairs": len(differences),
        "near_identical_ratio": round(ratio, 4) if ratio is not None else None,
        "mean_absolute_frame_difference": round(float(np.mean(differences)), 5) if differences else None,
        "near_static_video": len(differences) >= 2 and ratio >= 0.8,
        "heuristic_not_forensic_evidence": True,
    }
