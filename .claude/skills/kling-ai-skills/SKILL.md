---
name: kling-ai-skills
description: Generate AI videos with Kling or build better text-to-video and image-to-video prompts: structure, camera language, motion and negative prompts. Use when the user mentions Kling or wants stronger text-to-video prompts.
---
# Kling AI Skills: generation and prompt building

## Prompt structure
`Subject (detailed) + Action/Motion + Scene + Camera + Lighting + Style + Atmosphere`

Example:
> A barista with rolled sleeves pours steamed milk into a ceramic cup, forming a rosetta. Close-up, slow push-in, shallow depth of field. Warm morning window light, steam rising. Cinematic, 35mm film look, cozy and calm.

## Tips
- One main action per clip; describe motion speed ("slowly", "in one smooth motion").
- Camera words that work: push in, pull back, orbit, tracking shot, crane up, handheld, static.
- Image-to-video: describe only what should **move**; the image already sets the look.
- Use the negative prompt for: blurry, distorted hands, extra fingers, text, watermark, flicker.
- Generate 5 s first; extend only the takes that work.

## Generating
Use the Kling web app or its official API with the user's key (request it through the credential tool for the API host; check Kling's current API docs for endpoints and model names rather than guessing).

## After generation
Grade all clips together (**color-grade-ai**), cut with `tools/vid.py concat`, add captions/music, export.
