---
name: video-editor
description: Automate the repetitive finishing work on one video or a whole folder: color correction, subtitles and multi-platform exports. Use for batch processing or "make all of these ready to post".
---
# Video Editor: automated color, subtitles and exports

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

## One video, every platform
```bash
V="python3 tools/vid.py"
$V grade in.mp4 out/g.mp4 --look warm --strength 0.7
$V transcribe out/g.mp4
$V captions out/g.mp4 out/g.words.json out/gc.mp4 --style reel
for p in reels youtube square; do $V export out/gc.mp4 out/final-$p.mp4 --preset $p; done
```

## Batch a folder
```bash
for f in footage/*.mp4; do
  n=$(basename "$f" .mp4)
  $V audio-clean "$f" out/$n-a.mp4 && $V grade out/$n-a.mp4 out/$n-g.mp4 --look warm \
  && $V export out/$n-g.mp4 out/$n-reels.mp4 --preset reels
done
```

Pick the look with the **color-grade-ai** skill and the caption style with **caption-clip**. After a batch, build a contact sheet of one output and look at it before reporting success.
