---
name: video-shotcraft
description: Turn a website or web app into a cinematic product video: scripted scrolling, zooms and clicks recorded in a headless browser, then graded, scored and captioned. Use for product demos and launch videos of a URL.
---
# Video Shotcraft: website → cinematic product video

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

## 1. Capture shots
`scripts/capture.mjs` (in this skill folder) opens a URL in Playwright's Chromium and records a smooth, eased scroll at 2x scale:
```bash
node .claude/skills/video-shotcraft/scripts/capture.mjs https://example.com out/shot1.webm --w 1080 --h 1920 --dur 8
```
Record one short shot per idea (hero, feature, pricing, CTA). For clicks or typing, copy the script and add `page.click()` / `page.keyboard.type()` between the scroll steps, with pauses.

## 2. Make it cinematic
```bash
V="python3 tools/vid.py"
$V concat out/rough.mp4 out/shot1.webm out/shot2.webm out/shot3.webm
$V grade out/rough.mp4 out/graded.mp4 --look punchy --strength 0.6
$V music out/graded.mp4 music.mp3 out/scored.mp4 --music-db -10
```
- Add a title card and end card with the **hyperframes** skill.
- Add captions or callouts with **caption-clip**.
- Keep each shot 2–5 s; open on the strongest visual.
