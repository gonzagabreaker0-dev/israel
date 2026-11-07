---
name: pexo-agent
description: Generate AI video clips by choosing the best text-to-video / image-to-video model for each shot (Veo, Kling, Runway, Luma, Sora, Hailuo and others) and writing model-specific prompts. Use when the user wants AI-generated footage.
---
# Pexo Agent: multi-model AI video generation

This skill plans and prompts AI video generation and assembles the results. It does not include a vendor client: generation runs through whichever provider the user has an account and API key for.

## 1. Shot plan
Break the idea into shots of 4–10 s. For each: subject, action, setting, camera move, lighting, mood, duration, aspect ratio.

## 2. Pick a model per shot
| Need | Strong choices |
|---|---|
| Photoreal people, dialogue, native audio | Veo |
| Dynamic motion, image-to-video consistency | Kling |
| Stylized looks, camera control | Runway |
| Fast, smooth camera moves | Luma |
| Long coherent scenes | Sora |
Model lineups change quickly: check each provider's current docs before recommending one.

## 3. Prompt formula
`[shot type + camera move], [subject + action], [setting], [lighting], [style/film stock], [mood]` — one action per shot; describe motion explicitly; add negatives where supported ("no text, no warped hands").

## 4. Generate
Use the provider's official API or web app. If an API call needs a key, request it with the credential tool for that provider's host; never ask for keys in chat.

## 5. Assemble
`python3 tools/vid.py concat out/ai-cut.mp4 shot1.mp4 shot2.mp4 …`, then grade with **color-grade-ai** so shots from different models match, and add music with **audio-editing**.
