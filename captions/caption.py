#!/usr/bin/env python3
"""Burn house-style captions (and a logo) into a vertical talking-head video.

House style (from the reference frame):
  - 1080x1920 (9:16). Landscape or other sizes are scaled/cropped to fill.
  - Captions: bold uppercase, yellow fill, thin dark outline + soft drop shadow,
    max 2 lines, centered horizontally, centred at ~65% of frame height
    (chest level, below the face, never in the bottom UI zone).
  - Logo: top-left corner (~6% in from the left, ~5% down).

Usage:
  python3 captions/caption.py INPUT.mp4 [-o OUT.mp4] [--logo logo.png | --logo-text LOGO]
                              [--words 4] [--srt-only] [--model small.en]
Transcription runs locally with faster-whisper; edit the generated .ass/.json
next to the output and re-run with --from-json to fix wording.
"""
import argparse, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")

W, H = 1080, 1920
STYLE = dict(
    font="Poppins", bold=-1, size=100,
    fill="&H0000E5F2",      # ASS is &HAABBGGRR -> #F2E500 yellow
    outline="&H00141414", outline_w=5,
    shadow="&H96000000", shadow_d=6,
    center_y=0.655,         # caption block centre, fraction of height
    side_margin=90,
)
LOGO = dict(x=0.065, y=0.045, height=0.055, text_color="&H00E04A1E", text_size=96)  # #1E4AE0 blue


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r.stdout


def probe(path):
    out = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", path]))
    s = out["streams"][0]
    return s["width"], s["height"], float(out["format"]["duration"])


def transcribe(path, model_name):
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    import numpy as np
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    segs, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True, beam_size=5)
    words = []
    for s in segs:
        for w in s.words or []:
            t = w.word.strip()
            if t:
                words.append({"w": t, "s": round(w.start, 3), "e": round(w.end, 3)})
    return words


def chunk(words, max_words, max_chars=22):
    """Group words into short caption cards; break on pauses and sentence ends."""
    cards, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["s"] - w["e"]) if nxt else 9
        end_sentence = re.search(r"[.!?]$", w["w"])
        if len(cur) >= max_words or len(text) >= max_chars * 2 - 6 or gap > 0.45 or end_sentence or not nxt:
            cards.append(cur)
            cur = []
    # never leave a single word stranded on its own card
    merged = []
    for c in cards:
        if merged and len(c) == 1 and c[0]["s"] - merged[-1][-1]["e"] < 0.3 \
                and len(" ".join(x["w"] for x in merged[-1] + c)) <= max_chars * 2 - 4:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def clean(t):
    t = re.sub(r"[.,!?;:]+$", "", t)          # no trailing punctuation on cards
    return t.upper()


def two_lines(words, max_chars=22):
    text = " ".join(clean(w["w"]) for w in words)
    if len(text) <= max_chars or len(words) == 1:
        return text
    best, best_diff = text, 1e9
    for k in range(1, len(words)):
        a = " ".join(clean(w["w"]) for w in words[:k]); b = " ".join(clean(w["w"]) for w in words[k:])
        d = abs(len(a) - len(b))
        if d < best_diff:
            best, best_diff = a + r"\N" + b, d
    return best


def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(cards, duration, logo_text=None):
    st = STYLE
    cy = int(H * st["center_y"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{st['size']},{st['fill']},{st['fill']},{st['outline']},{st['shadow']},{st['bold']},0,0,0,100,100,0,0,1,{st['outline_w']},{st['shadow_d']},5,{st['side_margin']},{st['side_margin']},0,1
Style: Logo,{st['font']},{LOGO['text_size']},{LOGO['text_color']},{LOGO['text_color']},&H00FFFFFF,&H64000000,-1,0,0,0,100,100,0,0,1,2,4,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for i, c in enumerate(cards):
        start = c[0]["s"]
        nxt = cards[i + 1][0]["s"] if i + 1 < len(cards) else duration
        end = min(max(c[-1]["e"] + 0.25, start + 0.6), nxt)  # hold briefly, never overlap
        # quick pop-in: 85% -> 100% over 80ms
        fx = r"{\pos(%d,%d)\fscx85\fscy85\t(0,80,\fscx100\fscy100)}" % (W // 2, cy)
        lines.append(f"Dialogue: 1,{ts(start)},{ts(end)},Cap,,0,0,0,,{fx}{two_lines(c)}")
    if logo_text:
        lines.append(f"Dialogue: 0,{ts(0)},{ts(duration)},Logo,,0,0,0,,"
                     + r"{\pos(%d,%d)}" % (int(W * LOGO["x"]), int(H * LOGO["y"])) + logo_text)
    return head + "\n".join(lines) + "\n"


def write_srt(cards, path):
    with open(path, "w") as f:
        for i, c in enumerate(cards, 1):
            s, e = c[0]["s"], c[-1]["e"]
            fmt = lambda t: f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(t*1000)%1000:03d}"
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{two_lines(c).replace(chr(92)+'N', chr(10))}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out")
    ap.add_argument("--logo", help="logo image (png/svg/jpg) placed top-left")
    ap.add_argument("--logo-text", help="text logo instead of an image")
    ap.add_argument("--words", type=int, default=4, help="max words per caption card")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--from-json", help="reuse/edit a words .json instead of transcribing")
    ap.add_argument("--srt-only", action="store_true")
    a = ap.parse_args()

    base = os.path.splitext(a.out or a.input)[0]
    out = a.out or base + "-captioned.mp4"
    _, _, dur = probe(a.input)

    if a.from_json:
        words = json.load(open(a.from_json))
    else:
        words = transcribe(a.input, a.model)
        json.dump(words, open(base + ".words.json", "w"), indent=1)
    cards = chunk(words, a.words)
    write_srt(cards, base + ".srt")
    if a.srt_only:
        print(base + ".srt"); return

    ass_path = base + ".ass"
    open(ass_path, "w").write(build_ass(cards, dur, a.logo_text if not a.logo else None))

    fill = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    esc = lambda p: p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    subs = f"ass='{esc(ass_path)}':fontsdir='{esc(FONT_DIR)}'"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.input]
    if a.logo:
        logo = a.logo
        if logo.lower().endswith(".svg"):
            png = os.path.join(tempfile.mkdtemp(), "logo.png")
            run(["node", os.path.join(ROOT, "captions", "svg2png.mjs"), logo, png, str(int(H * LOGO["height"]) * 2)])
            logo = png
        lh = int(H * LOGO["height"])
        cmd += ["-i", logo, "-filter_complex",
                f"[0:v]{fill}[v];[1:v]scale=-1:{lh}[lg];[v][lg]overlay={int(W*LOGO['x'])}:{int(H*LOGO['y'])}[v2];[v2]{subs}[out]",
                "-map", "[out]", "-map", "0:a?"]
    else:
        cmd += ["-vf", f"{fill},{subs}", "-map", "0:v", "-map", "0:a?"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    run(cmd)
    print(out)


if __name__ == "__main__":
    main()
