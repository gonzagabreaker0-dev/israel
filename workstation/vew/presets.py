"""Social media export presets. All are H.264 + AAC, MP4 container."""
from __future__ import annotations

from .util import VewError

# safe_bottom: fraction of frame height kept clear of captions (platform UI overlays on vertical video)
# caption_margin_v: default caption distance from the bottom edge, as a fraction of height
PRESETS = {
    "instagram_reels": dict(label="Instagram Reels", w=1080, h=1920, fps=30, safe_bottom=0.15, caption_margin_v=0.18),
    "facebook_reels": dict(label="Facebook Reels", w=1080, h=1920, fps=30, safe_bottom=0.15, caption_margin_v=0.18),
    "tiktok": dict(label="TikTok", w=1080, h=1920, fps=30, safe_bottom=0.15, caption_margin_v=0.18),
    "youtube_shorts": dict(label="YouTube Shorts", w=1080, h=1920, fps=30, safe_bottom=0.15, caption_margin_v=0.18),
    "facebook_feed": dict(label="Facebook Feed (1:1)", w=1080, h=1080, fps=30, safe_bottom=0.05, caption_margin_v=0.08),
    "instagram_feed": dict(label="Instagram Feed (4:5)", w=1080, h=1350, fps=30, safe_bottom=0.05, caption_margin_v=0.08),
    "youtube": dict(label="YouTube (16:9)", w=1920, h=1080, fps=30, safe_bottom=0.05, caption_margin_v=0.07),
}


def get_preset(name: str, scale: float = 1.0) -> dict:
    if name not in PRESETS:
        raise VewError(f"Unknown preset '{name}'. Available: {', '.join(PRESETS)}")
    p = dict(PRESETS[name])
    p["name"] = name
    if scale != 1.0:  # preview renders: keep aspect ratio, force even dimensions
        p["w"] = max(2, int(p["w"] * scale) // 2 * 2)
        p["h"] = max(2, int(p["h"] * scale) // 2 * 2)
    return p
