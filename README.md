# PitchPerfect AI Studio

A browser-first football highlight editor for creators making YouTube Shorts, TikTok, Instagram Reels and landscape highlight videos.

## Current prototype

- Local video upload and browser preview (MP4, MOV, WebM)
- Start/end trim points and set-to-playhead controls
- 9:16, 16:9 and 1:1 output framing
- Playback speed controls
- Experimental local frame-difference scan that suggests high-motion moments
- MP4 export using FFmpeg WebAssembly, loaded on demand
- Responsive UI and Playwright smoke tests on GitHub Actions

## Run the browser tests

Requires Node.js 20 or newer:

```bash
npm install
npx playwright install --with-deps chromium
npm run test:e2e
```

GitHub Actions runs the browser tests on pushes to `main`, pull requests, and manual workflow dispatch.

## GitHub Pages

This is a static site and can be hosted from the repository root using GitHub Pages. In repository settings, open **Pages**, select **Deploy from a branch**, choose `main` and `/(root)`, then save. The deployed page will be available at the URL GitHub Pages reports.

## Important limitations

This is an early editor foundation, not a complete professional editor. The activity scan compares sampled frames and **does not classify goals, tackles, saves, players or named identities**. It can suggest visually active timestamps but should not label them as verified football events.

A real event detector needs a compatible trained model and its weights, plus evaluation on representative football footage. SoccerNet provides research benchmarks and baselines: https://github.com/SoccerNet/sn-spotting and https://github.com/SoccerNet/sn-teamspotting. Review their dataset access, licenses and model requirements before integrating any checkpoint.

Rendering uses FFmpeg WebAssembly in the browser. Large videos may exceed browser memory limits; short clips are recommended. The first export needs a network connection to load the engine. This prototype does not upload source footage to an application server.

## Next milestones

1. Run and stabilize browser tests against real sample videos in desktop and mobile Chromium.
2. Add a model-backed football-event detection pipeline with confidence scores and timestamps.
3. Add editable timeline tracks, captions, beat analysis and more reliable audio handling.
4. Evaluate exports for audio/no-audio files, long inputs, rotation metadata and different browsers.
