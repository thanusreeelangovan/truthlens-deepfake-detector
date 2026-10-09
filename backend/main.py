"""
TruthLens AI — Backend Entry Point
Path: backend/main.py
"""

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.utils.video_processor import save_video, extract_frames, find_video_path, FRAMES_DIR, MAX_FILE_SIZE_MB, MAX_DURATION_SECONDS
from backend.utils.face_detector import detect_faces
from backend.utils.inference import InferenceEngine, MODEL_CHECKPOINT, MODEL_NAME
from backend.utils.aggregation import aggregate_probabilities
from backend.utils.reference_model import download_reference_checkpoint, reference_enabled, SOURCE_URL

inference_engine = None
model_error = None

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("TRUTHLENS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ready" if inference_engine is not None else "model_unavailable",
            "engine": "TruthLens AI", "version": "0.6.0",
            "model_loaded": inference_engine is not None,
            "model_source": inference_engine.model_source if inference_engine else None,
            "reference_research_model": bool(inference_engine and inference_engine.reference),
            "model_error": model_error or (None if inference_engine is not None else "Trained checkpoint not installed.")}


@app.on_event("startup")
async def load_detector():
    global inference_engine, model_error
    inference_engine, model_error = None, None
    try:
        if os.path.exists(MODEL_CHECKPOINT):
            inference_engine = InferenceEngine(MODEL_CHECKPOINT)
        elif reference_enabled():
            # Opt-in research baseline; not the user's own trained model.
            checkpoint = download_reference_checkpoint()
            inference_engine = InferenceEngine(str(checkpoint), reference=True)
        else:
            model_error = "No trained checkpoint configured. Reference demo is disabled."
    except Exception as exc:
        # Health remains available even when the model or download fails.
        model_error = f"Model unavailable: {type(exc).__name__}: {exc}"
        inference_engine = None


@app.get("/api/model/info")
def model_info():
    return {
        "name": inference_engine.model_name if inference_engine else MODEL_NAME,
        "model_loaded": inference_engine is not None,
        "model_source": inference_engine.model_source if inference_engine else None,
        "reference_research_model": bool(inference_engine and inference_engine.reference),
        "reference_model_card": SOURCE_URL if inference_engine and inference_engine.reference else None,
        "calibrated_probabilities": False,
        "decision_policy": "heuristic_temporal_v1",
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_duration_seconds": MAX_DURATION_SECONDS,
    }


@app.post("/api/upload")
def upload_video(file: UploadFile = File(...)):
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Trained model unavailable. Upload disabled.")
    result = save_video(file)
    return {
        "status": "received",
        "case_id": result["case_id"],
        "filename": result["filename"],
        "size_mb": result["size_mb"],
        "next_stage": "frame_extraction",
    }


@app.post("/api/analyze/{case_id}")
def analyze_case(case_id: str):
    # Reject unsafe identifiers BEFORE touching a filesystem path or entering cleanup.
    try:
        if str(uuid.UUID(case_id)) != case_id:
            raise ValueError("Case ID is not canonical.")
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid case ID.") from None
    case_frame_dir = os.path.join(FRAMES_DIR, case_id)
    try:
        if inference_engine is None:
            raise HTTPException(status_code=503, detail=model_error or f"Trained checkpoint not found at '{MODEL_CHECKPOINT}'.")
        started = time.perf_counter()
        extraction = extract_frames(case_id)
        faces = detect_faces(extraction["frame_paths"], case_frame_dir, extraction["frame_timestamps"])
        frame_probabilities = inference_engine.predict(faces["face_crops"])
        values = [item["fake_probability"] for item in frame_probabilities]
        aggregate = aggregate_probabilities(values, frame_indices=[item["frame_index"] for item in frame_probabilities])
        signals = []
        if aggregate["suspicious_frame_count"]:
            signals.append(f"{aggregate['suspicious_frame_count']} of {len(values)} analyzed frames showed elevated manipulation probability.")
        if aggregate["longest_suspicious_sequence"]:
            signals.append(f"Manipulation probability remained elevated across {aggregate['longest_suspicious_sequence']} consecutive frames.")
        if not values:
            signals.append("No usable face found. Authenticity cannot be assessed.")
        elif len(values) < 3:
            signals.append("Too few analyzable frames for a meaningful verdict.")
        elif not signals:
            signals.append("No sustained elevated manipulation probability was measured.")
        signals.append("Model outputs and thresholds are not calibrated forensic confidence.")

        return {
            "status": "complete", "case_id": case_id, "fps": extraction["fps"],
            "total_frames": extraction["total_frames"], "frames_analyzed": len(frame_probabilities),
            "faces_detected": faces["faces_detected"], "frames_with_faces": faces["frames_with_faces"],
            "suspicious_frame_count": aggregate["suspicious_frame_count"], "suspicious_ratio": aggregate["suspicious_ratio"],
            "mean_probability": aggregate["mean_probability"], "median_probability": aggregate["median_probability"],
            "probability_variance": aggregate["probability_variance"], "longest_suspicious_sequence": aggregate["longest_suspicious_sequence"],
            "frame_probabilities": frame_probabilities, "verdict": aggregate["verdict"], "confidence": aggregate["confidence"], "confidence_calibrated": False, "decision_policy": aggregate["decision_policy"],
            "manipulation_indicators": signals, "explanation_signals": signals,
            "model": inference_engine.model_name,
            "model_source": inference_engine.model_source,
            "research_reference_model": inference_engine.reference,
            "processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
            "stages": [
                {"key": "sampling", "label": "Frame sampling", "status": "complete"},
                {"key": "faces", "label": "Face localization", "status": "complete"},
                {"key": "features", "label": "Feature extraction", "status": "complete"},
                {"key": "inference", "label": "Authenticity inference", "status": "complete"},
                {"key": "aggregation", "label": "Temporal aggregation", "status": "complete"},
                {"key": "verdict", "label": "Video verdict", "status": "complete"},
            ],
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        try:
            video_path = find_video_path(case_id)
            if os.path.exists(video_path):
                os.remove(video_path)
        except HTTPException:
            pass
        if os.path.isdir(case_frame_dir):
            import shutil
            shutil.rmtree(case_frame_dir)