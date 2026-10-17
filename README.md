# PitchPerfect AI Studio

A browser-first football highlight editor for creators making YouTube Shorts, TikTok, Instagram Reels and landscape highlight videos.

## Free-first hosting plan

The goal is to keep hosting costs at £0. The frontend can be published as a static site with GitHub Pages from this public repository. GitHub Pages does not run Python or PyTorch backend services, so it cannot host the T-DEED inference API.

## Current prototype

- Local video upload and browser preview (MP4, MOV, WebM)
- Start/end trim points and set-to-playhead controls
- 9:16, 16:9 and 1:1 output framing
- Playback speed controls
- Optional T-DEED / SoccerNet Ball Action Spotting inference-service connection for timestamped football-event predictions
- Experimental local frame-difference scan as a fallback; this is not semantic football-event detection
- MP4 export using FFmpeg WebAssembly, loaded on demand
- Responsive UI and Playwright smoke tests on GitHub Actions

## Genuine football-event model

The `backend/` folder contains a FastAPI adapter for the official [T-DEED implementation](https://github.com/arturxe2/T-DEED) and its SoccerNet Ball Action Spotting model. It is intended to return timestamped predictions for classes such as Goal, Shot, Header, Cross and Player Successful Tackle.

**The pretrained checkpoint is not included, and the inference API is not hosted.** The official checkpoint folder is available from the [upstream authors](https://drive.google.com/drive/folders/1sxZalU_hCwL8ITZCU9VqSWE8dB94lJty?usp=drive_link). Follow the upstream model and dataset terms. Until a compatible checkpoint is installed and the model service is running, genuine event detection is unavailable.

The editor's **Football AI Service URL** field must point to a backend whose `/health` endpoint reports `ready: true`. Clicking **Detect football events** uploads the selected video to that service. Only enter a service URL you trust. Model predictions can be wrong and need review.

## Publish the static frontend for free

1. Open this repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Choose branch `main` and folder `/(root)`, then save.
5. Wait for GitHub to publish the site and use the URL shown in the Pages settings.

GitHub Pages only serves static website files. It does not run the Python/PyTorch API. Keep this as a free project/demo deployment and check GitHub Pages' usage terms if the project becomes a commercial SaaS.

## What can run at £0

Browser-based editing and export can work without a separate server, subject to browser memory and device performance. The AI service can be tested in a free interactive compute environment, but that is not reliable permanent hosting: free sessions may disconnect and compute availability can change. Do not use a temporary notebook as a public production API or promise that football AI detection is always online.

## Run browser tests

Requires Node.js 20 or newer:

```bash
npm install
npx playwright install --with-deps chromium
npm run test:e2e
```

GitHub Actions runs browser tests and checks Python syntax on pushes to `main`, pull requests, and manual workflow dispatch.

## Limitations

- This is an early editor foundation, not a complete professional editor.
- The local frame-difference scan only suggests visually active timestamps; it does not identify event semantics.
- T-DEED integration code is committed, but the checkpoint, deployment and real-video inference have not been verified.
- FFmpeg WebAssembly runs in the browser. Large videos may exceed browser memory limits; short clips are recommended. The first export needs a network connection to load the engine.
- Named-player identity, reliable player tracking, beat detection and a full multitrack timeline are not implemented yet.

## Model references

- [T-DEED official implementation and inference instructions](https://github.com/arturxe2/T-DEED)
- [SoccerNet action spotting benchmark](https://github.com/SoccerNet/sn-spotting)
- [SoccerNet team/ball action spotting benchmark](https://github.com/SoccerNet/sn-teamspotting)

Review upstream licenses, checkpoint terms and dataset access requirements before deploying or redistributing model components.
