---
name: clipify
description: Turn one long video (podcast, webinar, stream) into multiple short clips automatically. Use when the user wants many shorts cut from a long recording.
---
# Clipify: long video → many short clips

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.  Needs `pip install faster-whisper`.

1. `python3 tools/vid.py transcribe long.mp4` → `long.txt` with timestamps.
2. Read `long.txt` and choose 3–10 segments that each stand alone: 20–60 s, a complete thought, starts on a strong line, ends on a payoff. Use the scoring rubric in **claude-shorts**.
3. Cut them, vertical:
   `clips long.mp4 out/clips --ranges "312-351,605-640,1210-1262" --vertical --mode crop`
4. Caption each:
   ```bash
   for c in out/clips/clip*.mp4; do
     python3 tools/vid.py transcribe "$c"
     python3 tools/vid.py captions "$c" "${c%.mp4}.words.json" "${c%.mp4}-cap.mp4" --style karaoke --pos middle
   done
   ```
5. Deliver a table: clip file, time range, hook line, suggested title.
