---
name: audio-editing
description: Clean background noise, improve voice clarity, balance levels and add music ducked under speech. Use for noisy recordings, quiet or uneven voices, and music mixing.
---
# Audio Editing

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

- **Clean voice:** `python3 tools/vid.py audio-clean in.mp4 out/clean.mp4`
  (80 Hz high-pass, FFT denoise, compression, presence boost, loudness to -14 LUFS).
  Heavy noise: `--denoise 20`. YouTube/podcast loudness: `--lufs -16`.
- **Add music under the voice:** `music out/clean.mp4 track.mp3 out/mixed.mp4 --music-db -16 --duck`
  (`--duck` lowers the music whenever someone speaks; the music loops and fades out at the end).
- **Audio only:** `ffmpeg -i in.mp4 -vn -c:a pcm_s16le out/voice.wav`.
- **Replace audio:** `ffmpeg -i in.mp4 -i new.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out/x.mp4`.
- **Measure loudness:** `ffmpeg -i in.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12`.

For original music, sound design and voice-over generated from code, see `audio/make_audio.py` in this repo.
Listen-check is impossible here, so verify numerically: integrated loudness near target, true peak ≤ -1.5 dBTP.
