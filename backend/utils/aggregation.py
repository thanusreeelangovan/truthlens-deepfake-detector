"""Explicitly heuristic temporal aggregation; no claims of calibrated certainty."""
import math
from statistics import median, mean, pvariance

from training.config import (
    AUTHENTIC_MEDIAN_THRESHOLD,
    AUTHENTIC_RATIO_MAX,
    MANIPULATED_RATIO_MIN,
    MANIPULATED_SEQUENCE_MIN,
    SUSPICIOUS_FRAME_THRESHOLD,
)

MIN_ANALYZED_FRAMES = 3


def longest_consecutive(indices: list[int]) -> int:
    longest = current = 0
    previous = None
    for index in sorted(indices):
        current = current + 1 if previous is not None and index == previous + 1 else 1
        longest = max(longest, current)
        previous = index
    return longest


def aggregate_probabilities(probabilities: list[float], threshold: float = SUSPICIOUS_FRAME_THRESHOLD, frame_indices=None) -> dict:
    """Use original sample positions to avoid joining detections across missing faces."""
    values = [float(v) for v in probabilities]
    if any(not math.isfinite(v) or v < 0 or v > 1 for v in values):
        raise ValueError("All model scores must be finite probabilities between zero and one.")
    positions = list(range(len(values))) if frame_indices is None else list(frame_indices)
    if len(values) != len(positions) or len(set(positions)) != len(positions):
        raise ValueError("Frame indices must be unique and match the number of probabilities.")
    if positions != sorted(positions):
        raise ValueError("Frame indices must be in chronological order.")
    suspicious = [position for position, value in zip(positions, values) if value >= threshold]
    ratio = len(suspicious) / len(values) if values else 0.0
    average = mean(values) if values else 0.0
    midpoint = median(values) if values else 0.0
    longest = longest_consecutive(suspicious)
    if len(values) < MIN_ANALYZED_FRAMES:
        verdict = "INCONCLUSIVE"
    elif ratio <= AUTHENTIC_RATIO_MAX and midpoint <= AUTHENTIC_MEDIAN_THRESHOLD:
        verdict = "LIKELY_AUTHENTIC"
    elif ratio >= MANIPULATED_RATIO_MIN and longest >= MANIPULATED_SEQUENCE_MIN:
        verdict = "LIKELY_MANIPULATED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "confidence": None,
        "confidence_calibrated": False,
        "decision_policy": "heuristic_temporal_v1",
        "suspicious_frame_count": len(suspicious),
        "suspicious_ratio": round(ratio, 4),
        "mean_probability": round(average, 4),
        "median_probability": round(midpoint, 4),
        "probability_variance": round(pvariance(values), 4) if len(values) > 1 else 0.0,
        "longest_suspicious_sequence": longest,
    }
