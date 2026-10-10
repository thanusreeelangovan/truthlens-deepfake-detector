# TruthLens

TruthLens is a local media-forensics workstation for a trainable, probabilistic deepfake detector. It samples video over time, detects faces, runs a trained EfficientNet-B0 classifier on face crops, and aggregates frame evidence into a confidence-aware verdict. It is not forensic proof.

## False positives and research verdict safeguards (v0.7)

The previous hosted research baseline produced a false positive on an authentic face-photo clip, demonstrating that a passing inference test is **not evidence of accuracy**. The Xicor9 reference model's model card maps class 0 to real, class 1 to fake, and shows **full frames resized to 224×224 with ToTensor only**, rather than tightly cropped face patches. The hosted research path now follows that documented input format, while continuing to require at least one detectable face in each analyzed frame.

Until a representative labelled authentic/manipulated dataset is evaluated, the third-party reference is **screening-only**: its internal aggregate is available through the frame scores, but the public verdict is \`INCONCLUSIVE\` with a distinct \`LOW_MODEL_SIGNAL\`, \`MIXED_MODEL_SIGNAL\`, or \`ELEVATED_MODEL_SIGNAL\`. A nearly static video also receives \`INCONCLUSIVE\` as its frames are not independent temporal observations. These guards avoid unsupported fake/real accusations; they do not improve model accuracy.

For meaningful authentic-versus-manipulated classification, independently evaluate both classes on held-out videos matching the intended use, investigate false positives and compression/lighting sensitivity, determine calibrated operating thresholds, and document error rates with abstention coverage. Do not tune a threshold solely to pass a handful of demo videos.

## Live research demo

**Frontend:** [Open TruthLens experimental live demo](https://truthlens-web-hnkt.onrender.com)  
**API readiness:** [Backend health](https://truthlens-api-cysu.onrender.com/api/health)

The hosted version optionally runs the **externally trained** [Xicor9 EfficientNet-B0 FaceForensics++ C23 reference checkpoint](https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23) by Himanshu Kashyap. Its weights are downloaded at backend startup when `TRUTHLENS_REFERENCE_DEMO=1` is set. **TruthLens did not train that model**, and its published benchmark figures have not been independently reproduced here. It is an educational research demonstration, not forensic proof. The model is enabled only when the readiness endpoint reports `model_loaded: true`.

Public hosting has resource and cold start limitations; short clips are recommended. The project training pipeline remains separate and allows replacing the reference checkpoint with independently trained, evaluated weights.

**Accuracy caveat from live testing:** An end-to-end smoke test on October 10, 2026 successfully uploaded a six-second clip made from an unmanipulated face photograph and produced frame scores. The external model classified that constructed clip as `LIKELY_MANIPULATED`. This highlights potential false positives and dataset shift; the smoke test verifies API functionality only. No reliable real-world detection accuracy is claimed.

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

The metadata adapter reads `filename`, `label`, and `original`. It maps `REAL=0` and `FAKE=1`, binds each fake to its `original` source group, validates files, and prints missing-file statistics. It never silently treats missing metadata files as valid training data. Each video also receives a unique `video_id` distinct from its `source_group`, preventing crop directory collisions.

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

The best checkpoint is saved at `models/truthlens_efficientnet_b0.pt`. Training and runtime share the same largest-face crop and margin implementation.

## Test videos and reproducible live evaluation

See [docs/test-videos.md](docs/test-videos.md) for verified dataset sources,
a labelled DFDC REAL/FAKE pair generator, a live API evaluation command,
and guidance on false positives, abstentions and raw-score ROC AUC.
No accuracy statistics have been claimed without running labelled clips.

## Evaluation

```bash
python training/evaluate.py --manifest data/processed/dfdc/faces/face_manifest.csv --checkpoint models/truthlens_efficientnet_b0.pt --split test
```

The report includes frame-level accuracy, precision, recall, F1, ROC AUC, false-positive rate, false-negative rate, and confusion matrix. It also reports video-level metrics by grouping crops by individual video, applying the production aggregation logic, and reporting inconclusive outcomes as abstentions rather than authentic predictions. No metrics are claimed until this command is run on an actual dataset and checkpoint.

## Runtime inference

Start the backend from the repository root:

```bash
uvicorn backend.main:app --reload --port 8000
```

The backend loads `models/truthlens_efficientnet_b0.pt` once at startup. Override it with `TRUTHLENS_CHECKPOINT=/absolute/path/model.pt`. Without a checkpoint, `/api/health` returns `model_loaded: false` and analysis returns HTTP 503. No random or mock predictions are produced.

Each face crop is resized to 224x224 and normalized with ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)`. Frames are sampled by time interval, defaulting to one second in runtime and configurable with `--interval-seconds` during extraction. Frames without a usable face are skipped.

