---
name: higgsfield-skills
description: Plan and write AI UGC-style ads, faceless videos and consistent-character content for platforms like Higgsfield: scripts, character sheets, shot prompts and assembly. Use for AI UGC ads, faceless channels and recurring AI characters.
---
# Higgsfield Skills: AI UGC ads, faceless videos, characters

Generation happens on the user's Higgsfield (or similar) account; this skill does the planning, prompts and the edit.

## UGC ad (15–30 s)
1. **Hook (0–3 s):** a person on camera saying a relatable problem line.
2. **Demo (3–15 s):** product in hand / in use, 2–3 benefits.
3. **Proof:** result, before/after, or a reaction.
4. **CTA:** what to do now.
Write it as a script with a shot prompt per line: framing (selfie, handheld), setting (kitchen, car, café), wardrobe, emotion.

## Faceless video
Script → voice-over (TTS) → 1 visual prompt per sentence (B-roll style, no faces needed) → captions (**caption-clip**) → music (**audio-editing**).

## Consistent character
Write a **character sheet** reused verbatim in every prompt: age, face, hair, skin, outfit, signature item, voice. Generate one hero reference image first and use image-to-video from it so the character stays the same.

## Assemble
Download clips into `footage/ai/`, then `concat`, `captions` and `export --preset reels` with `tools/vid.py`.
Label AI-generated ads as required by the platform's ad policies; don't present AI people as real customers.
