---
name: video-trimmer
description: Cut videos to exact timestamps, keep several ranges, or split into parts. Use when the user gives precise times like 0:12–0:47.
---
# Video Trimmer: exact timestamps

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

Timestamps take seconds (`83.5`), `m:ss` (`1:23.5`) or `h:mm:ss`.

- One range: `python3 tools/vid.py trim in.mp4 out/part.mp4 --start 1:02 --end 1:47`
- Several ranges joined: `trim in.mp4 out/edit.mp4 --keep "0:05-0:31,1:10-1:42,2:00-2:15"`
- Several ranges as separate files: `clips in.mp4 out/parts --ranges "0:05-0:31,1:10-1:42"`

Trims re-encode, so they are frame-accurate (no keyframe snapping). Check the cut points with
`frames out/part.mp4 out/chk --n 2` if the user cares about the exact first and last frame.