Uncalibrated heuristic aggregation thresholds are centralized in [training/config.py](training/config.py): suspicious frame score `0.65`, authentic ratio maximum `0.15`, authentic median maximum `0.30`, manipulated ratio minimum `0.45`, and minimum suspicious sequence length `3`. Verdicts are `LIKELY_AUTHENTIC`, `INCONCLUSIVE`, and `LIKELY_MANIPULATED`. A single high-probability frame cannot produce a manipulated verdict.

The API returns a case ID, analyzed frames, sample timestamps, scores, aggregates, abstention-aware verdict, measurable indicators, and processing time. Calibration has not been established, so confidence is null.

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

## Model readiness and honesty

**The GitHub repository does not contain a TruthLens-trained checkpoint.** The UI refuses uploads when the backend reports `model_loaded: false`. For your own model, train a checkpoint with the documented workflow and configure `TRUTHLENS_CHECKPOINT`. The hosted research demo can instead load the explicitly credited external checkpoint with `TRUTHLENS_REFERENCE_DEMO=1`. Neither approach justifies invented accuracy claims.

The result's `confidence` field is now `null` because the heuristic aggregation policy has not been calibrated on held out videos. The displayed mean frame score is **not** a calibrated probability that the video is fake. Videos with fewer than three analyzable sampled frames receive `INCONCLUSIVE`. Temporal sequence length preserves gaps where no face was detected. The reference implementation intentionally analyzes the largest visible face per sampled frame. It does not yet perform multi-face tracking, speech analysis, C2PA verification, or live model progress reporting.

Runtime limits are 100 MB and 120 seconds per video. Both limits are enforced by the backend and can be tightened for a public deployment. The API uses locally stored temporary files and deletes them after an analysis request. Case data and results are not persisted.

To allow a deployed frontend origin, set `TRUTHLENS_ALLOWED_ORIGINS` to a comma-separated list of trusted HTTPS origins. The Vite frontend uses `VITE_API_URL` for the backend origin.

## Engineering release checklist

1. Run the DFDC pipeline against actual video files (the adapter supports nested train_sample_videos directories).
2. Confirm model checkpoint loading using `GET /api/health`.
3. Run unit tests and the full frontend build.
4. Run `training/evaluate.py` and report held out video outcomes, classification metrics, and abstention coverage.
5. Validate the model on a distinct dataset before claiming real world generalization or calibrated confidence.
6. Only then deploy both the backend with a licensed trained checkpoint and the frontend over HTTPS.

## Tests and limitations

```bash
pytest -q
python -m py_compile backend/main.py backend/utils/*.py training/*.py scripts/*.py
```

Tests cover DFDC metadata mapping, source-group linkage, missing-file reporting, split leakage, threshold boundaries, and the three verdict classes. Face detection can miss faces under occlusion, unusual pose, low resolution, or difficult lighting. Results depend on training distribution and manipulation type. This project makes no production-accuracy claim and does not establish provenance or legal authenticity.
