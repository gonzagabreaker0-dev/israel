---
name: ai-video-editor-folders
description: The user's editing workflow on their own computer — raw videos go in "Downloads/AI VIDEO EDITOR/RAW", finished edits go in OUTPUT, and edited raws are moved to PROCESSED. Use whenever the user says to edit a video from RAW, check the AI VIDEO EDITOR folder, or "edit my video".
---
# AI VIDEO EDITOR folder workflow

Folder: `~/Downloads/AI VIDEO EDITOR/` (on Windows `%USERPROFILE%\Downloads\AI VIDEO EDITOR\`)

```
AI VIDEO EDITOR/
  RAW/         the user drops new videos here
  OUTPUT/      every finished video goes here
  PROCESSED/   raw videos that have been edited (create it if missing)
```

## Rules
1. **Wait for the user's prompt.** Don't edit anything in RAW until the user says which video and what edit they want. If they don't name a file, list what's in RAW and ask.
2. **Edit with the video skills** (see `superpowers` for which one) using `tools/vid.py` from the `israel` repo. Do intermediate steps in a temp/work folder, not in RAW or OUTPUT.
3. **Never modify or delete the raw file.** Read it, write new files.
4. **Save the finished video to OUTPUT** as `<raw name> - <short edit description>.mp4`, e.g. `coffee-promo - reels captions.mp4`. Never overwrite an existing OUTPUT file; add ` (2)` instead.
5. **Verify before moving anything:** the OUTPUT file exists, `python3 tools/vid.py probe` reads it with a sensible duration, and a few frames (`frames … --n 4`) look right.
6. **Then move the raw** from RAW to PROCESSED (move, not copy; same filename; if the name already exists in PROCESSED, add ` (2)`).
7. **Report:** what was done, the OUTPUT path, the raw's new PROCESSED path, and the before/after duration.

If an edit fails or the user is not happy with it, leave the raw in RAW.
