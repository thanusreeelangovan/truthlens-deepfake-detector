# Local datasets

Dataset files are never downloaded or committed by TruthLens.

## DFDC primary path

Obtain or attach the Kaggle Deepfake Detection Challenge data and point the preparation script at the directory containing one or more `metadata.json` files:

```text
data/raw/dfdc/
  metadata.json
  train_sample_videos/
    video1.mp4
  video1.mp4
  video2.mp4
```

Larger chunks are supported when each chunk contains its own metadata and videos:

```text
/kaggle/input/dfdc-chunk-1/metadata.json
/kaggle/input/dfdc-chunk-1/*.mp4
/kaggle/input/dfdc-chunk-2/metadata.json
/kaggle/input/dfdc-chunk-2/*.mp4
```

Run:

```bash
python scripts/prepare_dfdc.py --raw-root data/raw/dfdc
python scripts/create_splits.py --input data/processed/dfdc/manifest.csv --output data/processed/dfdc/manifest.csv
python scripts/extract_faces.py --manifest data/processed/dfdc/manifest.csv --output-root data/processed/dfdc/faces --interval-seconds 0.5
```

The DFDC adapter reads `label` and optional `original`, maps `REAL=0` and `FAKE=1`, validates listed files, and keeps each original plus its derived fakes in one `source_group` split.

## FaceForensics++ compatibility

The existing FaceForensics++ adapter accepts officially obtained c23 data under:

```text
data/raw/FaceForensics++/
  original_sequences/youtube/c23/videos/*.mp4
  manipulated_sequences/Deepfakes/c23/videos/*.mp4
  manipulated_sequences/FaceSwap/c23/videos/*.mp4
  manipulated_sequences/Face2Face/c23/videos/*.mp4
  manipulated_sequences/NeuralTextures/c23/videos/*.mp4
```

Generated manifests, face crops, and checkpoints are ignored by Git through the repository `.gitignore`.
