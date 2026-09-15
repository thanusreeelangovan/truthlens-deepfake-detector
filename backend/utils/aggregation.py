from statistics import median, mean, pvariance

from training.config import (
    AUTHENTIC_MEDIAN_THRESHOLD,
    AUTHENTIC_RATIO_MAX,
    MANIPULATED_RATIO_MIN,
    MANIPULATED_SEQUENCE_MIN,
    SUSPICIOUS_FRAME_THRESHOLD,
)


def longest_consecutive(indices: list[int]) -> int:
    longest = current = 0
    previous = None
    for index in sorted(indices):
        current = current + 1 if previous is not None and index == previous + 1 else 1
        longest = max(longest, current)
        previous = index
    return longest


def aggregate_probabilities(probabilities: list[float], threshold: float = SUSPICIOUS_FRAME_THRESHOLD) -> dict:
    if not probabilities:
        return {
                    "verdict": "INCONCLUSIVE", "confidence": 0.0, "suspicious_frame_count": 0,
            "suspicious_ratio": 0.0, "mean_probability": 0.0, "median_probability": 0.0,
            "probability_variance": 0.0, "longest_suspicious_sequence": 0,
        }
    suspicious_indices = [index for index, value in enumerate(probabilities) if value >= threshold]
    suspicious_ratio = len(suspicious_indices) / len(probabilities)
    mean_probability = mean(probabilities)
    median_probability = median(probabilities)
    longest_sequence = longest_consecutive(suspicious_indices)
    if suspicious_ratio <= AUTHENTIC_RATIO_MAX and median_probability <= AUTHENTIC_MEDIAN_THRESHOLD:
        verdict = "LIKELY_AUTHENTIC"
        confidence = (1 - median_probability) * 100
    elif suspicious_ratio >= MANIPULATED_RATIO_MIN and longest_sequence >= MANIPULATED_SEQUENCE_MIN:
        verdict = "LIKELY_MANIPULATED"
        confidence = min(100.0, suspicious_ratio * 100)
    else:
        verdict = "INCONCLUSIVE"
        confidence = max(0.0, 100 - abs(suspicious_ratio - 0.3) * 100)
    return {
        "verdict": verdict, "confidence": round(confidence, 2),
        "suspicious_frame_count": len(suspicious_indices), "suspicious_ratio": round(suspicious_ratio, 4),
        "mean_probability": round(mean_probability, 4), "median_probability": round(median_probability, 4),
        "probability_variance": round(pvariance(probabilities), 4) if len(probabilities) > 1 else 0.0,
        "longest_suspicious_sequence": longest_sequence,
    }
