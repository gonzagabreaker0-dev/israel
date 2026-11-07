# Israel Digital Solutions — Coffee House · 60s Cinematic Reel

A one-minute 3D reel built with **Three.js**: procedural geometry and lighting, with no stock footage. Every frame depends only on time `t`, so the same code plays live in the browser and renders frame-accurate MP4.

Format: **1080×1920 (9:16)**, 30 fps, 60 s. It fits Instagram Reels, TikTok and YouTube Shorts. A 16:9 cut is one command away.

## Shot list

| Time | Shot | Camera | Caption | Transition out |
|---|---|---|---|---|
| 0–9s | **Intro**: a vortex of coffee beans in the dark, warm key light and brand-blue rim light | Spirals down through the vortex, then whip-pans | *Israel Digital Solutions / Coffee House* | Warm flash + motion blur |
| 9–19s | **The Bean**: a slow-motion hero bean falls onto a glowing roast pile with embers | Follow-cam locked to the falling bean, then pulls back to reveal the pile | *01 — Hand-picked. Fresh roasted.* | Dip to black + light leak |
| 19–31s | **The Shot**: espresso machine, double-spout pour, rising crema, steam, brand-blue LED | Close on the spouts, cranes down the stream, orbits the cup, then dives into the cup | *02 — Pulled to perfection* | Dive match-cut + whip blur |
| 31–41s | **The Craft**: overhead milk pour; the rosetta blooms and is pulled into a heart | Overhead spiral, then tilts to a hero 3/4 view | *03 — Every cup, a little art* | Light-leak sweep |
| 41–51s | **The Ritual**: the cup slides down the bar past pendant lamps, a laptop, IDS house-blend bags and the neon sign | Tracking follow-cam with a little lag, then a push-in on the sign | *04 — Your daily ritual* | Dip to black |
| 51–60s | **Outro**: the brand cube (from `logo.svg`) spins in and settles; rings, orbiting beans, steam | Slow push-in | *Israel Digital Solutions · Coffee · Code · Community · VISIT US TODAY* | Fade out |

Finishing layers: Unreal bloom, ACES tone mapping, film grain, vignette, dust motes, bokeh, word-by-word mask-reveal captions (Playfair Display + Inter), and a brand bug at the top of the frame.

## Run it

```bash
npm install
npm run serve            # open http://localhost:8080 and tap to play (space = play/pause, scrub bar)
```

## Render the video

```bash
npm run render           # out/reel-1080x1920.mp4
npm run render:landscape # out/reel-1920x1080.mp4
npm run stills           # preview JPEGs in out/
node render.mjs --from 19 --to 31   # re-render one shot
```

Rendering needs `ffmpeg` and Playwright's Chromium. It drives `window.REEL.renderAt(t)` frame by frame and pipes the frames into x264.

## Editing

- **Captions and timing:** `CAPTIONS` in `reel.js`
- **Transitions:** `updateFX()` (flashes, dips, blur, light leak)
- **Shots:** each `shot('name', start, end, ...)` block owns its scene, lights and camera move
- **Brand colors:** CSS variables in `index.html` and the neon/cube canvases in `reel.js`

The video is silent. Add a track in your editor or in the app when you post (trending audio usually performs best), or mux one in:
`ffmpeg -i out/reel-1080x1920.mp4 -i music.mp3 -shortest -c:v copy -c:a aac out/reel-with-music.mp4`

## Video skills (Claude Code)

`.claude/skills/` holds 30 video skills that Claude Code loads automatically in this repo: editing, motion graphics, Shorts, analysis and captions, color/audio/AI generation, and full workflows. Start with `superpowers`, which says which skill fits which job.

They run on `tools/vid.py`, an ffmpeg toolkit (`python3 tools/vid.py -h`):

```bash
python3 tools/vid.py silence-cut raw.mp4 out/tight.mp4        # remove pauses
python3 tools/vid.py transcribe out/tight.mp4                  # .srt + word timings (pip install faster-whisper)
python3 tools/vid.py captions out/tight.mp4 out/tight.words.json out/cap.mp4 --style karaoke
python3 tools/vid.py reframe in.mp4 out/vertical.mp4 --mode blur
python3 tools/vid.py grade in.mp4 out/graded.mp4 --look warm --strength 0.7
python3 tools/vid.py export out/cap.mp4 out/final.mp4 --preset reels
```

The AI-generation skills (`pexo-agent`, `higgsfield-skills`, `kling-ai-skills`) cover planning, prompting and assembly. Generating clips needs your own account and API key with those providers.
