---
name: skill-creator
description: Build new custom Claude skills for video creation in this repo: folder layout, SKILL.md frontmatter, trigger descriptions, helper scripts and testing. Use when the user wants a new or modified video skill.
---
# Skill Creator (video)

## Layout
```
.claude/skills/<kebab-name>/
  SKILL.md          # required
  scripts/…         # optional helpers the skill runs
  references/…      # optional longer docs, loaded only when needed
```

## SKILL.md
```markdown
---
name: kebab-name
description: What it does + when to use it, with the words a user would actually say. (This line decides when the skill triggers.)
---
# Title
Steps with exact commands, options worth knowing, how to verify the result.
```

## Guidelines
- Build on `tools/vid.py` and `render.mjs` instead of new one-off scripts; add a subcommand to `vid.py` if a capability is missing.
- Keep SKILL.md under ~150 lines; move long reference material into `references/`.
- Include a verification step (frames to Read, loudness to check).
- Test on a synthetic clip before committing:
  `ffmpeg -f lavfi -i testsrc2=s=1920x1080:d=10 -f lavfi -i sine=d=10 -shortest -pix_fmt yuv420p out/test.mp4`
- Add the new skill to the routing table in **superpowers**.
