"""Optional speech-to-text (Whisper). Imports are lazy so the rest of the toolkit works without them.

NOTE: not exercised by the automated tests (needs a model download + real speech audio).
Review the generated SRT before burning; use `fixsubs` for explicit corrections.
"""
from __future__ import annotations

import json
from pathlib import Path

from .subtitles import Cue, write_srt
from .util import VewError


def transcribe(audio, out_srt, language=None, model="small", words=True) -> dict:
    """language: 'en', 'tl' (Filipino/Tagalog) or None to auto-detect. Writes SRT (+ words JSON)."""
    cues, word_list = [], []
    try:
        from faster_whisper import WhisperModel  # type: ignore
        segs, info = WhisperModel(model, compute_type="int8").transcribe(str(audio), language=language, word_timestamps=words)
        for s in segs:
            cues.append(Cue(len(cues) + 1, s.start, s.end, s.text.strip()))
            word_list += [{"w": w.word.strip(), "start": w.start, "end": w.end} for w in (s.words or [])]
        lang = info.language
    except ImportError:
        try:
            import whisper  # type: ignore
        except ImportError:
            raise VewError("No Whisper backend installed. Run: pip install faster-whisper   (or: pip install openai-whisper)")
        res = whisper.load_model(model).transcribe(str(audio), language=language, word_timestamps=words)
        for s in res["segments"]:
            cues.append(Cue(len(cues) + 1, s["start"], s["end"], s["text"].strip()))
            word_list += [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for w in s.get("words", [])]
        lang = res.get("language")
    cues = [c for c in cues if c.text]
    if not cues:
        raise VewError("No speech detected")
    write_srt(cues, out_srt)
    if words and word_list:
        Path(out_srt).with_suffix(".words.json").write_text(json.dumps(word_list, indent=1), encoding="utf-8")
    return {"srt": str(out_srt), "language": lang, "cues": len(cues), "words": len(word_list)}
