---
name: remotion-agent-skills
description: Build custom, data-driven animated videos in code with Remotion: templates driven by JSON props, batch renders, charts and lists animated from data. Use when the user wants programmatic or templated video generation.
---
# Remotion Agent Skills: videos as code

Set up Remotion as in **remotion-motion-graphics** (`npx create-video@latest remotion`).

## Data-driven template
1. Define the props with a zod schema so they're validated and editable in the Studio:
   ```tsx
   export const schema = z.object({title: z.string(), items: z.array(z.object({label: z.string(), value: z.number()}))});
   ```
2. Build scenes with `<Sequence from={…} durationInFrames={…}>` and animate each item with a staggered `spring({frame: frame - i * 6, fps})`.
3. Compute duration from data with `calculateMetadata` so a 3-item and a 10-item video both fit.

## Batch render from a data file
```bash
node -e '
const rows = require("./data.json");
const {execSync} = require("child_process");
rows.forEach((r, i) => execSync(`npx remotion render Main ../out/v${i}.mp4 --props=${JSON.stringify(JSON.stringify(r))}`, {stdio: "inherit"}));'
```

## Preview and check
- `npx remotion studio` for live preview.
- `npx remotion still Main ../out/f.png --frame=45` to check a frame and Read it before a full render.
- Animate only from `useCurrentFrame()`; load fonts with `@remotion/google-fonts` or `staticFile()`.
