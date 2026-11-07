---
name: motion-graphics
description: Create animated B-roll, transitions, lower thirds and branded graphics as video clips to drop into an edit. Use for branded overlays, animated stats, logo stings or transition elements.
---
# Motion Graphics: B-roll, transitions, branded graphics

Build graphics as time-driven HTML pages (see **hyperframes**) or Three.js scenes (like `reel.js`) and render with `render.mjs`.

## Elements to build
- **Lower third:** name + role bar that wipes in from the left, holds 3 s, wipes out. Render on a green or black background, or with transparency (below).
- **Animated stat:** a number counting up (`Math.round(easeOutCubic(p) * target)`) with a bar or ring filling.
- **Logo sting:** the brand cube from `logo.svg` scaling in with overshoot, 1.5 s.
- **Transition wipe:** a brand-color panel sweeping across in 0.4 s; place it on the cut between two clips.

## Render
```bash
node render.mjs --page lower-third.html --to 5 --w 1080 --h 1920
```

## Overlay onto footage
Render on pure green (`#00ff00`), then key it out:
```bash
ffmpeg -i main.mp4 -i out/lower-third.mp4 -filter_complex \
 "[1:v]colorkey=0x00ff00:0.3:0.1[g];[0:v][g]overlay=0:0:enable='between(t,2,7)'" -c:a copy out/with-l3.mp4
```
For a full-screen graphic as B-roll, use the **broll-overlay** skill. Keep brand colors and fonts consistent with `index.html`.
