# FaceForensics++ data

TruthLens does not download or store dataset files in Git. Request FaceForensics++ access from the official project, select the compressed `c23` videos, and place the extracted manipulation folders here:

```text
data/raw/FaceForensics++/
  original_sequences/youtube/c23/videos/*.mp4
  manipulated_sequences/Deepfakes/c23/videos/*.mp4
  manipulated_sequences/FaceSwap/c23/videos/*.mp4
  manipulated_sequences/Face2Face/c23/videos/*.mp4
  manipulated_sequences/NeuralTextures/c23/videos/*.mp4
```

The manifest builder scans nested directories and also accepts a flattened `original/`, `Deepfakes/`, `FaceSwap/`, `Face2Face/`, and `NeuralTextures/` layout.

Run the preparation scripts from the repository root. Generated manifests and face crops belong under `data/processed/` and are ignored by Git.
