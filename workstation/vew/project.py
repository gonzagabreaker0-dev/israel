"""Project folders, editing configuration and the build pipeline (preview / final)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import qc as qcmod
from .brand import load_brand
from .edit import render_sequence
from .presets import get_preset
from .subtitles import burn_subtitles, load_keywords
from .util import VewError, set_log, versioned_path, log_event

SUBDIRS = ["source", "work", "audio", "subs", "assets", "previews", "final", "logs", "reports"]

DEFAULT_CONFIG = {
    "name": "",
    "preset": "instagram_reels",
    "fit_mode": "auto",
    "encoder": "auto",
    "normalize_audio": True,
    "brand": None,
    "clips": [],
    "subtitles": {"srt": None, "style": None, "keywords": []},
}


def slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip()).strip("-").lower()
    if not s:
        raise VewError("Project name is empty")
    return s


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not (self.root / "config.json").is_file():
            raise VewError(f"Not a project folder (no config.json): {self.root}")

    @classmethod
    def create(cls, base, name: str) -> "Project":
        root = Path(base) / slug(name)
        if root.exists():
            raise VewError(f"Project already exists: {root}")
        for d in SUBDIRS:
            (root / d).mkdir(parents=True)
        cfg = dict(DEFAULT_CONFIG, name=name)
        (root / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return cls(root)

    def path(self, sub: str) -> Path:
        return self.root / sub

    @property
    def config(self) -> dict:
        return json.loads((self.root / "config.json").read_text(encoding="utf-8"))

    def save_config(self, cfg: dict) -> None:
        (self.root / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    def resolve(self, rel) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (self.root / p)

    def build(self, quality: str = "preview", force: bool = False) -> dict:
        """clips -> (merged, fitted to preset) -> optional captions -> QC. Returns the production report."""
        cfg = self.config
        if quality not in ("preview", "final"):
            raise VewError("quality must be 'preview' or 'final'")
        set_log(self.path("logs") / "render.log.jsonl")
        log_event(event="build_start", project=cfg["name"], quality=quality)
        clips = []
        for c in cfg["clips"]:
            src = self.resolve(c["src"])
            if not src.is_file():
                raise VewError(f"Missing asset: {src}")
            clips.append({**c, "src": str(src)})
        if not clips:
            raise VewError("config.json has no clips. Add entries like {\"src\": \"source/a.mp4\", \"start\": 0, \"end\": 5}")
        subs = cfg.get("subtitles") or {}
        srt = self.resolve(subs["srt"]) if subs.get("srt") else None
        if srt and not srt.is_file():
            raise VewError(f"Missing asset: {srt}")
        brand = load_brand(self.resolve(cfg["brand"]) if cfg.get("brand") else None)

        scale = 0.5 if quality == "preview" else 1.0
        preset = get_preset(cfg["preset"], scale)
        stem = f"{slug(cfg['name'])}_{cfg['preset']}"
        merged = self.path("work") / f"{stem}_{quality}_merged.mp4"
        if merged.exists():
            merged.unlink()  # work files are disposable intermediates, never originals
        step = render_sequence(clips, merged, preset["w"], preset["h"], preset["fps"], cfg["fit_mode"],
                               "intermediate" if srt else quality, cfg["encoder"], cfg["normalize_audio"],
                               force=True)
        expected = step["expected_duration"]
        caption_info = None
        target = versioned_path(self.path("previews" if quality == "preview" else "final"), stem)
        if srt:
            style = subs.get("style") or brand["subtitle"]["style"]
            caption_info = burn_subtitles(
                merged, target, srt, style, preset, brand, load_keywords(subs.get("keywords")),
                quality=quality, encoder=cfg["encoder"], ass_out=self.path("subs") / f"{stem}_{quality}.ass")
        else:
            shutil.move(str(merged), target)
        report = qcmod.run_qc(target, preset, expected, caption_info,
                              assets=[c["src"] for c in clips] + ([str(srt)] if srt else []))
        report.update(project=cfg["name"], quality=quality, output=str(target), preset=cfg["preset"],
                      encoder=step["encoder"], render_seconds=step["render_seconds"])
        qcmod.write_report(report, self.path("reports") / f"{target.stem}_report")
        log_event(event="build_done", output=str(target), passed=report["passed"])
        return report
