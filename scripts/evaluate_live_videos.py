"""Measure TruthLens on a labelled video manifest, including abstentions and raw-score false alarms.

WARNING: Passing --api-url pointing to a public server UPLOADS all listed videos
to that service. Run only on clips for which you have upload rights and consent.
No videos or remote case IDs are stored in the local report.
"""
import argparse
import csv
import json
import math
import time
from pathlib import Path

import httpx
from sklearn.metrics import confusion_matrix, roc_auc_score

LABELS = {"REAL": 0, "FAKE": 1}
VERDICTS = {"LIKELY_AUTHENTIC": 0, "LIKELY_MANIPULATED": 1}
EXPLORATORY_THRESHOLDS = (0.50, 0.65, 0.90)


def read_manifest(manifest: Path, max_videos: int = 20) -> list[dict]:
    if max_videos < 1:
        raise ValueError("max_videos must be at least 1.")
    with Path(manifest).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"video_path", "label"} <= set(reader.fieldnames):
            raise ValueError("Manifest needs video_path and label columns.")
        rows = list(reader)
    if not rows:
        raise ValueError("Manifest is empty.")
    if len(rows) > max_videos:
        raise ValueError(f"Manifest has {len(rows)} videos. Raise --max-videos to confirm the larger upload.")
    for row in rows:
        label = str(row["label"]).upper()
        if label not in LABELS:
            raise ValueError(f"Unknown label {label!r}. Use REAL or FAKE.")
        row["label"] = label
        video = Path(row["video_path"]).expanduser()
        if not video.is_absolute():
            video = (Path(manifest).parent / video).resolve()
        if not video.is_file():
            raise FileNotFoundError(f"Cannot find video: {video}")
        if video.suffix.lower() not in {".mp4", ".mov", ".avi", ".webm"}:
            raise ValueError(f"Unsupported video extension: {video.name}")
        row["video_path"] = str(video)
    return rows


def summarize(outcomes: list[dict]) -> dict:
    """Separate operational verdicts from exploratory raw score discrimination."""
    successful = [r for r in outcomes if r.get("status") == "complete"]
    decided = [r for r in successful if r.get("verdict") in VERDICTS]
    abstentions = [r for r in successful if r.get("verdict") == "INCONCLUSIVE"]
    metric = {
        "requested": len(outcomes),
        "completed": len(successful),
        "errors": len(outcomes) - len(successful),
        "labelled_real_completed": sum(r["label"] == "REAL" for r in successful),
        "labelled_fake_completed": sum(r["label"] == "FAKE" for r in successful),
        "reported_verdicts": {name: sum(r.get("verdict") == name for r in successful)
                              for name in ("LIKELY_AUTHENTIC", "LIKELY_MANIPULATED", "INCONCLUSIVE")},
        "decided_videos": len(decided),
        "abstentions": len(abstentions),
        "coverage": len(decided) / len(successful) if successful else None,
        "abstention_rate": len(abstentions) / len(successful) if successful else None,
        "accuracy_on_decided_videos": None,
        "confusion_matrix_on_decided": None,
    }
    if decided:
        truth = [LABELS[r["label"]] for r in decided]
        predicted = [VERDICTS[r["verdict"]] for r in decided]
        metric["accuracy_on_decided_videos"] = sum(a == b for a, b in zip(truth, predicted)) / len(truth)
        metric["confusion_matrix_on_decided"] = confusion_matrix(truth, predicted, labels=[0, 1]).tolist()

    # The scoring subset excludes no-face and near-static clips. Those still count
    # toward operational coverage and are visible in the per-video output.
    scorable = [
        r for r in successful
        if r.get("frames_analyzed", 0) >= 3
        and r.get("raw_mean_score") is not None
        and math.isfinite(float(r["raw_mean_score"]))
        and not r.get("near_static_video", False)
    ]
    raw = {
        "eligible_videos": len(scorable),
        "excluded_from_score_comparison": len(successful) - len(scorable),
        "roc_auc": None,
        "candidate_thresholds_NOT_CALIBRATED": {},
    }
    if len({r["label"] for r in scorable}) == 2:
        raw["roc_auc"] = float(roc_auc_score(
            [LABELS[r["label"]] for r in scorable],
            [float(r["raw_mean_score"]) for r in scorable],
        ))
    for threshold in EXPLORATORY_THRESHOLDS:
        authentic = [r for r in scorable if r["label"] == "REAL"]
        fake = [r for r in scorable if r["label"] == "FAKE"]
        raw["candidate_thresholds_NOT_CALIBRATED"][str(threshold)] = {
            "false_alarm_rate_on_real": (
                sum(r["raw_mean_score"] >= threshold for r in authentic) / len(authentic)
                if authentic else None
            ),
            "detection_rate_on_fake": (
                sum(r["raw_mean_score"] >= threshold for r in fake) / len(fake)
                if fake else None
            ),
            "real_count": len(authentic),
            "fake_count": len(fake),
        }
    metric["exploratory_raw_mean_score"] = raw
    metric["warning"] = (
        "Do not claim calibrated confidence or deployment accuracy from these exploratory thresholds. "
        "AUC measures score ranking, not probability calibration; hold out entire source/identity groups. "
        "If every model verdict abstains, classification accuracy is undefined, not zero or 100%."
    )
    return metric


