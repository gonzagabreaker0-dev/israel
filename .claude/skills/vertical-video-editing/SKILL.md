---
name: vertical-video-editing
description: Create Reels/TikTok/Shorts with animated word-by-word captions, transitions and effects. Use for any 9:16 social video edit.
---
# Vertical Video Editing (Reels / TikTok / Shorts)

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

## Edit
```bash
V="python3 tools/vid.py"
$V reframe in.mp4 out/v.mp4 --mode crop --x 0.5         # or --mode blur to keep the full frame
$V silence-cut out/v.mp4 out/v2.mp4 --min 0.3 --pad 0.05  # fast pacing
$V transcribe out/v2.mp4
$V captions out/v2.mp4 out/v2.words.json out/v3.mp4 --style karaoke --pos middle --max-words 3
$V export out/v3.mp4 out/reel.mp4 --preset reels
```

## Transitions between clips (ffmpeg xfade)
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v][1:v]xfade=transition=slideup:duration=0.3:offset=<len_a-0.3>[v];[0:a][1:a]acrossfade=d=0.3[a]" \
 -map "[v]" -map "[a]" out/ab.mp4
```
Useful transitions: `slideup`, `smoothleft`, `circleopen`, `zoomin`, `fadeblack`, `wipeleft`.

## Effects
- Punch-in zoom on a beat: `-vf "zoompan=z='if(between(on,30,45),1.15,1)':d=1:s=1080x1920:fps=30"`
- Speed ramp: `-vf setpts=0.5*PTS -af atempo=2.0`

## Rules of thumb
Hook in the first 1.5 s; captions in the middle third, clear of the bottom 20% (platform UI); 20–45 s total; one idea per cut.
