---
name: hyperframes
description: Create animated titles, explainers and product videos from HTML/CSS/JS and render them frame-accurately to MP4. Use for title cards, kinetic typography, explainer scenes and product promos without footage.
---
# HyperFrames: HTML → animated video

This repo already renders any page that exposes `window.REEL` (see `render.mjs`). Every frame is a pure function of time `t`, so the render is frame-accurate.

## Page contract
```html
<script type="module">
  const stage = document.getElementById('stage');          // render.mjs screenshots #stage
  function renderAt(t) { /* set every style/transform from t; no timers, no CSS animations */ }
  window.REEL = { ready: true, renderAt, duration: 8 };
</script>
```
Use easing helpers (`easeOutCubic`, `easeInOutQuad`) and `clamp((t - start) / dur, 0, 1)` for each element's progress. Do not use `setTimeout`, `requestAnimationFrame` loops or CSS transitions inside `renderAt`; they don't follow `t`.

## Render
```bash
node render.mjs --page titles.html --to 8                 # 1080x1920 MP4 in out/
node render.mjs --page titles.html --to 8 --w 1920 --h 1080
node render.mjs --page titles.html --stills 1,3,6         # quick JPEG previews first
```
Look at the stills before a full render. Reuse the brand fonts in `fonts/` and colors from `index.html`.

## Recipes
- **Title card:** words slide up from a mask one by one (stagger 0.08 s), underline wipes in, hold, fade out.
- **Explainer:** 3–5 scenes, one idea each, 3–6 s per scene, icon + one line of text.
- **Product promo:** screenshot in a device frame, slow 3D tilt (`perspective` + `rotateY`), callouts pop in.
