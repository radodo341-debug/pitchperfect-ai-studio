"""Run and score a manual identity-continuity review for the selected player.

Run detection:
  python backend/validate_player_identity.py detect clip.mp4 --out-dir tracking_run

Review:
  Open tracking_run/review_template.csv. For each sampled timestamp, fill
  target_present (true/false) and target_track_id (the box ID belonging to the
  purple-shirted target; blank when absent). Use blank target ID for frames where
  the target is not visible. Review boxes visually; never infer identity from ID
  alone across a broadcast cut.

Evaluate:
  python backend/validate_player_identity.py evaluate tracking_run/review_template.csv

Requires the existing backend tracking dependencies and PP_TRACKER_MODEL.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    from player_tracking import sample_video
except ImportError:
    from backend.player_tracking import sample_video


def detect(video: Path, out_dir: Path, sample_fps: float) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    detections = sample_video(str(video), sample_fps=sample_fps)
    (out_dir / "detections.json").write_text(
        json.dumps(detections, indent=2), encoding="utf-8"
    )
    with (out_dir / "detections.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["time_seconds", "frame", "track_id", "confidence", "class",
                  "identity_status", "x1", "y1", "x2", "y2"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for d in detections:
            x1, y1, x2, y2 = d["bbox_xyxy"]
            writer.writerow({
                "time_seconds": d["time_seconds"], "frame": d["frame"],
                "track_id": d["track_id"], "confidence": d["confidence"],
                "class": d["class"], "identity_status": d["identity_status"],
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            })
    times = sorted({float(d["time_seconds"]) for d in detections})
    with (out_dir / "review_template.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "time_seconds", "segment", "target_present", "target_track_id", "notes"
        ])
        writer.writeheader()
        for t in times:
            segment = "before_cut" if t < 9 else ("cut_or_transition" if t < 13 else "celebration")
            writer.writerow({
                "time_seconds": f"{t:.3f}", "segment": segment,
                "target_present": "", "target_track_id": "", "notes": ""
            })
    print(f"Saved {len(detections)} detections across {len(times)} sampled timestamps to {out_dir}")
    print("Next: visually review detections.csv/JSON and fill review_template.csv; then run evaluate.")


def evaluate(review_csv: Path) -> None:
    rows = []
    with review_csv.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            present = row.get("target_present", "").strip().lower()
            tid = row.get("target_track_id", "").strip()
            if present not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError(f"Annotate target_present as true/false at {row.get('time_seconds')}")
            row["_present"] = present in {"true", "1", "yes"}
            row["_tid"] = tid or None
            row["_time"] = float(row["time_seconds"])
            rows.append(row)
    rows.sort(key=lambda r: r["_time"])
    visible = [r for r in rows if r["_present"]]
    covered = [r for r in visible if r["_tid"] is not None]
    coverage = len(covered) / len(visible) if visible else None
    ids = [r["_tid"] for r in covered]
    changes = sum(a != b for a, b in zip(ids, ids[1:]))
    false_matches = sum((not r["_present"]) and r["_tid"] is not None for r in rows)
    # A gap is a run of annotated-visible samples with no target track ID.
    gaps, current = [], []
    for r in rows:
        if r["_present"] and r["_tid"] is None:
            current.append(r["_time"])
        else:
            if current:
                gaps.append(current)
                current = []
    if current:
        gaps.append(current)
    longest_gap = max((g[-1] - g[0] for g in gaps), default=0.0)
    reacquired = False
    cut_rows = [r for r in rows if r.get("segment") == "celebration" and r["_present"]]
    if cut_rows:
        first = cut_rows[0]
        reacquired = first["_tid"] is not None or any(r["_tid"] is not None for r in cut_rows)
    report = {
        "reviewed_samples": len(rows),
        "target_visible_samples": len(visible),
        "target_frame_coverage": coverage,
        "target_id_changes_between_consecutive_covered_samples": changes,
        "false_matches_on_annotated_absent_samples": false_matches,
        "longest_untracked_visible_gap_seconds": round(longest_gap, 3),
        "reacquired_during_celebration": reacquired if cut_rows else None,
        "important_limit": "Metrics are only as reliable as manual target annotations; inspect IDs visually across broadcast cuts.",
    }
    out_path = review_csv.with_name("identity_metrics.json")
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_detect = sub.add_parser("detect", help="Run detector and create files for manual review")
    p_detect.add_argument("video", type=Path)
    p_detect.add_argument("--out-dir", type=Path, default=Path("tracking_run"))
    p_detect.add_argument("--sample-fps", type=float, default=2.0)
    p_eval = sub.add_parser("evaluate", help="Score manually annotated review CSV")
    p_eval.add_argument("review_csv", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "detect":
            detect(args.video, args.out_dir, args.sample_fps)
        else:
            evaluate(args.review_csv)
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
