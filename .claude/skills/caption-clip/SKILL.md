---
name: caption-clip
description: Generate subtitles for a video and burn them in, in a choice of styles (reel pop, bold, clean boxed, karaoke word highlight). Use when the user wants subtitles or captions on a video.
---
# Caption Clip: generate and burn in subtitles

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.  Needs `pip install faster-whisper`.

```bash
V="python3 tools/vid.py"
$V transcribe in.mp4                  # in.srt + in.words.json
$V captions in.mp4 in.words.json out/captioned.mp4 --style reel
```

| Style | Look | Use for |
|---|---|---|
| `reel` | white, heavy outline, uppercase, 3-word pops | Reels/TikTok |
| `bold` | yellow, uppercase, shadow | high energy |
| `karaoke` | words highlight as spoken | Shorts, music |
| `clean` | sentence case on a translucent box | YouTube, tutorials |

Options: `--pos bottom|middle|top`, `--max-words 2..6` (words per caption, only with `.words.json`), `--font Poppins`.
Pass the `.srt` instead of `.words.json` for full-sentence subtitles.

Before burning, Read the `.srt` and fix misheard names or brand terms, then burn from the corrected `.srt`.
To ship soft (toggleable) subtitles instead: `ffmpeg -i in.mp4 -i in.srt -c copy -c:s mov_text out/soft.mp4`.
