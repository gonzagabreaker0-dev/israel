---
name: claude-shorts
description: Find the best, most engaging moments in a video by analysing the transcript and turn them into captioned short clips. Use when the user asks which parts would go viral or to pick highlights.
---
# Claude Shorts: find the best moments

Toolkit: `python3 tools/vid.py <command>` from the repo root (run `python3 tools/vid.py -h` for every option).
Write results to `out/` (gitignored). Never overwrite the source footage; every step writes a new file.  Needs `pip install faster-whisper`.

1. `python3 tools/vid.py transcribe in.mp4` and Read `in.txt`.
2. Score candidate moments 1–5 on each:
   - **Hook**: does the first sentence make you stop scrolling? (bold claim, question, number, conflict)
   - **Standalone**: understandable with no context?
   - **Payoff**: a punchline, insight, reveal or tip by the end?
   - **Emotion/energy**: laughter, surprise, strong opinion, story.
   - **Length**: 15–45 s ideal.
3. Present the top 5 with timestamps, score, the hook line and why it works. Ask which to cut, or cut the top 3 if the user said to go ahead.
4. Cut, reframe and caption with `clips … --vertical`, then `captions … --style karaoke` (see **clipify**).
5. Suggest a title and a 1-line on-screen hook for each (see **caption-engine**).
