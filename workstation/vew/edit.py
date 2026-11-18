"""FFmpeg editing engine: trim, split, merge, resize/reframe, export.

Everything funnels through render_sequence(), which builds ONE filter_complex that
normalises every clip (size, fps, SAR, audio format) and concatenates them. Source
files are only ever read.
"""
from __future__ import annotations

import time
from pathlib import Path

from .probe import summarize
from .util import VewError, ffmpeg, guard_output, run, tool

_ENCODER_CACHE: dict = {}


def pick_encoder(prefer: str = "auto") -> str:
    """'cpu' -> libx264. 'auto'/'nvenc' -> h264_nvenc only if a real test encode works."""
    if prefer == "cpu":
        return "libx264"
    if "nvenc" not in _ENCODER_CACHE:
        proc = run(
            [tool("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
             "color=c=black:s=256x256:d=0.2", "-c:v", "h264_nvenc", "-f", "null", "-"],
            check=False, label="nvenc-probe",
        )
        _ENCODER_CACHE["nvenc"] = proc.returncode == 0
    if _ENCODER_CACHE["nvenc"]:
        return "h264_nvenc"
    if prefer == "nvenc":
        raise VewError("h264_nvenc requested but no working NVIDIA encoder was found; use --encoder cpu.")
    return "libx264"


def video_args(encoder: str, quality: str) -> list:
    crf = {"final": 18, "preview": 28, "intermediate": 12}[quality]
    if encoder == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p2" if quality == "preview" else "p5",
                "-rc", "vbr", "-cq", str(crf + 1), "-b:v", "0", "-pix_fmt", "yuv420p"]
    preset = {"final": "medium", "preview": "veryfast", "intermediate": "veryfast"}[quality]
    return ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p"]


AUDIO_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def resolve_mode(mode: str, sw: int, sh: int, w: int, h: int) -> str:
    """auto: crop only when aspect ratios nearly match; otherwise keep the whole frame on blurred padding."""
    if mode != "auto":
        return mode
    return "crop" if abs((sw / sh) / (w / h) - 1) < 0.06 else "blur"


def fit_chain(inp: str, out: str, tag: str, w: int, h: int, fps: float, mode: str,
              focus=(0.5, 0.5), speed: float = 1.0, sar: float = 1.0, pad_color: str = "black") -> str:
    """Filter-graph fragment fitting one input into w x h without ever stretching the picture."""
    pre = f"setpts=(PTS-STARTPTS)/{speed}"
    if abs(sar - 1.0) > 0.001:  # anamorphic source: bake SAR into pixels first
        pre += f",scale=trunc(iw*{sar}/2)*2:ih,setsar=1"
    tail = f"setsar=1,fps={fps:g},format=yuv420p"
    if mode == "crop":
        fx, fy = focus
        return (f"{inp}{pre},scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h}:(iw-ow)*{fx}:(ih-oh)*{fy},{tail}{out}")
    if mode == "pad":
        return (f"{inp}{pre},scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={pad_color},{tail}{out}")
    if mode == "blur":
        return (f"{inp}{pre},split=2[bg{tag}][fg{tag}];"
                f"[bg{tag}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                f"boxblur=luma_radius=min(h\\,w)/40:luma_power=2,eq=brightness=-0.10[bb{tag}];"
                f"[fg{tag}]scale={w}:{h}:force_original_aspect_ratio=decrease[fs{tag}];"
                f"[bb{tag}][fs{tag}]overlay=(W-w)/2:(H-h)/2,{tail}{out}")
    raise VewError(f"Unknown fit mode '{mode}' (use auto, crop, pad, blur)")


def _atempo(speed: float) -> str:
    if not 0.5 <= speed <= 2.0:
        raise VewError("speed must be between 0.5 and 2.0 in v1")
    return "" if speed == 1.0 else f",atempo={speed}"


