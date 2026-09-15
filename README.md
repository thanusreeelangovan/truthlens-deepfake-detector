# TruthLens

TruthLens is a local media-forensics workstation for a trainable, probabilistic deepfake detector. It samples video over time, detects faces, runs a trained EfficientNet-B0 classifier on face crops, and aggregates frame evidence into a confidence-aware verdict. It is not forensic proof.

## Architecture

The current FastAPI and React architecture is preserved. FastAPI owns upload validation, time-based OpenCV sampling, face localization, checkpoint inference, temporal aggregation, and cleanup. React consumes the existing API service and displays the report. Dataset adapters and model training are separate from runtime inference.

```text
video -> time sampling -> face crop -> 224x224 ImageNet preprocessing
      -> EfficientNet-B0 -> frame probability -> temporal aggregation -> verdict
```

## Kaggle DFDC workflow

The easiest training path is the Kaggle Deepfake Detection Challenge dataset. The scripts do not download dataset files or require Kaggle credentials. In Kaggle, attach the dataset or upload a downloaded DFDC chunk, clone this repository, and set paths through command arguments or `TRUTHLENS_DFDC_ROOT`.

Expected local or Kaggle layout:

```text
data/raw/dfdc/
  metadata.json
  train_sample_videos/
    video1.mp4
  video1.mp4
  video2.mp4
```

For larger DFDC chunks, the adapter scans nested directories and accepts one `metadata.json` beside each chunk:

```text
/kaggle/input/dfdc-chunk-1/metadata.json
/kaggle/input/dfdc-chunk-1/*.mp4
/kaggle/input/dfdc-chunk-2/metadata.json
/kaggle/input/dfdc-chunk-2/*.mp4
```

The metadata adapter reads `filename`, `label`, and `original`. It maps `REAL=0` and `FAKE=1`, binds each fake to its `original` source group, validates files, and prints missing-file statistics. It never silently treats missing metadata files as valid training data.

Kaggle commands:

```bash
cd /kaggle/working
git clone https://github.com/thanusreeelangovan/truthlens-deepfake-detector.git
cd truthlens-deepfake-detector
python scripts/prepare_dfdc.py --raw-root /kaggle/input/dfdc
python scripts/create_splits.py --input data/processed/dfdc/manifest.csv --output data/processed/dfdc/manifest.csv
python scripts/extract_faces.py --manifest data/processed/dfdc/manifest.csv --output-root data/processed/dfdc/faces --interval-seconds 0.5
python training/train.py --manifest data/processed/dfdc/faces/face_manifest.csv --checkpoint models/truthlens_efficientnet_b0.pt
python training/evaluate.py --manifest data/processed/dfdc/faces/face_manifest.csv --checkpoint models/truthlens_efficientnet_b0.pt --split test
```

For local use, replace `/kaggle/input/dfdc` with `data/raw/dfdc`. Generated files are ignored by Git. Kaggle output files can be written under `/kaggle/working/` by passing absolute output paths.

## FaceForensics++ compatibility

The existing adapter remains available for officially obtained FaceForensics++ c23 files:

```bash
python scripts/prepare_faceforensics.py
python scripts/create_splits.py
```

It is not required for the DFDC path. Dataset files must be obtained under their respective access agreements and are not included here.

## Training

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
python training/train.py --manifest data/processed/dfdc/faces/face_manifest.csv
```

The model is ImageNet-pretrained EfficientNet-B0 with a two-class REAL/MANIPULATED head. Training uses weighted CrossEntropyLoss, AdamW, ReduceLROnPlateau, early stopping, validation-F1 checkpointing, and CUDA mixed precision when available. CPU mode is supported for debugging but is substantially slower. Per epoch it logs training/validation loss, accuracy, precision, recall, F1, and ROC AUC when both classes are present.

The best checkpoint is saved at `models/truthlens_efficientnet_b0.pt`.

## Evaluation

```bash
python training/evaluate.py --manifest data/processed/dfdc/faces/face_manifest.csv --checkpoint models/truthlens_efficientnet_b0.pt --split test
```

The report includes frame-level accuracy, precision, recall, F1, ROC AUC, false-positive rate, false-negative rate, and confusion matrix. It also reports video-level metrics by grouping crops belonging to one source group and applying the production aggregation logic. No metrics are claimed until this command is run on an actual dataset and checkpoint.

## Runtime inference

Start the backend from the repository root:

```bash
uvicorn backend.main:app --reload --port 8000
```

The backend loads `models/truthlens_efficientnet_b0.pt` once at startup. Override it with `TRUTHLENS_CHECKPOINT=/absolute/path/model.pt`. Without a checkpoint, `/api/health` returns `model_loaded: false` and analysis returns HTTP 503. No random or mock predictions are produced.

Each face crop is resized to 224x224 and normalized with ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)`. Frames are sampled by time interval, defaulting to one second in runtime and configurable with `--interval-seconds` during extraction. Frames without a usable face are skipped.

Aggregation thresholds are centralized in [training/config.py](training/config.py): suspicious probability `0.65`, authentic ratio maximum `0.15`, authentic median maximum `0.30`, manipulated ratio minimum `0.45`, and minimum suspicious sequence length `3`. Verdicts are `LIKELY_AUTHENTIC`, `INCONCLUSIVE`, and `LIKELY_MANIPULATED`. A single high-probability frame cannot produce a manipulated verdict.

The API returns case ID, analyzed frames, faces, frame probabilities, suspicious count and ratio, mean, median, variance, longest suspicious sequence, confidence, verdict, measurable indicators, and processing time.

## Project structure

```text
data/README.md
scripts/prepare_dfdc.py
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
models/                         # ignored local checkpoints
```

## Tests and limitations

```bash
pytest -q
python -m py_compile backend/main.py backend/utils/*.py training/*.py scripts/*.py
```

Tests cover DFDC metadata mapping, source-group linkage, missing-file reporting, split leakage, threshold boundaries, and the three verdict classes. Face detection can miss faces under occlusion, unusual pose, low resolution, or difficult lighting. Results depend on training distribution and manipulation type. This project makes no production-accuracy claim and does not establish provenance or legal authenticity.
