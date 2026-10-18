"""Optional player detection and short-term tracking for PitchPerfect AI.

Requires the Ultralytics package and a person-detection model configured with
PP_TRACKER_MODEL. Tracks are anonymous IDs, not named-player recognition.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2


def tracking_status() -> dict[str, Any]:
    model_path = os.getenv("PP_TRACKER_MODEL", "").strip()
    return {
        "component": "player-detection-tracking",
        "provider": "Ultralytics YOLO tracking",
        "configured": bool(model_path),
        "model_exists": bool(model_path and Path(model_path).is_file()),
        "identity_mode": "anonymous track IDs; named-player identity requires user confirmation",
    }


def sample_video(video_path: str, sample_fps: float = 2.0, max_seconds: float = 5400) -> list[dict[str, Any]]:
    """Return person detections and tracker IDs at sampled frames.

    This function intentionally raises a clear error if the model is unavailable.
    It never guesses a real player's name from a detection or kit colour.
    """
    if not 0.2 <= sample_fps <= 5:
        raise ValueError("sample_fps must be between 0.2 and 5")
    model_path = os.getenv("PP_TRACKER_MODEL", "").strip()
    if not model_path or not Path(model_path).is_file():
        raise RuntimeError("Player tracker model is not configured. Set PP_TRACKER_MODEL to a supported YOLO weights file.")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Player tracking dependency is missing; install the backend tracking requirements.") from exc

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open the uploaded video.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = min(frame_count / fps if frame_count else 0, max_seconds)
    stride = max(1, round(fps / sample_fps))
    model = YOLO(model_path)
    results: list[dict[str, Any]] = []
    frame_index = 0
    try:
        while frame_index / fps <= duration:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % stride == 0:
                tracked = model.track(frame, persist=True, classes=[0], tracker="bytetrack.yaml", verbose=False)
                if tracked:
                    boxes = tracked[0].boxes
                    if boxes is not None:
                        xyxy = boxes.xyxy.cpu().tolist()
                        confs = boxes.conf.cpu().tolist()
                        ids = boxes.id.int().cpu().tolist() if boxes.id is not None else [None] * len(xyxy)
                        for box, confidence, track_id in zip(xyxy, confs, ids):
                            results.append({
                                "time_seconds": round(frame_index / fps, 3),
                                "frame": frame_index,
                                "track_id": int(track_id) if track_id is not None else None,
                                "bbox_xyxy": [round(float(v), 2) for v in box],
                                "confidence": round(float(confidence), 4),
                                "class": "person",
                                "identity_status": "unresolved",
                            })
            frame_index += 1
    finally:
        cap.release()
    return results
