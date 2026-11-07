---
name: omni-captions
description: Transcribe, translate and style captions in many languages: auto-detect language, translate to English or any other language, export SRT and burn in. Use for multilingual or translated subtitles.
---
# Omni Captions: transcribe, translate, style

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.  Needs `pip install faster-whisper`.

- Transcribe (auto-detects language): `python3 tools/vid.py transcribe in.mp4` — prints `language=…`.
- Force a language: `--lang es`. Accuracy: `--model medium` or `large-v3`.
- Translate speech straight to English: `transcribe in.mp4 --translate --out out/in.en`.
- Translate to any other language: Read the `.srt`, translate each cue's text yourself keeping the numbering and timestamps exactly, and write `out/in.<lang>.srt`. Keep lines under ~42 characters; split long cues into two lines.

Burn in and style with **caption-clip**:
```bash
python3 tools/vid.py captions in.mp4 out/in.es.srt out/in.es.mp4 --style clean
```
For several languages, deliver one `.srt` per language plus burned-in versions only for the ones the user asks for.
Non-Latin scripts (Arabic, Hindi, CJK) need a font that covers them: pass `--font "Noto Sans"` (install `fonts-noto` if missing).
