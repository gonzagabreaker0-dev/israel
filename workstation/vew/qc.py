"""Quality control: verify an export and write a production report."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .probe import summarize
from .util import run, tool


def _check(name, status, detail):
    return {"name": name, "status": status, "detail": detail}


def black_segments(path, min_dur=0.5, pix_th=0.10) -> list:
    proc = run([tool("ffmpeg"), "-hide_banner", "-nostdin", "-i", str(path), "-vf",
                f"blackdetect=d={min_dur}:pix_th={pix_th}", "-an", "-f", "null", "-"], check=False, label="blackdetect")
    return [(float(a), float(b)) for a, b in
            re.findall(r"black_start:([\d.]+)\s+black_end:([\d.]+)", proc.stderr or "")]


def run_qc(path, preset: dict, expected_duration: float, caption_info: dict | None = None,
           assets=(), tolerance: float = 0.30) -> dict:
    checks = []
    path = Path(path)
    # missing assets
    missing = [a for a in assets if not Path(a).exists()]
    checks.append(_check("assets", "fail" if missing else "pass",
                         f"missing: {missing}" if missing else f"{len(list(assets))} referenced assets present"))
    if not path.is_file() or path.stat().st_size == 0:
        checks.append(_check("output", "fail", "output file missing or empty"))
        return _finish(path, checks, {})
    info = summarize(path)
    # integrity: full decode, any error text is a failure
    dec = run([tool("ffmpeg"), "-hide_banner", "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"],
              check=False, label="integrity")
    ok = dec.returncode == 0 and not (dec.stderr or "").strip()
    checks.append(_check("integrity", "pass" if ok else "fail",
                         "full decode clean" if ok else (dec.stderr or "decode failed")[:300]))
    # duration
    delta = abs(info["duration"] - expected_duration)
    checks.append(_check("duration", "pass" if delta <= tolerance else "fail",
                         f"{info['duration']:.2f}s vs expected {expected_duration:.2f}s (Δ{delta:.2f}s)"))
    # resolution
    same = (info["width"], info["height"]) == (preset["w"], preset["h"])
    checks.append(_check("resolution", "pass" if same else "fail",
                         f"{info['width']}x{info['height']} vs target {preset['w']}x{preset['h']}"))
    # fps
    fps_ok = abs(info["fps"] - preset["fps"]) < 0.1
    checks.append(_check("frame_rate", "pass" if fps_ok else "fail", f"{info['fps']:.2f} vs target {preset['fps']}"))
    # codecs
    codec_ok = info["vcodec"] == "h264" and any(a["codec"] == "aac" for a in info["audio"])
    checks.append(_check("codecs", "pass" if codec_ok else "fail",
                         f"video={info['vcodec']} audio={[a['codec'] for a in info['audio']]}"))
    # audio presence
    checks.append(_check("audio_present", "pass" if info["has_audio"] else "fail",
                         "audio stream found" if info["has_audio"] else "no audio stream"))
    # black frames (warning only: intentional fades are common)
    segs = black_segments(path)
    checks.append(_check("black_frames", "warn" if segs else "pass",
                         f"black segments (start,end): {segs}" if segs else "none detected"))
    # subtitles (geometry derived from the generated ASS style; see README for limits)
    if caption_info:
        cap_fail = []
        if caption_info["last_cue_end"] > info["duration"] + 0.05:
            cap_fail.append(f"last cue ends {caption_info['last_cue_end']:.2f}s after video end {info['duration']:.2f}s")
        bottom_aligned = caption_info["alignment"] in (1, 2, 3)
        need = round(preset["h"] * preset["safe_bottom"])
        if bottom_aligned and caption_info["margin_v_px"] < need - 1:
            cap_fail.append(f"bottom margin {caption_info['margin_v_px']}px is inside the {need}px platform UI safe zone")
        checks.append(_check("subtitles", "fail" if cap_fail else "pass",
                             "; ".join(cap_fail) or f"{caption_info['cues']} cues, style '{caption_info['style']}', "
                             f"bottom margin {caption_info['margin_v_px']}px (safe zone {need}px)"))
    return _finish(path, checks, info)


def _finish(path, checks, info) -> dict:
    return {"file": str(path), "passed": all(c["status"] != "fail" for c in checks),
            "checks": checks, "media": info}


def write_report(report: dict, base) -> tuple:
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    jpath, mpath = base.with_suffix(".json"), base.with_suffix(".md")
    jpath.write_text(json.dumps(report, indent=2), encoding="utf-8")
    icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    lines = [f"# Production report: {Path(report['file']).name}", "",
             f"**Result: {'VERIFIED' if report['passed'] else 'FAILED QC'}**", ""]
    for k in ("project", "quality", "preset", "encoder", "render_seconds"):
        if k in report:
            lines.append(f"- {k}: {report[k]}")
    lines += ["", "| Check | Status | Detail |", "|---|---|---|"]
    lines += [f"| {c['name']} | {icon[c['status']]} | {c['detail'].replace('|', '/')} |" for c in report["checks"]]
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jpath, mpath
