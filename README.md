# TruthLens

TruthLens is a local media-forensics workstation for probabilistic deepfake analysis. It samples video over time, detects faces, runs a pretrained image classifier on face crops, and aggregates frame evidence into a confidence-aware verdict. It is not forensic proof and should not be treated as definitive.

## Architecture

React and Vite provide the evidence upload and report workstation. FastAPI owns upload validation, time-based OpenCV frame sampling, Haar cascade face localization, PyTorch/Transformers inference, temporal aggregation, and temporary-file cleanup. All browser requests go through `frontend/src/services/api.js`.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The first analysis downloads the configured Hugging Face model if it is not cached. Set `TRUTHLENS_MODEL_ID` to use another compatible image-classification model. If the model cannot load, the API returns an explicit error and never fabricates a score.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000`. Set `VITE_API_URL` to a different backend origin, for example:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Inference pipeline

The default model is `dima806/deepfake_vs_real_image_detection`, used as an image classifier over detected face crops. The Transformers processor performs the model's resize and normalization preprocessing; the model's fake score is normalized against its real and fake scores to produce a frame-level manipulated probability.

Frames are sampled once per second. Face crops are localized with OpenCV's bundled `haarcascade_frontalface_default.xml`. A frame score is the mean score of its detected face crops.

Classification thresholds are configuration constants in `backend/main.py`:

- `LIKELY_MANIPULATED` when at least 45% of scored frames are at or above 0.65 fake probability.
- `LIKELY_AUTHENTIC` when no more than 15% of scored frames reach that threshold.
- `INCONCLUSIVE` for mixed evidence or no detectable faces.

The response includes sampled frame indices, probabilities, face counts, suspicious ratio, signals, model ID, and the verdict. A single anomalous frame cannot determine the video verdict.

## API

- `GET /api/health`
- `POST /api/upload` with multipart field `file`
- `POST /api/analyze/{case_id}`

Uploads must use MP4, MOV, AVI, or WEBM, remain under 100 MB, and be readable by OpenCV. Uploaded videos and extracted crops are removed after analysis, including failed analysis attempts.

## Limitations

The detector is probabilistic and has not been calibrated or independently evaluated by this project. Haar detection can miss faces, particularly under occlusion, unusual lighting, or large pose changes. Model availability requires network access on first use, and image-level deepfake scores do not establish provenance, intent, or legal authenticity.
# TruthLens — Deepfake Detection System

## Quick start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# opens at http://localhost:5173
```

## Demo flow (for judges)
1. Open http://localhost:5173
2. Either upload a video OR click **Run demo analysis**
3. Watch the live forensic pipeline animate step by step
4. Read the verdict card, confidence score, and frame indicators

## Git workflow
- `backend-dev` → all Python changes
- `frontend-dev` → all React changes
- `main` → working merges only, push daily