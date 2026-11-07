---
name: caption-engine
description: Write scroll-stopping hooks, on-screen text and social post captions (with hashtags) from a video transcript. Use when the user needs hooks, titles or captions for posting a video.
---
# Caption Engine: hooks and post captions from transcripts

1. Get the words: `python3 tools/vid.py transcribe in.mp4` and Read the `.txt` (or use a transcript the user provides).
2. Identify the core promise of the video in one sentence.

## Deliver
- **5 on-screen hooks** (≤ 8 words each) using different angles: curiosity gap, bold claim, number/list, "stop doing X", relatable pain.
- **3 titles** (YouTube ≤ 60 chars, front-load the keyword).
- **Post caption per platform:**
  - Instagram: hook line, 2–4 short lines of value, CTA, 3–5 niche hashtags.
  - TikTok: one punchy line + 3 hashtags.
  - YouTube Shorts: title + 1–2 sentence description.
  - LinkedIn: insight-first, 3–5 short paragraphs, no hashtag spam.
- **CTA options** (follow, comment a keyword, visit, save).

Match the brand voice; for the coffee shop that's warm and inviting. Use only claims made in the transcript.
To put a hook on screen, use the **hyperframes** skill or a `captions` pass with a one-cue `.srt`.
