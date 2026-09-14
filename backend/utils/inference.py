import os
from collections import defaultdict


MODEL_ID = os.getenv("TRUTHLENS_MODEL_ID", "dima806/deepfake_vs_real_image_detection")


def _load_model():
	try:
		from transformers import pipeline
		return pipeline("image-classification", model=MODEL_ID)
	except Exception as exc:
		raise RuntimeError(
			f"Could not load pretrained model '{MODEL_ID}'. Download it once with network access or set TRUTHLENS_MODEL_ID."
		) from exc


def _fake_probability(predictions: list[dict]) -> float:
	fake = next((item["score"] for item in predictions if "fake" in item["label"].lower()), None)
	real = next((item["score"] for item in predictions if "real" in item["label"].lower()), None)
	if fake is None or real is None:
		raise RuntimeError("The model output must contain both real and fake labels.")
	return round(float(fake / (fake + real)), 4)


def infer_faces(face_crops: list[dict]) -> dict:
	"""Run image-level inference and aggregate face scores per sampled frame.

	The model processor handles resize and normalization to the model's expected
	input. Probability is the model's relative likelihood that a crop is fake.
	"""
	if not face_crops:
		return {"frame_probabilities": [], "model": MODEL_ID}

	model = _load_model()
	by_frame = defaultdict(list)
	for crop in face_crops:
		try:
			predictions = model(crop["path"])
			by_frame[crop["frame_index"]].append(_fake_probability(predictions))
		except RuntimeError:
			raise
		except Exception as exc:
			raise RuntimeError(f"Inference failed for frame {crop['frame_index']}.") from exc

	probabilities = [
		{"frame_index": frame_index, "fake_probability": round(sum(scores) / len(scores), 4)}
		for frame_index, scores in sorted(by_frame.items())
	]
	return {"frame_probabilities": probabilities, "model": MODEL_ID}
