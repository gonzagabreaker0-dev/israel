"""System diagnostics: Python, FFmpeg/FFprobe, encoders, GPU, disk space, optional Python packages."""
from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

from .util import run

NEEDED_ENCODERS = ["libx264", "aac", "h264_nvenc", "libx265"]
NEEDED_FILTERS = ["ass", "subtitles", "drawtext", "xfade", "loudnorm", "blackdetect", "boxblur"]
PY_PACKAGES = {  # name -> (import name, required?, purpose)
    "Pillow": ("PIL", False, "graphics / thumbnails (motion graphics, later versions)"),
    "numpy": ("numpy", False, "image maths"),
    "opencv-python": ("cv2", False, "advanced scene/face analysis (later versions)"),
    "faster-whisper": ("faster_whisper", False, "speech-to-text (recommended, lighter than openai-whisper)"),
    "openai-whisper": ("whisper", False, "speech-to-text (needs PyTorch)"),
    "torch": ("torch", False, "required by openai-whisper"),
}


def _first_line(proc) -> str:
    return ((proc.stdout or proc.stderr or "").strip().splitlines() or [""])[0]


def collect(workdir=".") -> dict:
    rep = {"os": f"{platform.system()} {platform.release()} ({platform.machine()})",
           "python": sys.version.split()[0], "python_exe": sys.executable, "problems": [], "advice": []}
    for name in ("ffmpeg", "ffprobe"):
        exe = shutil.which(name)
        if not exe:
            rep[name] = None
            rep["problems"].append(f"{name} missing")
            rep["advice"].append("Install FFmpeg on Windows: `winget install Gyan.FFmpeg`, then open a NEW terminal "
                                 "(or download from https://www.gyan.dev/ffmpeg/builds/ and add its bin folder to PATH).")
            continue
        rep[name] = {"path": exe, "version": _first_line(run([exe, "-version"], check=False))}
    if rep.get("ffmpeg"):
        exe = rep["ffmpeg"]["path"]
        enc = run([exe, "-hide_banner", "-encoders"], check=False).stdout
        rep["encoders"] = {e: any(f" {e} " in ln for ln in enc.splitlines()) for e in NEEDED_ENCODERS}
        flt = run([exe, "-hide_banner", "-filters"], check=False).stdout
        rep["filters"] = {f: any(f" {f} " in ln for ln in flt.splitlines()) for f in NEEDED_FILTERS}
        test = run([exe, "-hide_banner", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=black:s=256x256:d=0.2", "-c:v", "h264_nvenc", "-f", "null", "-"], check=False)
        rep["nvenc_usable"] = test.returncode == 0
        for must in ("libx264", "aac"):
            if not rep["encoders"][must]:
                rep["problems"].append(f"encoder {must} missing")
                rep["advice"].append("Use a full FFmpeg build (gyan.dev 'full' or 'essentials') that includes libx264 and aac.")
        if not (rep["filters"]["ass"] and rep["filters"]["subtitles"]):
            rep["problems"].append("libass filters missing (cannot burn subtitles)")
        if not rep["nvenc_usable"]:
            rep["advice"].append("NVIDIA GPU encoding unavailable; renders will use CPU libx264 (fully supported, slower).")
    smi = shutil.which("nvidia-smi")
    rep["nvidia_smi"] = _first_line(run([smi, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                                        check=False)) if smi else None
    usage = shutil.disk_usage(Path(workdir).resolve())
    rep["disk_free_gb"] = round(usage.free / 1e9, 1)
    if usage.free < 10e9:
        rep["problems"].append("less than 10 GB free disk space")
    rep["python_packages"] = {}
    for pkg, (mod, _req, purpose) in PY_PACKAGES.items():
        rep["python_packages"][pkg] = {"installed": importlib.util.find_spec(mod) is not None, "purpose": purpose}
    if not any(rep["python_packages"][p]["installed"] for p in ("faster-whisper", "openai-whisper")):
        rep["advice"].append("Optional, for auto-subtitles: `pip install faster-whisper` (or `pip install openai-whisper`). "
                             "SRT files you supply work without it.")
    if sys.version_info < (3, 9):
        rep["problems"].append("Python 3.9+ required")
    rep["ready"] = not rep["problems"]
    return rep


def render_text(rep: dict) -> str:
    out = ["VIDEO WORKSTATION DIAGNOSTICS", "=" * 30, f"OS:      {rep['os']}", f"Python:  {rep['python']}  ({rep['python_exe']})"]
    for n in ("ffmpeg", "ffprobe"):
        out.append(f"{n:8} {rep[n]['version'] if rep.get(n) else 'MISSING'}")
    if rep.get("encoders"):
        out.append("Encoders: " + ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in rep["encoders"].items()))
        out.append("Filters:  " + ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in rep["filters"].items()))
        out.append(f"NVENC GPU encoding usable: {'YES' if rep['nvenc_usable'] else 'no (CPU rendering)'}")
    out.append(f"NVIDIA GPU: {rep['nvidia_smi'] or 'not detected'}")
    out.append(f"Free disk:  {rep['disk_free_gb']} GB")
    out.append("Python packages: " + ", ".join(f"{k}={'yes' if v['installed'] else 'no'}" for k, v in rep["python_packages"].items()))
    out.append("")
    out.append("STATUS: " + ("READY" if rep["ready"] else "NOT READY: " + "; ".join(rep["problems"])))
    out += [f"  - {a}" for a in rep["advice"]]
    return "\n".join(out)


def write(rep: dict, base) -> None:
    Path(base).with_suffix(".json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    Path(base).with_suffix(".txt").write_text(render_text(rep) + "\n", encoding="utf-8")
