---
name: remotion-motion-graphics
description: Make smooth text animations, intros and outros with Remotion (React). Use when the user asks for Remotion, or for reusable, data-driven intro/outro templates.
---
# Remotion Motion Graphics

Remotion renders React components to video. Use it for intros, outros, lower thirds and text animation that should be reusable as templates.
(The official **Remotion** plugin is also in the Anthropic plugin directory if you want its full skill set.)

## Set up (in a subfolder so the reel project stays untouched)
```bash
npx create-video@latest remotion --template blank   # then: cd remotion && npm i
```

## Text animation pattern
```tsx
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
export const Intro: React.FC<{title: string}> = ({title}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 200}});
  const out = interpolate(f, [70, 90], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#0b0b0f', justifyContent: 'center', alignItems: 'center'}}>
    <h1 style={{fontFamily: 'Poppins', color: 'white', fontSize: 120, opacity: out,
      transform: `translateY(${(1 - s) * 80}px) scale(${0.9 + s * 0.1})`}}>{title}</h1>
  </AbsoluteFill>;
};
```
Register it in `Root.tsx` with `<Composition id="Intro" component={Intro} durationInFrames={90} fps={30} width={1080} height={1920} defaultProps={{title: 'Hello'}} />`.

## Render and attach
```bash
npx remotion render Intro ../out/intro.mp4 --props='{"title":"Israel Coffee Shop"}'
python3 ../tools/vid.py concat ../out/with-intro.mp4 ../out/intro.mp4 ../out/main.mp4
```
Drive all motion from `useCurrentFrame()`; never from `Date` or timers.