def render_sequence(clips, out, w, h, fps=30, mode="auto", quality="final", encoder="auto",
                    normalize_audio=False, force=False, pad_color="black") -> dict:
    """clips: [{"src":..., "start":0, "end":None, "speed":1.0, "focus":[0.5,0.5]}]. Returns a result dict."""
    if not clips:
        raise VewError("No clips to render")
    w, h = int(w) // 2 * 2, int(h) // 2 * 2
    inputs, graph, concat_in, total = [], [], "", 0.0
    idx = 0
    for i, c in enumerate(clips):
        src = c["src"]
        info = summarize(src)
        start = float(c.get("start") or 0)
        end = c.get("end")
        end = info["duration"] if end in (None, "") else min(float(end), info["duration"])
        dur = end - start
        speed = float(c.get("speed") or 1.0)
        if start < 0 or dur <= 0.05:
            raise VewError(f"Clip {i} ({Path(src).name}): invalid range {start}-{end} (source is {info['duration']:.2f}s)")
        total += dur / speed
        out_dur = dur / speed
        mode_i = resolve_mode(c.get("mode") or mode, info["width"], info["height"], w, h)
        inputs += ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src)]
        vi = idx
        idx += 1
        graph.append(fit_chain(f"[{vi}:v:0]", f"[v{i}]", str(i), w, h, fps, mode_i,
                               tuple(c.get("focus") or (0.5, 0.5)), speed, info["sar"], pad_color))
        afmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
        if info["has_audio"]:
            graph.append(f"[{vi}:a:0]{afmt}{_atempo(speed)},apad=whole_dur={out_dur:.3f},"
                         f"atrim=end={out_dur:.3f},asetpts=PTS-STARTPTS[a{i}]")
        else:  # keep A/V in step: synthesize silence for clips without audio
            inputs += ["-f", "lavfi", "-t", f"{out_dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            graph.append(f"[{idx}:a:0]{afmt},asetpts=PTS-STARTPTS[a{i}]")
            idx += 1
        concat_in += f"[v{i}][a{i}]"
    graph.append(f"{concat_in}concat=n={len(clips)}:v=1:a=1[vcat][acat]")
    if normalize_audio:  # single-pass EBU R128 to -14 LUFS (social media standard)
        graph.append("[acat]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
        amap = "[aout]"
    else:
        amap = "[acat]"
    out = guard_output(out, [c["src"] for c in clips], force)
    enc = pick_encoder(encoder)
    cmd = [*inputs, "-filter_complex", ";".join(graph), "-map", "[vcat]", "-map", amap,
           *video_args(enc, quality), *AUDIO_ARGS, "-movflags", "+faststart", "-y", str(out)]
    t0 = time.time()
    ffmpeg(cmd)
    return {"out": str(out), "expected_duration": round(total, 3), "width": w, "height": h, "fps": fps,
            "encoder": enc, "quality": quality, "render_seconds": round(time.time() - t0, 2)}


# ---------------------------------------------------------------- convenience operations

def trim(src, out, start, end=None, quality="final", encoder="auto", force=False) -> dict:
    info = summarize(src)
    return render_sequence([{"src": src, "start": start, "end": end}], out, info["width"], info["height"],
                           round(info["fps"]) or 30, "pad", quality, encoder, force=force)


def split(src, points, out_dir, quality="final", encoder="auto", force=False) -> list:
    """Split at the given timestamps (seconds) into numbered parts inside out_dir."""
    info = summarize(src)
    cuts = [0.0, *sorted(float(p) for p in points), info["duration"]]
    results = []
    for n, (a, b) in enumerate(zip(cuts, cuts[1:]), start=1):
        out = Path(out_dir) / f"{Path(src).stem}_part{n:02d}.mp4"
        results.append(trim(src, out, a, b, quality, encoder, force))
    return results


def merge(srcs, out, preset=None, size=None, fps=None, mode="auto", quality="final", encoder="auto",
          normalize_audio=False, force=False) -> dict:
    """Concatenate whole files. Output size: preset, else explicit (w,h), else the first clip's size."""
    first = summarize(srcs[0])
    if preset:
        w, h, f = preset["w"], preset["h"], preset["fps"]
    elif size:
        (w, h), f = size, fps or round(first["fps"]) or 30
    else:
        w, h, f = first["width"], first["height"], fps or round(first["fps"]) or 30
    return render_sequence([{"src": s} for s in srcs], out, w, h, f, mode, quality, encoder, normalize_audio, force)


def export(src, out, preset, mode="auto", quality="final", encoder="auto", normalize_audio=False, force=False) -> dict:
    """Resize/reframe one file to a social preset (never stretches)."""
    return render_sequence([{"src": src}], out, preset["w"], preset["h"], preset["fps"], mode, quality,
                           encoder, normalize_audio, force)
