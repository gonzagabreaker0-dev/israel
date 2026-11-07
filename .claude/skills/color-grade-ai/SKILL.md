---
name: color-grade-ai
description: Give footage a cinematic look with color correction and grading: preset looks, strength control and LUTs. Use when the user wants footage to look warmer, more cinematic, moodier or consistent.
---
# Color Grade AI

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.

1. Look at the footage first: `python3 tools/vid.py frames in.mp4 out/before --n 4`, Read the frames. Note exposure, white balance and mood.
2. Pick a look:

| `--look` | Feel | Good for |
|---|---|---|
| `warm` | golden, cozy | food, coffee, lifestyle |
| `teal-orange` | blockbuster, skin pops against teal | travel, promos |
| `film` | soft contrast, grain, vignette | storytelling, nostalgic |
| `cool` | crisp, clean | tech, corporate |
| `bw` | contrasty monochrome | dramatic moments |
| `punchy` | saturated, sharp | social, product |

3. Apply, usually at partial strength: `grade in.mp4 out/graded.mp4 --look warm --strength 0.7`.
   With a `.cube` LUT: `grade in.mp4 out/graded.mp4 --lut looks/kodak.cube`.
4. Compare: grab the same timestamps from `out/graded.mp4` and Read before/after side by side.

Fix exposure before the look if needed: `ffmpeg -i in.mp4 -vf "eq=brightness=0.04:contrast=1.05,colortemperature=temperature=5200" -c:a copy out/fixed.mp4`.
Grade every clip in an edit with the same look and strength so they match.
