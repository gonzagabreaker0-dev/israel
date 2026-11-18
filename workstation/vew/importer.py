"""Import (non-destructive copy + checksum) and analysis: metadata, thumbnails, audio, scene changes."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
from pathlib import Path

from .probe import SUPPORTED_EXT, summarize
from .util import VewError, ffmpeg, sha256


def import_video(src, project, analyze_after: bool = True) -> dict:
    """Copy src into <project>/source (read-only), record its SHA-256 and optionally analyze it."""
    src = Path(src)
    if src.suffix.lower() not in SUPPORTED_EXT:
        raise VewError(f"Unsupported format '{src.suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXT))}")
    if not src.is_file():
        raise VewError(f"File not found: {src}")
    summarize(src)  # fail early if it is not decodable video
    dest = project.path("source") / src.name
    if dest.exists():
        if sha256(dest) != sha256(src):
            raise VewError(f"A different file named {src.name} is already imported; rename yours first.")
    else:
        shutil.copy2(src, dest)
        os.chmod(dest, stat.S_IREAD)  # originals stay untouched, protect the copy too
    entry = {"file": src.name, "sha256": sha256(dest), "source_path": str(src.resolve())}
    manifest_p = project.path("source") / "manifest.json"
    manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {}
    manifest[src.name] = entry
    manifest_p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if analyze_after:
        entry["analysis"] = analyze(dest, project.path("work") / dest.stem,
                                    audio_dir=project.path("audio"))["report_json"]
    return entry


def detect_scenes(path, threshold: float = 0.30) -> list:
    proc = ffmpeg(["-i", str(path), "-vf", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                  loglevel="info", check=False)
    return [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", proc.stderr or "")]


def analyze(path, out_dir, scene_threshold: float = 0.30, audio_dir=None) -> dict:
    """Write thumbnails + report.json/report.md into out_dir. Never touches the source."""
    path, out_dir = Path(path), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    info = summarize(path)
    dur = info["duration"]
    thumbs = []
    for label, frac in (("start", 0.05), ("middle", 0.5), ("end", 0.95)):
        t = out_dir / f"thumb_{label}.jpg"
        ffmpeg(["-ss", f"{dur * frac:.3f}", "-i", str(path), "-frames:v", "1", "-vf", "scale=640:-2",
                "-q:v", "3", "-y", str(t)])
        thumbs.append(str(t))
    audio_path = None
    if info["has_audio"]:  # 16 kHz mono WAV: the format speech-to-text models expect
        ad = Path(audio_dir) if audio_dir else out_dir
        ad.mkdir(parents=True, exist_ok=True)
        audio_path = str(ad / f"{path.stem}.wav")
        ffmpeg(["-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", audio_path])
    scenes = detect_scenes(path, scene_threshold)
    report = {**info, "thumbnails": thumbs, "audio_wav": audio_path, "scene_threshold": scene_threshold,
              "scene_changes": scenes, "scene_count": len(scenes) + 1}
    jp, mp = out_dir / "report.json", out_dir / "report.md"
    jp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    mp.write_text("\n".join([
        f"# Video analysis: {path.name}", "",
        f"- Resolution: {info['width']}x{info['height']}  ({info['width'] / info['height']:.3f}:1)",
        f"- Frame rate: {info['fps']:.2f} fps", f"- Duration: {dur:.2f}s",
        f"- Video codec: {info['vcodec']} ({info['pix_fmt']})",
        f"- Audio: {info['audio'] or 'none'}", f"- Size: {info['size_bytes'] / 1e6:.2f} MB",
        f"- Scene changes (threshold {scene_threshold}): {len(scenes)} at {scenes[:20]}",
        f"- Thumbnails: {', '.join(Path(t).name for t in thumbs)}",
        f"- Extracted audio: {audio_path or 'n/a'}", ""]), encoding="utf-8")
    return {"report": report, "report_json": str(jp), "report_md": str(mp)}
