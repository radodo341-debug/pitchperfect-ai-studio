from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

APP_DIR = Path(__file__).resolve().parent
TDEED_DIR = Path(os.getenv("TDEED_DIR", "/opt/T-DEED")).resolve()
MODEL_NAME = os.getenv("TDEED_MODEL", "SoccerNetBall_challenge1")
THRESHOLD_DEFAULT = float(os.getenv("TDEED_THRESHOLD", "0.30"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "500")) * 1024 * 1024
DEFAULT_CHECKPOINT = TDEED_DIR / "checkpoints" / "SoccerNetBall" / MODEL_NAME / "checkpoint_best.pt"
CHECKPOINT = Path(os.getenv("TDEED_CHECKPOINT_PATH", str(DEFAULT_CHECKPOINT))).resolve()
ALLOWED_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}

app = FastAPI(title="PitchPerfect Football Event Detection", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
inference_lock = asyncio.Lock()


def _download_checkpoint() -> None:
    """Download a trusted, direct HTTPS checkpoint URL configured by the service owner."""
    import urllib.request

    url = os.getenv("TDEED_CHECKPOINT_URL", "").strip()
    if CHECKPOINT.is_file() or not url:
        return
    if not url.startswith("https://"):
        raise RuntimeError("TDEED_CHECKPOINT_URL must be a direct HTTPS download URL.")
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    partial = CHECKPOINT.with_suffix(".pt.part")
    request = urllib.request.Request(url, headers={"User-Agent": "PitchPerfect-TDEED/0.2"})
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 2 * 1024 * 1024 * 1024:
                    raise RuntimeError("Checkpoint download exceeded the 2 GB safety limit.")
                output.write(chunk)
        with partial.open("rb") as downloaded:
            signature = downloaded.read(8)
        if total < 1024 * 1024 or not (signature.startswith(b"PK") or signature.startswith(b"\\x80")):
            raise RuntimeError("Checkpoint URL did not return a recognizable PyTorch checkpoint file.")
        partial.replace(CHECKPOINT)
    finally:
        partial.unlink(missing_ok=True)


@app.on_event("startup")
async def schedule_checkpoint_download() -> None:
    if os.getenv("TDEED_CHECKPOINT_URL", "").strip() and not CHECKPOINT.is_file():
        asyncio.create_task(asyncio.to_thread(_download_checkpoint))


def model_status() -> dict[str, Any]:
    source_ready = (TDEED_DIR / "inference.py").is_file()
    return {
        "service": "PitchPerfect T-DEED adapter",
        "model": MODEL_NAME,
        "model_family": "T-DEED / SoccerNet Ball Action Spotting",
        "source_ready": source_ready,
        "checkpoint_ready": CHECKPOINT.is_file(),
        "ready": source_ready and CHECKPOINT.is_file(),
        "checkpoint_path": str(CHECKPOINT),
        "events": [
            "Pass", "Drive", "Header", "High Pass", "Out", "Cross",
            "Throw In", "Shot", "Ball Player Block", "Player Successful Tackle",
            "Free Kick", "Goal"
        ],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return model_status()


@app.post("/api/detect")
async def detect(file: UploadFile = File(...), threshold: float = THRESHOLD_DEFAULT):
    status = model_status()
    if not status["source_ready"]:
        raise HTTPException(status_code=503, detail="Pinned T-DEED source is missing from the server image.")
    if not status["checkpoint_ready"]:
        raise HTTPException(
            status_code=503,
            detail=(
                "The T-DEED source is installed, but its pretrained checkpoint is missing. "
                f"Place the verified SoccerNet Ball checkpoint at {CHECKPOINT}; see backend/SETUP.md."
            ),
        )
    if not 0.01 <= threshold <= 0.99:
        raise HTTPException(status_code=400, detail="threshold must be between 0.01 and 0.99")

    suffix = Path(file.filename or "upload.mp4").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload an MP4, MOV, MKV, WebM or M4V video.")

    with tempfile.TemporaryDirectory(prefix="pitchperfect-") as temp_dir:
        temp_path = Path(temp_dir)
        video_path = temp_path / ("input" + suffix)
        size = 0
        with video_path.open("wb") as target:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"Video exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
                target.write(chunk)
        await file.close()
        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded video is empty.")

        # Use the uploaded file's actual frame rate for timestamps rather than assuming 25 fps.
        fps = 25.0
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                measured_fps = cap.get(cv2.CAP_PROP_FPS)
                if measured_fps and 1 <= measured_fps <= 240:
                    fps = float(measured_fps)
            cap.release()
        except ImportError:
            pass

        async with inference_lock:
            output_dir = TDEED_DIR / "inference_output"
            output_file = output_dir / "results_inference.json"
            if output_file.exists():
                output_file.unlink()
            command = [
                "python", "inference.py",
                "--model", MODEL_NAME,
                "--video_path", str(video_path),
                "--frame_width", "796",
                "--frame_height", "448",
                "--inference_threshold", str(threshold),
            ]
            started = time.time()
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(TDEED_DIR),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=900)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise HTTPException(status_code=504, detail="T-DEED inference timed out after 15 minutes.")
            log_tail = (stdout or b"").decode("utf-8", errors="replace")[-5000:]
            if process.returncode != 0:
                raise HTTPException(status_code=500, detail="T-DEED inference failed: " + log_tail[-1500:])
            if not output_file.exists():
                raise HTTPException(status_code=500, detail="T-DEED finished without producing results_inference.json. " + log_tail[-1000:])
            try:
                raw = json.loads(output_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise HTTPException(status_code=500, detail=f"Could not read model predictions: {exc}")
            finally:
                output_file.unlink(missing_ok=True)

            # Upstream T-DEED writes {predictions: [{frame, label, confidence}, ...]}.
            events = []
            for item in raw.get("predictions", []):
                frame = int(item.get("frame", 0))
                confidence = float(item.get("confidence", item.get("score", 0)))
                events.append({
                    "label": str(item.get("label", "Unknown")),
                    "time_seconds": round(frame / fps, 3),
                    "frame": frame,
                    "confidence": round(confidence, 4),
                    "source": "T-DEED SoccerNet Ball Action Spotting",
                })
            return JSONResponse({
                "model": MODEL_NAME,
                "model_family": "T-DEED",
                "duration_seconds": round(time.time() - started, 2),
                "threshold": threshold,
                "events": events,
                "warning": "Model confidence is not a guarantee. Review every suggested timestamp before editing.",
            })


@app.get("/api/tracking/health")
def tracking_health() -> dict[str, Any]:
    """Report whether an optional player tracking model is configured."""
    from player_tracking import tracking_status
    return tracking_status()


@app.post("/api/track")
async def track_players(file: UploadFile = File(...), sample_fps: float = 2.0):
    """Return anonymous person tracks from a match; does not identify player names."""
    from player_tracking import sample_video
    if not 0.2 <= sample_fps <= 5:
        raise HTTPException(status_code=400, detail="sample_fps must be between 0.2 and 5")
    suffix = Path(file.filename or "upload.mp4").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload an MP4, MOV, MKV, WebM or M4V video.")
    with tempfile.TemporaryDirectory(prefix="pitchperfect-track-") as temp_dir:
        video_path = Path(temp_dir) / ("input" + suffix)
        size = 0
        with video_path.open("wb") as target:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"Video exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
                target.write(chunk)
        await file.close()
        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded video is empty.")
        try:
            detections = await asyncio.to_thread(sample_video, str(video_path), sample_fps)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        tracks: dict[str, dict[str, Any]] = {}
        for detection in detections:
            track_id = detection.get("track_id")
            if track_id is None:
                continue
            key = str(track_id)
            item = tracks.setdefault(key, {"track_id": track_id, "first_seen_seconds": detection["time_seconds"], "last_seen_seconds": detection["time_seconds"], "detections": 0, "identity_status": "unresolved"})
            item["last_seen_seconds"] = detection["time_seconds"]
            item["detections"] += 1
        return JSONResponse({
            "provider": "Ultralytics YOLO + ByteTrack",
            "sample_fps": sample_fps,
            "detection_count": len(detections),
            "tracks": list(tracks.values()),
            "detections": detections,
            "warning": "Track IDs are anonymous and may change after cuts or occlusion. They are not named-player identity. Confirm the player before connecting tracks to football events.",
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
