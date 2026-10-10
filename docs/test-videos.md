# TruthLens: real/fake video testing and reproducible evaluation

This page is for **testing**, not a claim of reliable detection. The hosted
research checkpoint has already scored a non-manipulated still-image clip as
likely fake. TruthLens v0.7+ deliberately returns INCONCLUSIVE for the
unvalidated reference detector and shows raw experimental frame scores.
Its reported raw score is not a calibrated probability of authenticity.

## Where to obtain labelled clips (review each license first)

| Dataset | Best use | Labels and access |
|---|---|---|
| [DFDC Kaggle sample](https://www.kaggle.com/competitions/deepfake-detection-challenge/data) | Start here; realistic real/fake pairs | Extract **train_sample_videos.zip**; **metadata.json** gives REAL/FAKE and original filename. Account and competition terms required. The separate **test_videos.zip** does not provide ground truth labels. |
| [UADFV (98 videos)](https://drive.google.com/drive/u/0/folders/1GEk1DSxmlV_61JtpEGzC9Fo_BffvyxpH) | Smaller early real/fake benchmark | Reportedly 49 real + 49 fake videos. Check folder access, provenance and redistribution rights. |
| [FaceForensics++](https://github.com/ondyari/FaceForensics/tree/master/dataset) | Test the reference model in its original training domain | Original sequences and Deepfakes / FaceSwap / Face2Face / NeuralTextures in C23. Apply through the authors' official access request. Avoid evaluating on any exact clips used in model training. |
| [Celeb-DF v2](https://github.com/yuezunli/celeb-deepfakeforensics) | Test transfer to different manipulations | Research access request; includes real and synthetic videos. |
| [DF26 (2026)](https://huggingface.co/datasets/DF26/DF26) | Stress-test against newer AI-video generators | 271 real and 2,420 fake short talking-head videos. Gated, evaluation-only restrictions: don't redistribute or use prohibited subsets for training. |

**Quick manual checks:** record your own 8–12 second front-facing camera
clip in good light (label REAL), one with head movement and speech and one
with dimmer light or moderate compression. Compare with a labelled FAKE
sample from an authorized dataset. Keep the originals untouched and
record the source, compression, duration and known label. A near-static clip
is a **quality test**, not evidence of authenticity.

Only upload videos that you have permission to send to the hosted API.
Do not upload private or sensitive footage belonging to someone else.
Render may sleep on its free tier and impose upload/processing limits.

## Generate a balanced DFDC test manifest

1. Sign in to Kaggle and accept the competition's dataset terms.
2. Download and extract \`train_sample_videos.zip\`. It should contain
   MP4 files alongside \`metadata.json\`.
3. From the project root:

\`\`\`bash
python -m scripts.build_eval_manifest --dfdc-root "path/to/train_sample_videos" --pairs 10 --seed 42 --output data/processed/eval/dfdc_pairs.csv
\`\`\`

This selects up to ten **matched** source groups, one REAL original and
one FAKE derived from it per group. Selection is reproducible. Videos
and licences remain with their provider, not in this GitHub repository.

## Benchmark the public hosted research API

First inspect the manifest without sending files anywhere:

\`\`\`bash
python -m scripts.evaluate_live_videos --manifest data/processed/eval/dfdc_pairs.csv --dry-run
\`\`\`

If you have rights and consent to upload the listed videos:

\`\`\`bash
python -m scripts.evaluate_live_videos \
  --manifest data/processed/eval/dfdc_pairs.csv \
  --api-url https://truthlens-api-cysu.onrender.com \
  --output reports/dfdc_reference_eval.json \
  --max-videos 20
\`\`\`

The command uploads videos sequentially; each must meet the current
100 MB and 120-second API limits. Use a small number of clips to avoid
exhausting the free backend. Results are saved locally; **do not commit**
the JSON if clip names or paths may reveal private information.
Run against \`http://127.0.0.1:8000\` to avoid uploading to Render.

You can also make a CSV by hand with two columns:

\`\`\`csv
video_path,label
C:/Videos/authentic_01.mp4,REAL
C:/Videos/authorized_deepfake_01.mp4,FAKE
\`\`\`

### How to interpret the report

- **Completed / errors:** API reliability. Investigate any non-200 response.
- **Abstention rate and coverage:** The unvalidated reference model
  intentionally abstains; this is not a classification accuracy result.
- **Exploratory raw-mean-score ROC AUC:** Measures whether labelled FAKE
  clips tend to rank above REAL clips. Only defined if scorable examples of
  both labels exist, and does **not** imply calibrated probabilities.
- **Candidate threshold false-alarm / detection rates:** Diagnostics for
  thresholds 0.50, 0.65 and 0.90, NOT deployable calibrated thresholds.
  The values are based on **mean raw model scores** and exclude near-static
  / insufficient-face clips. Choose thresholds using a separate
  validation set, then report metrics on untouched test data.
- **Accuracy on decided videos:** Undefined when the model abstains
  on every video; never report this as 100% or 0%.

Start with 10 REAL + 10 FAKE, then scale to at least 50 of each from
multiple sources. The first set is a smoke benchmark only, not a
publishable accuracy estimate.

For robust next steps, hold out source identities across train/test,
compare FaceForensics++ C23 vs DFDC / Celeb-DF domain shift, measure
false-positive rate, true-positive rate, AUC, coverage and calibration.
A longer-term upgrade is to train a TruthLens checkpoint on licensed
data and evaluate it on an independent labelled test set.
