# Reproducible backend setup

## What this setup does (and does not do)

This pins the Python API/tracking dependencies and provides a Docker image, environment template, health checks and smoke tests. It **does not bundle model weights**. Weights are large binary artifacts and must be obtained from trusted upstream sources, checked against the expected model/task, and mounted locally. Do not commit weights to Git.

## Requirements

- Docker Desktop (or Docker Engine + Compose)
- Official T-DEED source checkout at `backend/T-DEED/` (or mount it at `/opt/T-DEED`)
- A compatible SoccerNet Ball Action Spotting checkpoint named `checkpoint_best.pt`
- A compatible Ultralytics person-detection weights file at `backend/models/yolo-person.pt`

Use the upstream [T-DEED repository](https://github.com/arturxe2/T-DEED) and its official [checkpoint folder](https://drive.google.com/drive/folders/1sxZalU_hCwL8ITZCU9VqSWE8dB94lJty?usp=drive_link). Verify the checkpoint is for `SoccerNetBall_challenge1` and follow the upstream licence/terms. The service must not report model-ready until both upstream source and checkpoint exist.

## Start

From the `backend` directory:

1. Copy `.env.example` to `.env` and adjust `CORS_ORIGINS` for the frontend origin.
2. Place the T-DEED checkout in `backend/T-DEED/`.
3. Place the approved tracking weights in `backend/models/yolo-person.pt`.
4. Build and start:

```bash
docker compose up --build
```

5. Open `http://localhost:8000/health` and `http://localhost:8000/api/tracking/health`. Readiness is component-specific; HTTP 200 alone does not mean the model is ready.

For source checkouts where T-DEED is stored elsewhere, update the `TDEED_DIR` mount in Compose and the matching environment value. This image intentionally does not silently download or execute arbitrary upstream code during startup.

## Test

```bash
docker compose exec pitchperfect-ai python -m pytest -q /app/tests
```

The tests check health response contracts, not model accuracy. After configuring weights, run inference on a labelled, representative football clip and manually compare predicted timestamps to ground truth. Record false positives, missed events and per-class precision/recall before describing event detection as validated.

## Player selection and identity limits

The tracker returns anonymous track IDs and bounding boxes. A user must select a visible detection at a timestamp; the selected ID can then be used as a short-term tracking target. IDs can switch after occlusion or broadcast cuts. This is not named-player recognition. Never claim a selected ID is a known footballer without separate evidence (for example, a user-confirmed reference frame or jersey-number workflow).
