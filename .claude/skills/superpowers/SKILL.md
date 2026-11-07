---
name: superpowers
description: Route video work to the right skill and enforce a disciplined production workflow (plan, preview, verify, never overwrite sources). Use at the start of any video task to choose skills, or when unsure which video skill applies.
---
# Superpowers: pick the right skill, follow the workflow

## Which skill?
| Task | Skill |
|---|---|
| Raw footage → finished | video-use |
| Edits in plain words | video-editing |
| Remove ums and pauses | cut-video |
| Exact timestamps | video-trimmer |
| Batch color/subs/exports | video-editor |
| Animated titles/explainers | hyperframes, remotion-motion-graphics, remotion-agent-skills |
| Website → product video | video-shotcraft |
| Reels with animated captions | vertical-video-editing |
| Long → many shorts | clipify, claude-shorts |
| 16:9 → 9:16 | shorts-video-creator |
| Branded graphics / B-roll | motion-graphics, broll-overlay |
| Thumbnails | thumbnail-skills |
| Review a video | claude-video-vision, watch-video |
| Subtitles / translation | caption-clip, omni-captions |
| Hooks & post captions | caption-engine |
| Color | color-grade-ai |
| Audio | audio-editing |
| AI-generated footage | pexo-agent, higgsfield-skills, kling-ai-skills |
| Full productions | video-producer, claude-code-video-toolkit |
| New skill | skill-creator |

## Workflow rules
1. **Plan first:** state the steps and outputs before rendering anything long.
2. **Preview cheaply:** stills and short ranges (`render.mjs --stills`, `trim` a 5 s test) before full renders.
3. **Never overwrite sources:** numbered outputs in `out/`.
4. **Verify by looking:** after each visual step, extract frames and Read them; after audio steps, check loudness numbers.
5. **Report honestly:** say what was checked and what wasn't (e.g. audio can't be listened to here).
