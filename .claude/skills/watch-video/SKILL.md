---
name: watch-video
description: Analyze a video's scenes, pacing and transcript and produce a structured breakdown (shot list, cut rate, speaking rate, structure). Use to study a video, including reference videos the user wants to imitate.
---
# Watch Video: scenes, pacing and transcript

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

```bash
V="python3 tools/vid.py"
$V probe in.mp4
$V scenes in.mp4 > out/scenes.txt            # shot boundaries and lengths
$V frames in.mp4 out/shots --scenes          # one frame per shot
$V transcribe in.mp4                          # in.txt / in.srt / in.words.json
```

## Report
1. **Shot list:** table of # / start–end / length / what's on screen (from the frames).
2. **Pacing:** average shot length, longest shots, cuts per minute; compare with ~2–3 s for Reels and 4–8 s for YouTube.
3. **Speech:** words per minute (word count / speaking minutes); pauses > 1 s.
4. **Structure:** hook → setup → body → payoff → CTA, with timestamps.
5. **Takeaways:** what makes it work, and how to reuse the pattern.
