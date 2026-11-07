---
name: video-producer
description: Produce product demo videos end to end: write the script, record the screen, generate a voice-over, sync and edit. Use for product demos, app walkthroughs and tutorial videos.
---
# Video Producer: product demos

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

1. **Script:** a table of beats: time, on-screen action, voice-over line. Hook → problem → 3 key features → result → CTA. ~150 spoken words per minute.
2. **Screen recording:** for web apps use **video-shotcraft**'s `capture.mjs` (scripted, repeatable takes); otherwise use the user's own recording.
3. **Voice-over:** either the user's recorded voice, a TTS service they have a key for, or local TTS:
   `apt-get install -y festival` (see `audio/make_audio.py` for how this repo builds narration), or `espeak-ng`.
   Generate one file per line so timing is easy to adjust.
4. **Sync:** place each line at its beat with ffmpeg `adelay` and `amix`, or stretch shots with `trim` to match the narration.
5. **Polish:** `audio-clean`, `music … --duck`, `captions … --style clean`, title/end cards with **hyperframes**.
6. **Export:** `export … --preset youtube` and a vertical cut with `--preset reels`.
