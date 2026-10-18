# Reproducible backend setup

## Current status

- T-DEED source is pinned to immutable upstream commit `d953b4de8a2ad941c565e1683c5b07255cbe644e`.
- Python dependencies and CPU PyTorch versions are pinned.
- The API health endpoint distinguishes source readiness from checkpoint readiness.
- **Pretrained model weights are not included or yet verified in this repository.** Do not describe football-event inference as validated until the checkpoint is acquired from the official source and tested on representative labelled footage.
- Player tracking returns anonymous IDs, not named-player recognition.

## Requirements

- Docker Desktop (or Docker Engine + Compose)
- A compatible official T-DEED SoccerNet Ball Action Spotting checkpoint named `checkpoint_best.pt`
- A compatible Ultralytics person-detection weights file at `backend/models/yolo-person.pt`

The upstream code and checkpoint information are documented in the [official T-DEED repository](https://github.com/arturxe2/T-DEED). The upstream README links its official checkpoint folder: [T-DEED checkpoints](https://drive.google.com/drive/folders/1sxZalU_hCwL8ITZCU9VqSWE8dB94lJty?usp=drive_link). The expected model name is `SoccerNetBall_challenge1`; the checkpoint must match the pinned source/configuration. Do not use a random checkpoint from another task. Review upstream licensing/terms.

## Configure and start

From the `backend` directory:

1. Copy `.env.example` to `.env` and set `CORS_ORIGINS` to the frontend origin.
2. Create `backend/models/SoccerNetBall_challenge1/` and place the verified upstream `checkpoint_best.pt` inside it.
3. Place the compatible person detector at `backend/models/yolo-person.pt`.
4. Build and start:

```bash
docker compose up --build
```

5. Check `http://localhost:8000/health` and `http://localhost:8000/api/tracking/health`. HTTP 200 means the API is responding; it does not guarantee model readiness.

The Docker image fetches the pinned T-DEED revision and applies the CPU-inference patch during build. Model artifacts are mounted separately under `/models`, so they do not overwrite the patched source tree.

## Tests and validation

Run the backend smoke tests in the image:

```bash
docker compose exec pitchperfect-ai python -m pytest -q /app/tests
```

These tests validate API health contracts only; they do not prove model accuracy. For real inference validation, run a short representative football clip with a known ground-truth event list, compare predicted timestamps and classes, and record false positives, missed events, and per-class precision/recall.

## Player-selection limits

The tracker returns anonymous track IDs and bounding boxes. IDs can switch after occlusion or broadcast cuts. They are not named-player identity. Confirm a selected player visually before associating that track with a detected football event.
