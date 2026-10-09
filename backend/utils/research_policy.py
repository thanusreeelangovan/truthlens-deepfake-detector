"""Guardrails for unvalidated third-party model predictions.

The research model has known false positives on non-deepfake imagery and
has no measured operating point on TruthLens's target video distribution.
Instead of guessing a new threshold, show raw signals and abstain from
authenticity claims until the model is independently validated.
"""


def apply_result_policy(raw_verdict: str, *, reference: bool, frame_quality: dict) -> dict:
    if raw_verdict not in {"LIKELY_AUTHENTIC", "INCONCLUSIVE", "LIKELY_MANIPULATED"}:
        raise ValueError("Unexpected model decision.")
    if frame_quality.get("near_static_video"):
        return {
            "verdict": "INCONCLUSIVE",
            "reason_code": "NEAR_STATIC_VIDEO",
            "reason": "Almost identical frames do not provide enough independent temporal evidence.",
            "screening_signal": "INSUFFICIENT_TEMPORAL_EVIDENCE",
            "research_evaluation_required": bool(reference),
        }
    if reference:
        signal = {
            "LIKELY_AUTHENTIC": "LOW_MODEL_SIGNAL",
            "LIKELY_MANIPULATED": "ELEVATED_MODEL_SIGNAL",
            "INCONCLUSIVE": "MIXED_MODEL_SIGNAL",
        }[raw_verdict]
        return {
            "verdict": "INCONCLUSIVE",
            "reason_code": "REFERENCE_MODEL_UNVALIDATED",
            "reason": "The third-party model has demonstrated false positives and has not been validated for general uploaded videos. The score is a screening signal, not a deepfake verdict.",
            "screening_signal": signal,
            "research_evaluation_required": True,
        }
    return {
        "verdict": raw_verdict,
        "reason_code": None,
        "reason": None,
        "screening_signal": None,
        "research_evaluation_required": False,
    }
