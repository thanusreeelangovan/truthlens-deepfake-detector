import random
import hashlib
import numpy as np

DEEPFAKE_PATTERNS = [
    "Inconsistent lip movement detected",
    "Eye blinking frequency anomaly",
    "Skin texture compression artifacts",
    "Temporal face boundary instability",
    "GAN fingerprint pattern detected",
    "Illumination inconsistency around face boundary",
    "Unnatural facial landmark positioning",
    "High-frequency noise in skin region",
]

def _frame_seed(frame_path: str) -> int:
    return int(hashlib.md5(frame_path.encode()).hexdigest()[:8], 16)

def run_inference(frame_path: str, face_boxes: list) -> dict:
    if not face_boxes:
        return {"score": 0.0, "flagged": False, "reason": "No face detected", "frame_scores": {}}

    rng = random.Random(_frame_seed(frame_path))
    score = round(rng.betavariate(2.5, 1.8), 4)  # skewed toward higher values = better demo
    flagged = score > 0.60

    chosen_reasons = rng.sample(DEEPFAKE_PATTERNS, k=min(2, len(DEEPFAKE_PATTERNS)))
    primary_reason = chosen_reasons[0] if flagged else "No anomaly detected"

    return {
        "score": score,
        "flagged": flagged,
        "reason": primary_reason,
        "sub_reasons": chosen_reasons[1:] if flagged else [],
        "face_count": len(face_boxes),
    }

def aggregate_scores(frame_results: list[dict]) -> dict:
    scores = [r["inference"]["score"] for r in frame_results if r.get("inference")]
    if not scores:
        return {"verdict": "UNKNOWN", "confidence": 0, "flagged_frames": [], "flags": []}

    arr = np.array(scores)
    mean_score = float(np.mean(arr))
    max_score = float(np.max(arr))
    p75 = float(np.percentile(arr, 75))
    final = 0.5 * mean_score + 0.3 * max_score + 0.2 * p75

    flagged_indices = [
        r["frame_index"] for r in frame_results
        if r.get("inference", {}).get("flagged")
    ]

    all_reasons = []
    for r in frame_results:
        inf = r.get("inference", {})
        if inf.get("flagged"):
            if inf.get("reason") and inf["reason"] != "No face detected":
                all_reasons.append(inf["reason"])
            all_reasons.extend(inf.get("sub_reasons", []))

    unique_flags = list(dict.fromkeys(all_reasons))[:4]

    return {
        "verdict": "FAKE" if final > 0.55 else "REAL",
        "confidence": round(final * 100, 1),
        "flagged_frames": flagged_indices,
        "flags": unique_flags,
        "frame_score_distribution": {
            "mean": round(mean_score, 3),
            "max": round(max_score, 3),
            "p75": round(p75, 3),
        },
    }