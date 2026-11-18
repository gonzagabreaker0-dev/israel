"""brand.json loading. Brand values are only ever read, never rewritten, by the engine."""
from __future__ import annotations

import json
from pathlib import Path

from .util import VewError

DEFAULT_BRAND = {
    "company_name": "",
    "colors": {"primary": "#FFFFFF", "secondary": "#000000", "accent": "#FFD400"},
    "font_family": "Arial",
    "fonts_dir": None,
    "logo_path": None,
    "watermark": {"enabled": False, "position": "bottom_right", "opacity": 0.7, "scale": 0.12},
    "subtitle": {"style": "bold", "overrides": {}},
    "cta": {"text": "", "text_color": "#FFFFFF", "background": "#000000"},
    "intro": {"enabled": False, "path": None},
    "outro": {"enabled": False, "path": None},
}


def load_brand(path=None) -> dict:
    brand = json.loads(json.dumps(DEFAULT_BRAND))
    if not path:
        return brand
    p = Path(path)
    if not p.is_file():
        raise VewError(f"brand file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    for key, val in data.items():
        if isinstance(val, dict) and isinstance(brand.get(key), dict):
            brand[key].update(val)
        else:
            brand[key] = val
    brand["_path"] = str(p.resolve())
    return brand
