# PitchPerfect AI Studio

A browser-first football highlight editor for creators making YouTube Shorts, TikTok, Instagram Reels and landscape highlight videos.

## Current prototype

- Local video upload and browser preview (MP4, MOV, WebM)
- Start/end trim points and set-to-playhead controls
- 9:16, 16:9 and 1:1 output framing
- Playback speed controls
- Optional **T-DEED / SoccerNet Ball Action Spotting** inference-service connection for timestamped football-event predictions
- Experimental local frame-difference scan as a fallback; this is not semantic football-event detection
- MP4 export using FFmpeg WebAssembly, loaded on demand
- Responsive UI and Playwright smoke tests on GitHub Actions

## Genuine football-event model

The `backend/` folder contains a FastAPI adapter for the official [T-DEED implementation](https://github.com/arturxe2/T-DEED) and its SoccerNet Ball Action Spotting model. It can return timestamped predictions for classes such as Goal, Shot, Header, Cross and Player Successful Tackle.

**The pretrained checkpoint is not included in this repository and the inference service is not yet hosted.** Obtain the checkpoint through the upstream authors' [official checkpoint folder](https://drive.google.com/drive/folders/1sxZalU_hCwL8ITZCU9VqSWE8dB94lJty?usp=drive_link), follow the upstream model/data terms, and follow the setup in [backend/README.md](backend/README.md). Until a compatible checkpoint is installed, the backend health endpoint will report that the model is not ready.

The frontend's **Football AI Service URL** field must point to a deployed backend that reports `ready: true` from `/health`. Clicking **Detect football events** sends the selected video to that service. Only enter a service URL you trust. Model predictions can be wrong and need review.

## Run browser tests

Requires Node.js 20 or newer:

```bash
npm install
npx playwright install --with-deps chromium
npm run test:e2e
```

GitHub Actions runs browser tests and checks Python syntax on pushes to `main`, pull requests, and manual workflow dispatch.

## GitHub Pages

The frontend is a static site and can be hosted from the repository root using GitHub Pages. In repository settings, open **Pages**, select **Deploy from a branch**, choose `main` and `/(root)`, then save. The deployed page will be available at the URL GitHub Pages reports.

GitHub Pages only hosts the frontend; it does not run the Python/PyTorch inference service. Deploy the backend separately and use its HTTPS URL in the editor.

## Limitations

- This is an early editor foundation, not a complete professional editor.
- The local frame-difference scan only suggests visually active timestamps; it does not identify event semantics.
- The T-DEED integration code is committed, but a checkpoint must be installed and the backend must be deployed before genuine model inference is available to the website.
- Rendering uses FFmpeg WebAssembly in the browser. Large videos may exceed browser memory limits; short clips are recommended. The first export needs a network connection to load the engine.
- Named-player identity, reliable player tracking, beat detection and a full multitrack timeline are not implemented yet.

## Model references

- [T-DEED official implementation and inference instructions](https://github.com/arturxe2/T-DEED)
- [SoccerNet action spotting benchmark](https://github.com/SoccerNet/sn-spotting)
- [SoccerNet team/ball action spotting benchmark](https://github.com/SoccerNet/sn-teamspotting)

Review upstream licenses, checkpoint terms and dataset access requirements before deploying or redistributing model components.
