# Genuine football-event detection service (T-DEED)

This folder contains a FastAPI adapter for the official [T-DEED implementation](https://github.com/arturxe2/T-DEED), using its SoccerNet Ball Action Spotting checkpoint. The model predicts football events; it is not the frontend's simple frame-difference scan.

## Event classes

The SoccerNet Ball Action Spotting task includes Pass, Drive, Header, High Pass, Out, Cross, Throw In, Shot, Ball Player Block, Player Successful Tackle, Free Kick and Goal. The model can miss events or produce false positives, so review every timestamp.

## 1. Obtain the official pretrained checkpoint

The upstream authors publish trained checkpoints through their [official checkpoint folder](https://drive.google.com/drive/folders/1sxZalU_hCwL8ITZCU9VqSWE8dB94lJty?usp=drive_link). Follow the official repository's instructions and any applicable model/data terms. Download the SoccerNet Ball checkpoint for `SoccerNetBall_challenge1` and place it at:

```
/opt/T-DEED/checkpoints/SoccerNetBall/SoccerNetBall_challenge1/checkpoint_best.pt
```

Do not commit the checkpoint to this Git repository. It is a large binary model file. The service's `/health` endpoint reports `checkpoint_ready: false` until this file exists.

## 2. Build and run

From the repository root:

```bash
docker build -t pitchperfect-tdeed ./backend
docker run --rm -p 8000:8000 \
  -e CORS_ORIGINS="*" \
  -v /absolute/path/to/checkpoint_best.pt:/opt/T-DEED/checkpoints/SoccerNetBall/SoccerNetBall_challenge1/checkpoint_best.pt:ro \
  pitchperfect-tdeed
```

Replace `/absolute/path/to/checkpoint_best.pt` with the actual file path on the machine running Docker. The first image build downloads the official T-DEED source and Python dependencies. CPU inference can be slow for long videos.

Check `http://localhost:8000/health`. `ready` must be `true` before detection is available.

## 3. API

- `GET /health` reports source/checkpoint readiness.
- `POST /api/detect` accepts multipart field `file` and optional query `threshold` (0.01–0.99), returning timestamped predictions.

Example:

```bash
curl -X POST "http://localhost:8000/api/detect?threshold=0.30" \
  -F "file=@football-clip.mp4"
```

The service limits uploads to 500 MB by default, serializes inference because the upstream script writes to a fixed output path, and times out after 15 minutes. Set `MAX_UPLOAD_MB`, `TDEED_THRESHOLD`, `TDEED_MODEL` or `CORS_ORIGINS` as needed. For production, set `CORS_ORIGINS` to the exact origin of the hosted frontend and deploy behind HTTPS with appropriate request limits.

## Limitations and licensing

- This is an integration adapter, not evidence that a trained checkpoint has been loaded or benchmarked in this repository yet.
- The official inference pipeline expects its model checkpoint and its prescribed frame dimensions. The adapter uses 796×448 and the SoccerNet Ball stride of 2 at 25 fps.
- Some model outputs are action classes, not a named-player identity or guaranteed highlight. Named-player tracking and reliable player reframing are separate work.
- The upstream T-DEED repository has its own license and dependencies. Review it before distributing a hosted service or derivative build: https://github.com/arturxe2/T-DEED
