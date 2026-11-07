---
name: video-use
description: Turn raw footage into a finished video end to end: clean the audio, remove silences, add captions and export for the target platform. Use when the user hands over a raw recording and wants a finished, postable video.
---
# Video-use: raw footage → finished video

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

## Pipeline
1. Inspect: `python3 tools/vid.py probe in.mp4`, then `contact-sheet in.mp4 out/sheet.jpg` and Read the sheet to see what was shot.
2. Clean audio: `audio-clean in.mp4 out/1-clean.mp4` (high-pass, denoise, compression, loudness to -14 LUFS).
3. Remove silences: `silence-cut out/1-clean.mp4 out/2-tight.mp4` (default: gaps over 0.45s quieter than -32 dB).
   Noisy room → `--noise -28`; too choppy → `--min 0.7 --pad 0.15`.
4. Transcribe: `transcribe out/2-tight.mp4` → `.srt`, `.words.json`, `.txt`.
5. Captions: `captions out/2-tight.mp4 out/2-tight.words.json out/3-cap.mp4 --style reel` (word-chunked, popping captions).
6. Export: `export out/3-cap.mp4 out/final-reels.mp4 --preset reels` (or `youtube`, `square`, `tiktok`).

## Check before handing over
- `frames out/final-reels.mp4 out/check --n 6` and Read 2–3 frames: captions legible, not covering faces, inside the safe area.
- Report the before/after duration and the output path.
