"""
TruthLens AI — Backend Entry Point
Path: backend/main.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.utils.video_processor import save_video, extract_frames, find_video_path, FRAMES_DIR
from backend.utils.face_detector import detect_faces
from backend.utils.inference import InferenceEngine, MODEL_CHECKPOINT, MODEL_NAME
from backend.utils.aggregation import aggregate_probabilities

inference_engine = None
model_error = None

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "TruthLens AI", "version": "0.4.0", "model_loaded": inference_engine is not None, "model_error": model_error}


@app.on_event("startup")
async def load_detector():
    global inference_engine, model_error
    if os.path.exists(MODEL_CHECKPOINT):
        try:
            inference_engine = InferenceEngine(MODEL_CHECKPOINT)
        except RuntimeError as exc:
            model_error = str(exc)


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    result = save_video(file)
    return {
        "status": "received",
        "case_id": result["case_id"],
        "filename": result["filename"],
        "size_mb": result["size_mb"],
        "next_stage": "frame_extraction",
    }


@app.post("/api/analyze/{case_id}")
async def analyze_case(case_id: str):
    case_frame_dir = os.path.join(FRAMES_DIR, case_id)
    try:
        if inference_engine is None:
            raise HTTPException(status_code=503, detail=model_error or f"Trained checkpoint not found at '{MODEL_CHECKPOINT}'.")
        started = time.perf_counter()
        extraction = extract_frames(case_id)
        faces = detect_faces(extraction["frame_paths"], case_frame_dir)
        frame_probabilities = inference_engine.predict(faces["face_crops"])
        values = [item["fake_probability"] for item in frame_probabilities]
        aggregate = aggregate_probabilities(values)
        signals = []
        if aggregate["suspicious_frame_count"]:
            signals.append(f"{aggregate['suspicious_frame_count']} of {len(values)} analyzed frames showed elevated manipulation probability.")
        if aggregate["longest_suspicious_sequence"]:
            signals.append(f"Manipulation probability remained elevated across {aggregate['longest_suspicious_sequence']} consecutive frames.")
        if not signals:
            signals.append("No sustained elevated manipulation probability was measured.")

        return {
            "status": "complete", "case_id": case_id, "fps": extraction["fps"],
            "total_frames": extraction["total_frames"], "frames_analyzed": len(frame_probabilities),
            "faces_detected": faces["faces_detected"], "frames_with_faces": faces["frames_with_faces"],
            "suspicious_frame_count": aggregate["suspicious_frame_count"], "suspicious_ratio": aggregate["suspicious_ratio"],
            "mean_probability": aggregate["mean_probability"], "median_probability": aggregate["median_probability"],
            "probability_variance": aggregate["probability_variance"], "longest_suspicious_sequence": aggregate["longest_suspicious_sequence"],
            "frame_probabilities": frame_probabilities, "verdict": aggregate["verdict"], "confidence": aggregate["confidence"],
            "manipulation_indicators": signals, "explanation_signals": signals, "model": MODEL_NAME,
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