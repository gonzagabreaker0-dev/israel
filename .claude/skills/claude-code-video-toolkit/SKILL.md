---
name: claude-code-video-toolkit
description: One workflow that handles scripting, audio, editing and rendering for a whole video project inside this repo. Use when the user wants a complete video made, start to finish, or asks what video tools are available.
---
# Claude Code Video Toolkit

Everything lives in this repo:
- `tools/vid.py`: ffmpeg toolkit (cutting, captions, reframing, grading, audio, analysis, export). `python3 tools/vid.py -h`.
- `render.mjs`: renders any time-driven HTML/Three.js page (`window.REEL.renderAt(t)`) to MP4.
- `audio/make_audio.py`: code-generated music, sound design and voice-over.
- `.claude/skills/`: the 30 video skills.

## Workflow
1. **Brief:** goal, audience, platform, length, CTA. Ask only what you can't infer.
2. **Script & shot list** (see **video-producer**, **caption-engine** for hooks).
3. **Visuals:** footage (**video-use**), generated graphics (**hyperframes**, **motion-graphics**, **remotion-motion-graphics**), screen captures (**video-shotcraft**), AI footage (**pexo-agent**).
4. **Audio:** voice, music, cleanup (**audio-editing**).
5. **Edit:** cut, B-roll, captions, grade.
6. **Review:** contact sheet + frames (**claude-video-vision**); fix issues.
7. **Export** per platform; thumbnail (**thumbnail-skills**).

Keep intermediate files numbered in `out/`; report final paths, durations and what changed.
