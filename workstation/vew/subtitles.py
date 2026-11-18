"""SRT handling, caption presets, ASS generation and burn-in via FFmpeg's libass filter.

The wording of every cue is preserved exactly. Only presentation (font, colour, position,
animation) is changed; keyword highlighting wraps existing words in colour tags.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .probe import summarize
from .util import VewError, ffmpeg, guard_output
from .edit import AUDIO_ARGS, pick_encoder, video_args

CAPTION_PRESETS = {
    "bold": dict(size_pct=4.4, bold=True, color="#FFFFFF", outline_color="#000000", alignment=2,
                 margin_h_pct=0.07, border_style=1, animation=None, highlight=False),
    "highlight": dict(size_pct=4.4, bold=True, color="#FFFFFF", outline_color="#000000", alignment=2,
                      margin_h_pct=0.07, border_style=1, animation=None, highlight=True),
    "centered": dict(size_pct=4.6, bold=True, color="#FFFFFF", outline_color="#000000", alignment=5,
                     margin_h_pct=0.08, border_style=1, animation=None, highlight=True),
    "lower_third": dict(size_pct=3.0, bold=False, color="#FFFFFF", outline_color="#000000", alignment=1,
                        margin_h_pct=0.06, border_style=3, box_alpha=0.35, animation=None, highlight=False),
    "animated": dict(size_pct=4.6, bold=True, color="#FFFFFF", outline_color="#000000", alignment=2,
                     margin_h_pct=0.07, border_style=1, animation="pop", highlight=True),
}


@dataclass
class Cue:
    index: int
    start: float
    end: float
    text: str


# ------------------------------------------------------------------ SRT

_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d{1,3})\s*-->\s*(\d+):(\d+):(\d+)[,.](\d{1,3})")


def _secs(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_srt(path) -> list:
    text = Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.split("\n")]
        for k, ln in enumerate(lines):
            m = _TIME.search(ln)
            if m:
                g = m.groups()
                body = "\n".join(lines[k + 1:]).strip()
                if body:
                    cues.append(Cue(len(cues) + 1, _secs(*g[:4]), _secs(*g[4:]), body))
                break
    if not cues:
        raise VewError(f"No subtitle cues found in {path}")
    return cues


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(cues, path) -> Path:
    path = Path(path)
    path.write_text("\n".join(f"{i}\n{_srt_time(c.start)} --> {_srt_time(c.end)}\n{c.text}\n"
                              for i, c in enumerate(cues, 1)), encoding="utf-8")
    return path


def apply_corrections(srt_in, mapping: dict, srt_out) -> int:
    """Explicit find->replace corrections (you choose every change). Returns number of replacements."""
    cues, n = parse_srt(srt_in), 0
    for c in cues:
        for wrong, right in mapping.items():
            if wrong in c.text:
                n += c.text.count(wrong)
                c.text = c.text.replace(wrong, right)
    write_srt(cues, srt_out)
    return n


# ------------------------------------------------------------------ ASS

def _ass_color(hex_color: str, alpha: float = 0.0) -> str:
    hx = hex_color.lstrip("#")
    if len(hx) != 6:
        raise VewError(f"Bad colour '{hex_color}', expected #RRGGBB")
    r, g, b = hx[0:2], hx[2:4], hx[4:6]
    return f"&H{int(round(alpha * 255)):02X}{b}{g}{r}".upper()


def _ass_time(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def resolve_style(style: str, brand: dict | None, preset: dict | None, overrides: dict | None = None) -> dict:
    if style not in CAPTION_PRESETS:
        raise VewError(f"Unknown caption style '{style}'. Available: {', '.join(CAPTION_PRESETS)}")
    s = dict(CAPTION_PRESETS[style])
    s["margin_v_pct"] = (preset or {}).get("caption_margin_v", 0.10)
    if s["alignment"] == 5:
        s["margin_v_pct"] = 0.0
    s.update(font="Arial", highlight_color="#FFD400")
    if brand:
        s["font"] = brand.get("font_family") or s["font"]
        s["highlight_color"] = brand.get("colors", {}).get("accent") or s["highlight_color"]
        s.update((brand.get("subtitle") or {}).get("overrides") or {})
    s.update(overrides or {})
    return s


def build_ass(cues, width: int, height: int, style: dict, keywords=()) -> str:
    size = round(height * style["size_pct"] / 100)
    mh = round(width * style["margin_h_pct"])
    mv = round(height * style["margin_v_pct"])
    boxed = style["border_style"] == 3
    outline = max(6, round(size * 0.3)) if boxed else max(2, round(size * 0.09))
    outline_col = _ass_color(style["outline_color"], 1 - style.get("box_alpha", 1.0) if boxed else 0.0)
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{style['font']},{size},{_ass_color(style['color'])},&H000000FF,{outline_col},"
        f"&H64000000,{-1 if style['bold'] else 0},0,0,0,100,100,0,0,{style['border_style']},{outline},0,"
        f"{style['alignment']},{mh},{mh},{mv},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    kw = [k for k in keywords if k.strip()]
    kw_re = re.compile(r"(?<!\w)(" + "|".join(re.escape(k) for k in kw) + r")(?!\w)", re.I) if kw else None
    base, hi = _ass_color(style["color"]), _ass_color(style["highlight_color"])
    lines = []
    for c in cues:
        text = c.text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")
        if kw_re and style.get("highlight"):
            text = kw_re.sub(lambda m: f"{{\\c{hi}}}{m.group(1)}{{\\c{base}}}", text)
        if style.get("animation") == "pop":
            text = "{\\fad(90,70)\\fscx85\\fscy85\\t(0,140,\\fscx100\\fscy100)}" + text
        lines.append(f"Dialogue: 0,{_ass_time(c.start)},{_ass_time(c.end)},Default,,0,0,0,,{text}")
    return header + "\n".join(lines) + "\n"


def _escape_filter_path(p: str) -> str:
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def burn_subtitles(src, out, srt, style="bold", preset=None, brand=None, keywords=(), overrides=None,
                   quality="final", encoder="auto", ass_out=None, force=False) -> dict:
    """Burn captions into src -> out. Returns result incl. the ASS path and measured style geometry."""
    info = summarize(src)
    w, h = info["width"], info["height"]
    cues = parse_srt(srt)
    st = resolve_style(style, brand, preset, overrides)
    ass_path = Path(ass_out) if ass_out else Path(out).with_suffix(".ass")
    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text(build_ass(cues, w, h, st, keywords), encoding="utf-8")
    out = guard_output(out, [src], force)
    vf = f"ass={ass_path.name}"
    fonts = (brand or {}).get("fonts_dir")
    if fonts:
        vf += f":fontsdir={_escape_filter_path(str(Path(fonts).resolve()))}"
    enc = pick_encoder(encoder)
    # cwd = ASS folder so the filter sees a plain relative filename (avoids Windows drive-colon escaping)
    ffmpeg(["-i", str(Path(src).resolve()), "-vf", vf, *video_args(enc, quality),
            *(AUDIO_ARGS if info["has_audio"] else ["-an"]), "-movflags", "+faststart", "-y", str(out)],
           cwd=str(ass_path.parent.resolve()))
    margin_px = round(h * st["margin_v_pct"])
    return {"out": str(out), "ass": str(ass_path), "style": style, "cues": len(cues),
            "last_cue_end": max(c.end for c in cues), "alignment": st["alignment"],
            "margin_v_px": margin_px, "height": h, "encoder": enc}


def load_keywords(arg) -> list:
    if not arg:
        return []
    if isinstance(arg, (list, tuple)):
        return list(arg)
    p = Path(arg)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return [k.strip() for k in str(arg).split(",") if k.strip()]
