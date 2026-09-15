# FaceForensics++ data

TruthLens does not download or store dataset files in Git. Request FaceForensics++ access from the official project, select the compressed `c23` videos, and place the extracted manipulation folders here:

```text
data/raw/FaceForensics++/
  original/*.mp4
  Deepfakes/*.mp4
  FaceSwap/*.mp4
  Face2Face/*.mp4
  NeuralTextures/*.mp4
```

Run the preparation scripts from the repository root. Generated manifests and face crops belong under `data/processed/` and are ignored by Git.
