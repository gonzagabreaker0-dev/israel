---
name: shorts-video-creator
description: Reframe horizontal 16:9 video into vertical 9:16 Shorts/Reels, with crop, blurred background or letterbox, and subject positioning. Use when converting landscape video to vertical.
---
# Shorts Video Creator: horizontal → vertical

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

Three framing modes:
- `--mode crop` fills the frame by cropping. `--x` sets where to crop horizontally (0 = left, 0.5 = center, 1 = right).
- `--mode blur` keeps the whole shot, centered over a blurred zoomed copy. Safe for screen recordings and wide shots.
- `--mode fit` keeps the whole shot with black bars.

```bash
python3 tools/vid.py reframe in.mp4 out/vertical.mp4 --mode crop --x 0.35
```

Find the subject first: `frames in.mp4 out/f --n 6`, Read the frames and estimate where the speaker sits horizontally; use that as `--x`.
If the subject moves, split into ranges with `trim` and reframe each with its own `--x`, then `concat`.
Finish with `export … --preset shorts`. Shorts must be ≤ 60 s for the classic Shorts shelf; check with `probe`.
