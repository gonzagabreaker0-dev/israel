---
name: cut-video
description: Remove awkward pauses and filler words (um, uh, like, you know) from talking-head videos, Tella-style. Use for cleaning up talking-head, tutorial, or webcam recordings.
---
# Cut Video: remove pauses and filler words

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.
Needs `pip install faster-whisper` (word timestamps).

```bash
python3 tools/vid.py fillers in.mp4 out/clean.mp4
```
This transcribes with word timings, cuts every filler word and every pause over 0.45 s, and joins the rest.

Tuning:
- Custom filler list: `--words "um,uh,you know,so basically"`. Leave out "like" or "actually" if the speaker uses them meaningfully.
- Pauses: `--min-silence 0.6` keeps more breathing room; `--pad 0.1` softens cuts.
- Non-English speech: `--lang es` (or the right code).
- Better accuracy on long footage: `--model medium`.

Afterwards run `transcribe out/clean.mp4` and skim the `.txt`; if a word was clipped, raise `--pad`.
Report seconds removed (the command prints it).
