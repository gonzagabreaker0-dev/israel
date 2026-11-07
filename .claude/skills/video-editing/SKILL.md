---
name: video-editing
description: Edit video from plain-English instructions: jump cuts, trims, reordering clips, and subtitles. Use when the user describes edits in everyday words ("cut the first 5 seconds", "make it snappier", "add subtitles").
---
# Video Editing from simple instructions

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

Translate what the user says into toolkit commands. Confirm timestamps by reading the transcript (`transcribe`) or frames (`frames`) when they are vague.

| The user says | Run |
|---|---|
| "cut the first 5 seconds" | `trim in.mp4 out/x.mp4 --start 5` |
| "keep 0:12 to 0:40" | `trim in.mp4 out/x.mp4 --start 0:12 --end 0:40` |
| "remove 1:05–1:20" | `trim in.mp4 out/x.mp4 --keep "0-65,80-<duration>"` |
| "make it snappier / jump cuts" | `silence-cut in.mp4 out/x.mp4 --min 0.3 --pad 0.05` |
| "remove the ums" | use the **cut-video** skill (`fillers`) |
| "put clip B after clip A" | `concat out/x.mp4 a.mp4 b.mp4` |
| "add subtitles" | `transcribe in.mp4` then `captions in.mp4 in.srt out/x.mp4 --style clean` |
| "make it vertical" | `reframe in.mp4 out/x.mp4 --mode blur` |

Chain steps through numbered files (`out/1-...`, `out/2-...`) so any step can be redone. Tell the user what each step changed.
