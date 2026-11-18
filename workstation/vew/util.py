"""Shared helpers: tool lookup, subprocess runner with JSON-lines logging, path guards."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


class VewError(RuntimeError):
    """Any user-facing failure (missing tool, bad input, refused overwrite...)."""


INSTALL_HINT = (
    "{name} was not found. On Windows install FFmpeg with:  winget install Gyan.FFmpeg  "
    "(then open a NEW terminal), or download it from https://www.gyan.dev/ffmpeg/builds/ "
    "and add its bin folder to PATH. You can also set the {env} environment variable to the exe path."
)


def tool(name: str) -> str:
    env = name.upper()
    path = os.environ.get(env) or shutil.which(name)
    if not path:
        raise VewError(INSTALL_HINT.format(name=name, env=env))
    return path


_LOG_PATH: Path | None = None


def set_log(path) -> None:
    """Direct all subsequent command logs to this file (JSON lines)."""
    global _LOG_PATH
    _LOG_PATH = Path(path) if path else None
    if _LOG_PATH:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_event(**fields) -> None:
    if not _LOG_PATH:
        return
    fields = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
    with open(_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(fields, ensure_ascii=False) + "\n")


def run(cmd, cwd=None, check=True, label: str = "") -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    secs = round(time.time() - t0, 2)
    log_event(
        event="command", label=label or Path(cmd[0]).name, cmd=cmd, returncode=proc.returncode,
        seconds=secs, stderr_tail=(proc.stderr or "")[-1500:] if proc.returncode else "",
    )
    if check and proc.returncode != 0:
        raise VewError(f"{label or Path(cmd[0]).name} failed (exit {proc.returncode}):\n{(proc.stderr or '')[-2000:]}")
    return proc


def ffmpeg(args, loglevel: str = "error", **kw) -> subprocess.CompletedProcess:
    return run([tool("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", loglevel, *args], label="ffmpeg", **kw)


def sha256(path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                return h.hexdigest()
            h.update(block)


def guard_output(out, sources=(), force: bool = False) -> Path:
    """Refuse to overwrite a source file or (without force) any existing file."""
    out = Path(out).resolve()
    for s in sources:
        if Path(s).resolve() == out:
            raise VewError(f"Refusing to write over source file: {out}")
    if out.exists() and not force:
        raise VewError(f"Output already exists: {out}\nChoose another name or pass --force.")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def versioned_path(directory, stem: str, ext: str = ".mp4") -> Path:
    """Next free <stem>_vNNN<ext>; never reuses a name, so finals are never overwritten."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    n = 1
    while (directory / f"{stem}_v{n:03d}{ext}").exists():
        n += 1
    return directory / f"{stem}_v{n:03d}{ext}"


def fmt_ts(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
