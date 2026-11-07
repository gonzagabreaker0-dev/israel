---
name: broll-overlay
description: Add relevant B-roll over a talking-head video at the right moments, full screen or picture-in-picture, matched to what is being said. Use when a talking-head video needs cutaways.
---
# B-Roll Overlay

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

1. Transcribe the talking head: `python3 tools/vid.py transcribe talk.mp4`, Read `talk.txt`.
2. Mark B-roll moments: concrete nouns or actions the viewer could see ("espresso machine", "our app's dashboard"), every 5–10 s, 2–4 s each. Never cover the first 2 s (the hook) or an emotional moment where the face matters.
3. Source B-roll from the user's footage, renders from **motion-graphics** / **hyperframes**, or screen captures from **video-shotcraft**.
4. Apply each overlay in turn (audio stays from the talking head):
   ```bash
   V="python3 tools/vid.py"
   $V broll talk.mp4 broll/machine.mp4 out/b1.mp4 --at 6.2 --dur 3
   $V broll out/b1.mp4 broll/app.mp4 out/b2.mp4 --at 14.0 --dur 2.5
   $V broll out/b2.mp4 broll/chart.mp4 out/b3.mp4 --at 21.5 --dur 3 --pip   # picture-in-picture corner
   ```
5. Spot-check with `frames out/b3.mp4 out/chk --n 8`.
