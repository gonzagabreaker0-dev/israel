---
name: thumbnail-skills
description: Create branded YouTube thumbnails and video covers: a strong frame, a big short hook, high contrast. Use for thumbnails, Reels covers and video cover images.
---
# Thumbnail Skills

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

## Quick thumbnail from a frame
1. Find a strong frame: `python3 tools/vid.py frames in.mp4 out/cands --n 12`, Read them, pick an expressive face or the clearest product shot.
2. `thumbnail in.mp4 out/thumb.jpg --at 12.4 --text "3X FASTER"` (1280x720). Reels cover: `--w 1080 --h 1920`.
   Colors: `--color "#FFE600"` (default yellow), white or brand blue. Custom font: `--fontfile path.ttf`.

## Designed thumbnail (more control)
Write a 1280x720 HTML page (frame as background image, bold text, arrow/circle, logo) and screenshot it:
```bash
node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});await p.goto('file://'+process.cwd()+'/thumb.html');await p.screenshot({path:'out/thumb.png'});await b.close()})()"
```

## Rules
- 2–4 words maximum; never repeat the title.
- Readable at 160 px wide: check by scaling down and reading it.
- One focal point, high contrast, faces showing emotion work best.
- Make 2–3 variants for A/B testing.