def run_evaluation(rows: list[dict], api_url: str, delay: float = 0.0) -> list[dict]:
    if delay < 0:
        raise ValueError("Delay must be non-negative.")
    outcomes = []
    timeout = httpx.Timeout(connect=30, read=240, write=120, pool=30)
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=timeout, follow_redirects=False) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        if not health.json().get("model_loaded"):
            raise RuntimeError("Backend health says model_loaded=false. Evaluation cannot start.")
        model_info = client.get("/api/model/info")
        model_info.raise_for_status()
        print("Model:", model_info.json().get("model_source") or model_info.json().get("name"))
        for i, row in enumerate(rows, start=1):
            path = Path(row["video_path"])
            record = {"filename": path.name, "label": row["label"],
                      "dataset": row.get("dataset", "unspecified"),
                      "status": "error", "error": None}
            try:
                # Upload once and immediately request analysis. The API deletes files.
                with path.open("rb") as file_handle:
                    uploaded = client.post("/api/upload", files={
                        "file": (path.name, file_handle, "video/mp4")
                    })
                uploaded.raise_for_status()
                case_id = uploaded.json()["case_id"]
                analyzed = client.post(f"/api/analyze/{case_id}")
                analyzed.raise_for_status()
                result = analyzed.json()
                record.update({
                    "status": "complete", "verdict": result["verdict"],
                    "frames_analyzed": result.get("frames_analyzed", 0),
                    "near_static_video": result.get("frame_quality", {}).get("near_static_video", False),
                    "raw_mean_score": result.get("mean_probability"),
                    "screening_signal": result.get("screening_signal"),
                    "decision_reason_code": result.get("decision_reason_code"),
                    "model_source": result.get("model_source"),
                })
                print(f"[{i}/{len(rows)}] {path.name}: {record['verdict']} "
                      f"mean={record['raw_mean_score']} static={record['near_static_video']}")
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                record["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
                print(f"[{i}/{len(rows)}] {path.name}: ERROR {record['error']}")
            outcomes.append(record)
            if delay and i < len(rows):
                time.sleep(delay)
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--api-url", help="Explicit destination for uploads; use http://127.0.0.1:8000 for local.")
    parser.add_argument("--output", type=Path, default=Path("reports/truthlens_evaluation.json"))
    parser.add_argument("--max-videos", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and labels without uploading any media.")
    args = parser.parse_args()
    rows = read_manifest(args.manifest, args.max_videos)
    real = sum(r["label"] == "REAL" for r in rows)
    fake = len(rows) - real
    print(f"Validated {len(rows)} videos: {real} REAL, {fake} FAKE")
    if args.dry_run:
        print("Dry run complete. Nothing uploaded.")
        return
    if not args.api_url:
        parser.error("--api-url is required unless --dry-run is used.")
    outcomes = run_evaluation(rows, args.api_url, args.delay)
    payload = {
        "api_url": args.api_url,
        "manifest_name": args.manifest.name,
        "note": "Locally generated experimental report. Videos are not bundled with this JSON.",
        "summary": summarize(outcomes),
        "videos": outcomes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")
    if payload["summary"]["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
