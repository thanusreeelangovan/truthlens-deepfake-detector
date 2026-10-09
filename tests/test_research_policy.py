"""Reference model must not turn unsupported scores into fake video claims."""
import cv2
import numpy as np

from backend.utils.quality import assess_frame_motion
from backend.utils.research_policy import apply_result_policy


def test_reference_model_abstains_on_high_scores_with_real_video_motion():
    motion = {"near_static_video": False}
    result = apply_result_policy("LIKELY_MANIPULATED", reference=True, frame_quality=motion)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["screening_signal"] == "ELEVATED_MODEL_SIGNAL"
    assert result["reason_code"] == "REFERENCE_MODEL_UNVALIDATED"


def test_reference_model_abstains_on_low_scores_too():
    result = apply_result_policy("LIKELY_AUTHENTIC", reference=True, frame_quality={"near_static_video": False})
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["screening_signal"] == "LOW_MODEL_SIGNAL"


def test_static_input_gets_insufficient_evidence_even_with_trained_checkpoint():
    result = apply_result_policy("LIKELY_MANIPULATED", reference=False, frame_quality={"near_static_video": True})
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["reason_code"] == "NEAR_STATIC_VIDEO"


def test_local_model_normal_policy_not_broken():
    result = apply_result_policy("LIKELY_MANIPULATED", reference=False, frame_quality={"near_static_video": False})
    assert result["verdict"] == "LIKELY_MANIPULATED"


def test_nearly_identical_frames_are_static(tmp_path):
    paths = []
    for i in range(6):
        path = tmp_path / f"frame{i}.jpg"
        cv2.imwrite(str(path), np.full((64, 64, 3), 90, dtype=np.uint8))
        paths.append(str(path))
    quality = assess_frame_motion(paths)
    assert quality["near_static_video"] is True
    assert quality["compared_pairs"] == 5


def test_distinct_frames_are_not_static(tmp_path):
    paths = []
    for i in range(6):
        path = tmp_path / f"frame{i}.jpg"
        cv2.imwrite(str(path), np.full((64, 64, 3), i * 35, dtype=np.uint8))
        paths.append(str(path))
    quality = assess_frame_motion(paths)
    assert quality["near_static_video"] is False
