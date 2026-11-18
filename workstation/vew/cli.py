"""Command line interface:  python -m vew <command> ...  (run from the workstation folder)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import diagnose as diag
from . import edit, importer, qc as qcmod, subtitles
from .brand import load_brand
from .presets import PRESETS, get_preset
from .project import Project
from .probe import summarize
from .util import VewError, set_log

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECTS = ROOT / "projects"


def _preset_args(p):
    p.add_argument("--preset", choices=list(PRESETS), required=True)
    p.add_argument("--mode", default="auto", choices=["auto", "crop", "pad", "blur"],
                   help="how to fit footage to the preset (never stretches)")


def _common(p):
    p.add_argument("--quality", default="final", choices=["preview", "final"])
    p.add_argument("--encoder", default="auto", choices=["auto", "cpu", "nvenc"])
    p.add_argument("--force", action="store_true", help="allow overwriting an existing output file")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="vew", description="Video editing workstation (FFmpeg)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("diagnose", help="check FFmpeg, encoders, GPU, disk, Python packages")
    p.add_argument("--out", default=str(ROOT / "diagnostics_report"))

    sub.add_parser("presets", help="list export presets")

    p = sub.add_parser("new", help="create a project folder")
    p.add_argument("name")
    p.add_argument("--base", default=str(DEFAULT_PROJECTS))

    p = sub.add_parser("import", help="import footage into a project (copy, checksum, analyze)")
    p.add_argument("project")
    p.add_argument("files", nargs="+")
    p.add_argument("--no-analyze", action="store_true")

    p = sub.add_parser("analyze", help="analyze one file (metadata, thumbnails, scenes, audio)")
    p.add_argument("file")
    p.add_argument("--out", required=True, help="folder for thumbnails and report")
    p.add_argument("--scene-threshold", type=float, default=0.30)

    p = sub.add_parser("trim")
    p.add_argument("src"); p.add_argument("out")
    p.add_argument("--start", type=float, default=0.0); p.add_argument("--end", type=float)
    _common(p)

    p = sub.add_parser("split", help="split at timestamps into parts")
    p.add_argument("src"); p.add_argument("--at", type=float, nargs="+", required=True)
    p.add_argument("--outdir", required=True)
    _common(p)

    p = sub.add_parser("merge", help="concatenate files (normalised to one size/fps)")
    p.add_argument("out"); p.add_argument("srcs", nargs="+")
    p.add_argument("--preset", choices=list(PRESETS))
    p.add_argument("--mode", default="auto", choices=["auto", "crop", "pad", "blur"])
    p.add_argument("--normalize-audio", action="store_true")
    _common(p)

    p = sub.add_parser("export", help="resize/reframe to a social preset")
    p.add_argument("src"); p.add_argument("out")
    _preset_args(p)
    p.add_argument("--normalize-audio", action="store_true")
    _common(p)

    p = sub.add_parser("subtitle", help="burn an SRT into a video")
    p.add_argument("src"); p.add_argument("out"); p.add_argument("--srt", required=True)
    p.add_argument("--style", default="bold", choices=list(subtitles.CAPTION_PRESETS))
    p.add_argument("--keywords", help="comma list or JSON file of words to highlight")
    p.add_argument("--preset", choices=list(PRESETS), help="use this preset's caption safe margins")
    p.add_argument("--brand", help="path to brand.json")
    _common(p)

    p = sub.add_parser("fixsubs", help="apply explicit find->replace corrections to an SRT")
    p.add_argument("srt"); p.add_argument("--map", required=True, help='JSON file {"wrong": "right"}')
    p.add_argument("--out", required=True)

    p = sub.add_parser("transcribe", help="Whisper speech-to-text -> SRT (optional dependency)")
    p.add_argument("audio"); p.add_argument("--out", required=True)
    p.add_argument("--lang", help="en, tl (Filipino), ... default auto")
    p.add_argument("--model", default="small")

    p = sub.add_parser("qc", help="verify an exported file")
    p.add_argument("file"); p.add_argument("--preset", choices=list(PRESETS), required=True)
    p.add_argument("--expected-duration", type=float, required=True)

    p = sub.add_parser("build", help="render a project from config.json, then run QC")
    p.add_argument("project")
    p.add_argument("--quality", default="preview", choices=["preview", "final"])
    return ap


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return _dispatch(args)
    except VewError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def _dispatch(a) -> int:
    c = a.cmd
    if c == "diagnose":
        rep = diag.collect(ROOT)
        diag.write(rep, a.out)
        print(diag.render_text(rep))
        return 0 if rep["ready"] else 1
    if c == "presets":
        for k, v in PRESETS.items():
            print(f"{k:16} {v['w']}x{v['h']}  {v['fps']}fps  {v['label']}")
        return 0
    if c == "new":
        pr = Project.create(a.base, a.name)
        print(f"Created project: {pr.root}")
        return 0
    if c == "import":
        pr = Project(a.project)
        set_log(pr.path("logs") / "render.log.jsonl")
        for f in a.files:
            e = importer.import_video(f, pr, analyze_after=not a.no_analyze)
            print(f"imported {e['file']}  sha256={e['sha256'][:12]}…" + (f"  report: {e['analysis']}" if "analysis" in e else ""))
        return 0
    if c == "analyze":
        r = importer.analyze(a.file, a.out, a.scene_threshold)
        print(open(r["report_md"], encoding="utf-8").read())
        return 0
    if c == "trim":
        r = edit.trim(a.src, a.out, a.start, a.end, a.quality, a.encoder, a.force)
    elif c == "split":
        rs = edit.split(a.src, a.at, a.outdir, a.quality, a.encoder, a.force)
        for r in rs:
            print(r["out"])
        return 0
    elif c == "merge":
        r = edit.merge(a.srcs, a.out, get_preset(a.preset) if a.preset else None, mode=a.mode, quality=a.quality,
                       encoder=a.encoder, normalize_audio=a.normalize_audio, force=a.force)
    elif c == "export":
        r = edit.export(a.src, a.out, get_preset(a.preset), a.mode, a.quality, a.encoder, a.normalize_audio, a.force)
    elif c == "subtitle":
        r = subtitles.burn_subtitles(a.src, a.out, a.srt, a.style, get_preset(a.preset) if a.preset else None,
                                     load_brand(a.brand) if a.brand else None, subtitles.load_keywords(a.keywords),
                                     quality=a.quality, encoder=a.encoder, force=a.force)
    elif c == "fixsubs":
        n = subtitles.apply_corrections(a.srt, json.loads(Path(a.map).read_text(encoding="utf-8")), a.out)
        print(f"{n} replacements -> {a.out}")
        return 0
    elif c == "transcribe":
        from .transcribe import transcribe
        r = transcribe(a.audio, a.out, a.lang, a.model)
    elif c == "qc":
        rep = qcmod.run_qc(a.file, get_preset(a.preset), a.expected_duration)
        base = Path(a.file).with_name(Path(a.file).stem + "_qc")
        qcmod.write_report(rep, base)
        print(base.with_suffix(".md").read_text(encoding="utf-8"))
        return 0 if rep["passed"] else 1
    elif c == "build":
        rep = Project(a.project).build(a.quality)
        print(json.dumps({k: rep[k] for k in ("output", "passed")}, indent=2))
        for ch in rep["checks"]:
            print(f"  [{ch['status'].upper():4}] {ch['name']}: {ch['detail']}")
        print("VERIFIED" if rep["passed"] else "QC FAILED: do not publish this render")
        return 0 if rep["passed"] else 1
    else:
        raise VewError(f"unhandled command {c}")
    print(json.dumps(r, indent=2))
    return 0
