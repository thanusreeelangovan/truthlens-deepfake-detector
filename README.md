# TruthLens

TruthLens is a local media-forensics workstation for a trainable, probabilistic deepfake detector. It samples video over time, detects faces, runs a trained EfficientNet-B0 classifier on face crops, and aggregates frame evidence into a confidence-aware verdict. It is not forensic proof and should not be treated as definitive.

## Architecture

React and Vite provide the evidence upload and report workstation. FastAPI owns upload validation, time-based OpenCV frame sampling, Haar cascade face localization, PyTorch/TorchVision inference, temporal aggregation, and temporary-file cleanup. Training and evaluation live in `training/` and dataset preparation in `scripts/`. All browser requests go through `frontend/src/services/api.js`.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API loads `models/truthlens_efficientnet_b0.pt` once at startup. It returns an explicit error if that trained checkpoint is missing or cannot load; it never fabricates a score.

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

## Dataset and training

FaceForensics++ is the primary dataset. It is access-controlled by its official research agreement; obtain the compressed `c23` videos through the official process and place them under the layout in [data/README.md](data/README.md). Dataset files, crops, manifests, and weights are ignored by Git. No dataset files are included here. Respect the dataset's license and terms.

From the repository root:

```bash
python scripts/prepare_faceforensics.py
python scripts/create_splits.py
python scripts/extract_faces.py
python training/train.py
python training/evaluate.py
```

The manifest is split at source-video level with a fixed seed into approximately 70% train, 15% validation, and 15% test. Frames from one source video cannot cross splits. `training/train.py` uses ImageNet-pretrained EfficientNet-B0, a two-class REAL/MANIPULATED head, weighted CrossEntropyLoss, AdamW, ReduceLROnPlateau, early stopping, checkpointing on validation F1, and CUDA mixed precision when available. It logs loss, accuracy, precision, recall, F1, and ROC AUC per epoch. `training/evaluate.py` reports accuracy, precision, recall, F1, ROC AUC, false-positive rate, false-negative rate, and confusion matrix for the selected split.

## Inference pipeline

The deployed model is the locally trained EfficientNet-B0 checkpoint. Each largest detected face crop is resized to 224x224 and normalized with ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)`. The manipulated-class softmax score is the frame-level manipulation probability.

Frames are sampled once per second. Face crops are localized with OpenCV's bundled `haarcascade_frontalface_default.xml`, with a small margin. Frames with no usable face are skipped. A frame score is the mean score of its detected face crops.

Classification thresholds are configuration constants in `backend/main.py`:

- `LIKELY_MANIPULATED` only when at least 45% of scored frames are at or above 0.65 and at least 3 suspicious frames are consecutive.
- `LIKELY_AUTHENTIC` when no more than 15% of scored frames reach that threshold and median probability is at most 0.30.
- `INCONCLUSIVE` for mixed evidence or no detectable faces.

Aggregation also returns mean, median, variance, suspicious ratio, and longest suspicious sequence. These initial thresholds are configuration values, not calibrated claims.

The response includes sampled frame indices, probabilities, face counts, suspicious ratio, signals, model ID, and the verdict. A single anomalous frame cannot determine the video verdict.

## API

- `GET /api/health`
- `POST /api/upload` with multipart field `file`
- `POST /api/analyze/{case_id}`

Uploads must use MP4, MOV, AVI, or WEBM, remain under 100 MB, and be readable by OpenCV. Uploaded videos and extracted crops are removed after analysis, including failed analysis attempts. The model checkpoint path can be changed with `TRUTHLENS_CHECKPOINT`.

## Project structure

```text
data/README.md
scripts/prepare_faceforensics.py
scripts/create_splits.py
scripts/extract_faces.py
training/config.py
training/data.py
training/model.py
training/train.py
training/evaluate.py
backend/utils/aggregation.py
backend/utils/inference.py
models/                         # local ignored checkpoints
```

## Limitations

The detector is probabilistic and has not been trained or evaluated in this repository until you run the supplied commands; this project therefore makes no accuracy claim. Performance depends on dataset distribution and manipulation type. Haar detection can miss faces, particularly under occlusion, unusual lighting, or large pose changes. EfficientNet frame scores do not establish provenance, intent, or legal authenticity. DFDC cross-dataset evaluation is intentionally not bundled because it requires separate Kaggle access; use `training/evaluate.py` with a compatible external manifest if available.
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