"""FFprobe wrapper returning a flat, easy-to-use summary of a media file."""
from __future__ import annotations

import json
from pathlib import Path

from .util import VewError, run, tool

SUPPORTED_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def _rate(text) -> float:
    try:
        num, den = str(text).split("/")
        return float(num) / float(den) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        try:
            return float(text)
        except (TypeError, ValueError):
            return 0.0


def probe(path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise VewError(f"File not found: {path}")
    proc = run([tool("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", path], label="ffprobe")
    return json.loads(proc.stdout or "{}")


def summarize(path) -> dict:
    """Return {path,duration,width,height,fps,vcodec,pix_fmt,sar,has_audio,audio,size_bytes,format}."""
    data = probe(path)
    streams = data.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")]
    if not video:
        raise VewError(f"No video stream in {path}")
    v = video[0]
    rotation = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotation = int(float(sd["rotation"]))
    if not rotation and (v.get("tags") or {}).get("rotate"):
        rotation = int(float(v["tags"]["rotate"]))
    width, height = int(v["width"]), int(v["height"])
    if abs(rotation) % 180 == 90:  # ffmpeg auto-rotates on decode, so use displayed dimensions
        width, height = height, width
    sar = 1.0
    if v.get("sample_aspect_ratio") not in (None, "N/A", "0:1"):
        try:
            a, b = v["sample_aspect_ratio"].split(":")
            sar = float(a) / float(b)
        except (ValueError, ZeroDivisionError):
            sar = 1.0
    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or v.get("duration") or 0)
    audio = [
        {"codec": s.get("codec_name"), "channels": s.get("channels"), "sample_rate": s.get("sample_rate")}
        for s in streams if s.get("codec_type") == "audio"
    ]
    return {
        "path": str(path),
        "format": fmt.get("format_name"),
        "duration": duration,
        "width": width,
        "height": height,
        "rotation": rotation,
        "sar": sar,
        "fps": _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate")),
        "vcodec": v.get("codec_name"),
        "pix_fmt": v.get("pix_fmt"),
        "has_audio": bool(audio),
        "audio": audio,
        "size_bytes": int(fmt.get("size") or Path(path).stat().st_size),
    }
