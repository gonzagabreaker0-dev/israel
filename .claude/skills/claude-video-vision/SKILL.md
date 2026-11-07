---
name: claude-video-vision
description: Let Claude watch a video by sampling frames and contact sheets, then critique it and suggest concrete improvements. Use when the user asks for feedback on a video or what to improve.
---
# Claude Video Vision: watch and suggest improvements

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

Claude sees images, not video, so sample the video into images and Read them.

1. Overview: `python3 tools/vid.py contact-sheet in.mp4 out/sheet.jpg --n 20 --cols 5`, Read it.
2. Detail: `frames in.mp4 out/frames --scenes` (one frame per shot) or `--n 16` evenly; Read the important ones.
3. Audio/words: `transcribe in.mp4`, Read the `.txt`.
4. Pacing: `scenes in.mp4` (shot lengths).

## Feedback format
Give timestamped, actionable notes, most impactful first:
- **Hook (0–3 s):** does it grab? What to open on instead.
- **Pacing:** shots that drag (> 5 s without change), dead air.
- **Framing & image:** headroom, exposure, color consistency, text safe areas.
- **Captions & text:** readability, typos, timing.
- **Audio:** levels, noise, music vs voice.
- **Ending/CTA.**
Offer to apply the fixes with the matching skills.
