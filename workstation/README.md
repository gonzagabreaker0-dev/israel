# Video Editing Workstation (v0.1)

FFmpeg-based, scriptable video editing for social ads and reels. Pure Python standard library: no pip installs needed for v1 (Whisper is optional).

## Setup (Windows)

```powershell
winget install Gyan.FFmpeg        # then open a NEW terminal
python --version                  # 3.9+
cd workstation
python -m vew diagnose            # writes diagnostics_report.txt/.json
```

`diagnose` checks Python, FFmpeg/FFprobe, encoders (x264, AAC, NVENC), libass, GPU, disk space and optional packages, and prints install steps for anything missing. NVENC is only used if a real test encode succeeds; otherwise it uses CPU x264.

## Quick start

```powershell
python -m vew new "Coffee Ad"                      # projects/coffee-ad/{source,work,audio,subs,assets,previews,final,logs,reports}
python -m vew import projects/coffee-ad C:\footage\clip1.mp4 C:\footage\clip2.mov
#   copies to source/ (read-only), records SHA-256, writes thumbnails, 16 kHz WAV, scene list, report.md
```

Edit `projects/coffee-ad/config.json`:

```json
{
  "name": "Coffee Ad",
  "preset": "instagram_reels",
  "fit_mode": "auto",
  "encoder": "auto",
  "normalize_audio": true,
  "brand": "../../brand.json",
  "clips": [
    {"src": "source/clip1.mp4", "start": 1.0, "end": 6.5},
    {"src": "source/clip2.mov", "start": 0, "end": 4, "mode": "crop", "focus": [0.5, 0.4]}
  ],
  "subtitles": {"srt": "subs/ad.srt", "style": "highlight", "keywords": ["fresh"]}
}
```

```powershell
python -m vew build projects/coffee-ad                    # half-size preview -> previews/
python -m vew build projects/coffee-ad --quality final    # full quality -> final/<name>_<preset>_v001.mp4
```

`build` runs QC and prints `VERIFIED` only when every check passes. Finals are versioned (`_v001`, `_v002`...) and never overwritten.

## Individual commands

| Command | What it does |
|---|---|
| `analyze FILE --out DIR` | metadata, thumbnails, audio extract, scene changes, report |
| `trim SRC OUT --start 2 --end 8` | frame-accurate trim (re-encode, source resolution) |
| `split SRC --at 5 10 --outdir DIR` | split into parts |
| `merge OUT A B C --preset tiktok` | normalise + concatenate (mixed sizes/fps/missing audio OK) |
| `export SRC OUT --preset youtube --mode blur` | resize/reframe to a preset |
| `subtitle SRC OUT --srt x.srt --style bold --keywords a,b` | burn captions |
| `fixsubs x.srt --map fixes.json --out y.srt` | explicit find→replace corrections |
| `transcribe AUDIO --out x.srt --lang tl` | Whisper (optional, see below) |
| `qc FILE --preset P --expected-duration S` | verify an export |
| `presets` | list presets |

Presets: `instagram_reels`, `facebook_reels`, `tiktok`, `youtube_shorts` (1080x1920), `facebook_feed` (1080x1080), `instagram_feed` (1080x1350), `youtube` (1920x1080). H.264 + AAC, yuv420p, faststart.

Fit modes (never stretch): `auto` (crop only if aspect is within 6%, else blur), `blur` (whole frame over blurred fill), `pad` (black bars), `crop` (centre or `focus` crop).

Caption styles: `bold`, `highlight`, `centered`, `lower_third`, `animated`. Font, colours and size come from `brand.json` (`subtitle.overrides` accepts `size_pct`, `color`, `outline_color`, `margin_v_pct`, `alignment`, ...). Caption text is never altered; keywords only get a colour tag.

## Safety rules built in

- Sources are only read. Imports are copied read-only and checksummed; writing over a source path is refused.
- Existing outputs are never overwritten without `--force`; project finals are auto-versioned.
- Every FFmpeg command is logged (JSON lines) to `projects/<name>/logs/render.log.jsonl`.
- `brand.json` is read-only to the engine.

## Quality control

Checks: assets present, full-decode integrity, duration, resolution, fps, H.264/AAC, audio present, black frames (warning only), subtitles. Reports go to `reports/*.md|json`.
Limitation: the subtitle check validates timing against video length and bottom margin against the platform safe zone from the generated style. It does not detect text overlap with on-screen content.

## Optional: Whisper

`pip install faster-whisper` (or `openai-whisper`, which needs PyTorch). `transcribe` writes an SRT and word-level timestamps. Always review the SRT. This command is not covered by the automated tests.

## Tests

```powershell
python -m unittest discover -s tests -v
```
Generates synthetic clips with FFmpeg and tests probe, trim, merge of mixed sources, all presets, subtitles, source protection, import/analysis, build + QC, and QC failure detection.

## Roadmap (not in v1)

Crossfades/xfade transitions, zoom effects, colour grading, music and SFX mixing with ducking, motion graphics (titles, lower thirds, CTA, end screens), logo watermark and intro/outro from `brand.json`, advertising-script workflow, word-by-word animated captions.
