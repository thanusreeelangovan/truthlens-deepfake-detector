"""
TruthLens AI — Backend Entry Point
Path: backend/main.py
"""

import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.video_processor import save_video, extract_frames, find_video_path, FRAMES_DIR
from utils.face_detector import detect_faces
from utils.inference import infer_faces

SUSPICIOUS_FRAME_THRESHOLD = 0.65
LIKELY_MANIPULATED_RATIO = 0.45
LIKELY_AUTHENTIC_RATIO = 0.15

app = FastAPI(
    title="TruthLens AI",
    description="Real-time media authenticity analysis engine",
    version="0.3.0",
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
    return {"status": "online", "engine": "TruthLens AI", "version": "0.3.0"}


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
        extraction = extract_frames(case_id)
        faces = detect_faces(extraction["frame_paths"], case_frame_dir)
        inference = infer_faces(faces["face_crops"])
        frame_probabilities = inference["frame_probabilities"]
        suspicious = [item for item in frame_probabilities if item["fake_probability"] >= SUSPICIOUS_FRAME_THRESHOLD]
        suspicious_ratio = len(suspicious) / len(frame_probabilities) if frame_probabilities else 0

        if not frame_probabilities:
            verdict = "INCONCLUSIVE"
            confidence = 0
            signals = ["No detectable face regions were available for inference."]
        elif suspicious_ratio >= LIKELY_MANIPULATED_RATIO:
            verdict = "LIKELY_MANIPULATED"
            confidence = round(min(100, suspicious_ratio * 100), 1)
            signals = ["Facial texture inconsistency", "Temporal instability"]
        elif suspicious_ratio <= LIKELY_AUTHENTIC_RATIO:
            verdict = "LIKELY_AUTHENTIC"
            confidence = round(min(100, (1 - suspicious_ratio) * 100), 1)
            signals = ["Probability consistency"]
        else:
            verdict = "INCONCLUSIVE"
            confidence = round((1 - abs(suspicious_ratio - 0.5) * 2) * 100, 1)
            signals = ["Mixed frame-level evidence"]

        return {
            "status": "complete", "case_id": case_id, "fps": extraction["fps"],
            "total_frames": extraction["total_frames"], "frames_analyzed": len(frame_probabilities),
            "faces_detected": faces["faces_detected"], "frames_with_faces": faces["frames_with_faces"],
            "suspicious_frame_count": len(suspicious), "suspicious_ratio": round(suspicious_ratio, 4),
            "frame_probabilities": frame_probabilities, "verdict": verdict, "confidence": confidence,
            "explanation_signals": signals, "model": inference["model"],
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