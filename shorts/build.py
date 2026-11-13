#!/usr/bin/env python3
"""Short-form edit builder: cuts, punch-in zooms, grade, audio mix and timeline.

  python3 shorts/build.py RAW.mp4 shorts/projects/<name>/edit.json OUTDIR [--words words.json]

Writes OUTDIR/base.mp4 (picture only), OUTDIR/audio.wav (voice + music + sfx)
and OUTDIR/timeline.json (captions, inserts, CTA in edited time). Then run
  node shorts/render.mjs OUTDIR    -> OUTDIR/final.mp4
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SFX = os.path.join(ROOT, ".claude/skills/sound-effects/sfx")
W, H, FPS = 1080, 1920, 30
ZOOM_IN = 1.12
ANCHOR = (0.56, 0.40)  # zoom about the face


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit("FAILED: " + " ".join(cmd)[:400] + "\n" + r.stderr[-3000:])
    return r


def transcribe(path):
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    import numpy as np
    from faster_whisper import WhisperModel
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(a, word_timestamps=True, beam_size=5)
    return [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]


def silences(path, min_len):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-32dB:d=0.2", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return [(a, b) for a, b in zip(st, en) if b - a >= min_len]


def subtract(keep, cuts):
    for ca, cb in cuts:
        nxt = []
        for a, b in keep:
            if cb <= a or ca >= b:
                nxt.append((a, b))
            else:
                if ca > a: nxt.append((a, ca))
                if cb < b: nxt.append((cb, b))
        keep = nxt
    return [(a, b) for a, b in keep if b - a >= 0.15]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("edit"); ap.add_argument("out")
    ap.add_argument("--words")
    ap.add_argument("--timeline-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    E = json.load(open(a.edit))
    words = json.load(open(a.words)) if a.words else transcribe(a.raw)

    # ---- 1. decide what to keep (source time) --------------------------------
    pad = 0.08
    cuts = [(s + pad, e - pad) for s, e in silences(a.raw, E.get("cut_silence_min", 0.3))]
    for i, j in E.get("remove_words", []):
        cuts.append((words[i]["s"] - 0.03, words[j]["e"] + 0.05))
    keep = subtract([(E.get("start", 0), E["end"])], sorted(cuts))

    offs, t = [], 0.0
    for s, e in keep:
        offs.append(t); t += e - s
    total = t

    def remap(x):
        for (s, e), o in zip(keep, offs):
            if s - 1e-6 <= x <= e + 1e-6:
                return o + (x - s)
        return None

    # zoom: toggle at real cuts (gap >= .3 s) once >= 1.6 s has passed
    zooms, z, since = [], 1.0, 0
    for k, (s, e) in enumerate(keep):
        if k and s - keep[k - 1][1] >= 0.3 and since >= 1.6:
            z = ZOOM_IN if z == 1.0 else 1.0; since = 0
        zooms.append(z); since += e - s

    # ---- 2. words in edited time ---------------------------------------------
    fixes = {int(k): v for k, v in E.get("word_fix", {}).items()}
    removed = {i for a_, b_ in E.get("remove_words", []) for i in range(a_, b_ + 1)}
    tw = []
    for i, w in enumerate(words):
        if i in removed: continue
        mid = (w["s"] + w["e"]) / 2
        ns, ne, nm = remap(w["s"]), remap(w["e"]), remap(mid)
        if nm is None and ns is None and ne is None: continue
        base = nm if nm is not None else (ns if ns is not None else ne)
        ns = ns if ns is not None else base
        ne = ne if ne is not None else base + 0.15
        if ne - ns > 0.9: ns = ne - 0.6          # words that swallowed a cut pause
        text = fixes.get(i, w["w"])
        tw.append({"i": i, "w": text, "s": round(ns, 3), "e": round(max(ne, ns + 0.08), 3)})

    # ---- 3. caption cards -----------------------------------------------------
    kw = set(E.get("keywords", []))
    hook = E.get("hook", {})
    cards, cur = [], []
    vis = [w for w in tw if w["w"].strip()]
    for n, w in enumerate(vis):
        cur.append(w)
        nxt = vis[n + 1] if n + 1 < len(vis) else None
        chars = len(" ".join(x["w"] for x in cur))
        brk = (not nxt or len(cur) >= 4 or chars >= 20 or (re.search(r"[.!?,]$", w["w"]) and not re.match(r"(?i)^(dr|mr|mrs|ms)\.$", w["w"]))
               or (nxt and nxt["s"] - w["e"] > 0.35)
               or (hook and w["i"] == hook.get("to")))
        if brk and len(cur) == 1 and nxt and nxt["s"] - w["e"] < 0.3 and not re.search(r"[.!?]$", w["w"]) \
                and not (hook and w["i"] == hook.get("to")):
            brk = False
        if brk:
            cards.append(cur); cur = []
    # fold stranded single words into a neighbour
    merged = []
    k = 0
    while k < len(cards):
        c = cards[k]
        if len(c) == 1 and k + 1 < len(cards) and not re.search(r"[.!?,]$", c[0]["w"]) \
                and cards[k + 1][0]["s"] - c[0]["e"] < 0.5 and len(cards[k + 1]) <= 4:
            cards[k + 1] = c + cards[k + 1]; k += 1; continue
        if len(c) == 1 and merged and c[0]["s"] - merged[-1][-1]["e"] < 0.6 and len(merged[-1]) <= 4 \
                and not merged[-1][-1]["w"].endswith("?"):
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
        k += 1
    cards = merged
    out_cards = []
    for k, c in enumerate(cards):
        end = cards[k + 1][0]["s"] if k + 1 < len(cards) else total
        end = min(end, c[-1]["e"] + 0.6)
        ws = []
        for w in c:
            clean = w["w"].upper() if re.match(r"(?i)^(dr|mr|mrs|ms)\.$", w["w"]) else re.sub(r"[.,!?;:]+$", "", w["w"]).upper()
            if hook and hook["from"] <= w["i"] <= hook["to"]:
                clean = w["w"].upper() if re.match(r"(?i)^(dr|mr|mrs|ms)\.$", w["w"]) else re.sub(r"[.,;:]+$", "", w["w"]).upper()
            bare = re.sub(r"[^A-Z0-9']", "", clean.split()[-1]) if clean else ""
            ws.append({"t": clean, "s": w["s"], "key": bare in kw or clean in kw,
                       "hl": bool(hook) and w["i"] in range(hook.get("highlight", [-1, -2])[0], hook.get("highlight", [-1, -2])[1] + 1)})
        out_cards.append({"s": c[0]["s"], "e": round(end, 3), "words": ws,
                          "hook": bool(hook) and c[0]["i"] <= hook.get("to", -1)})

    # ---- 4. inserts, CTA, sfx -------------------------------------------------
    byi = {w["i"]: w for w in tw}
    def wt(i, side):
        for d in range(0, 6):
            for j in ((i + d, i - d) if side == "s" else (i - d, i + d)):
                if j in byi: return byi[j][side]
        return None
    inserts, sfx = [], []
    for ins in E.get("inserts", []):
        s = wt(ins["words"][0], "s") - 0.12; e = wt(ins["words"][1], "e") + 0.18
        if e - s < 1.4: e = s + 1.4
        def resolve(o):  # word indices under "at"/"mark"/"link" -> edited time
            if isinstance(o, dict):
                return {k: (wt(v, "s") if k in ("at", "mark", "link") and isinstance(v, int) else resolve(v)) for k, v in o.items()}
            if isinstance(o, list):
                return [resolve(x) for x in o]
            return o
        d = resolve({k: v for k, v in ins.items() if k != "words"}); d["s"], d["e"] = round(s, 3), round(e, 3)
        inserts.append(d)
    for k, d in enumerate(inserts):            # avoid overlaps
        if k + 1 < len(inserts) and d["e"] > inserts[k + 1]["s"] - 0.05:
            d["e"] = inserts[k + 1]["s"] - 0.05
    prev_e = -9
    for d in inserts:
        if d["s"] - prev_e > 0.3:
            sfx.append({"f": "whoosh/fs830856.ogg", "t": max(d["s"] - 0.12, 0), "g": -6})
        sfx.append({"f": "pop/fs527522.ogg", "t": d["s"] + 0.25, "g": -9})
        flags = d.get("flag") or []
        for f in [flags] if isinstance(flags, dict) else flags:
            sfx.append({"f": "pop/fs202230.ogg", "t": f["at"], "g": -8})
        for it in d.get("items", []) + d.get("bars", []):
            if isinstance(it.get("mark"), (int, float)): sfx.append({"f": "pop/fs323738.ogg", "t": it["mark"], "g": -10})
        prev_e = d["e"]
    sfx.insert(0, {"f": "impact/fs524817.ogg", "t": 0.02, "g": -10})
    cta = None
    if E.get("cta"):
        cs = wt(E["cta"]["from_word"], "s")
        cta = dict(E["cta"], s=cs, e=total)
        sfx.append({"f": "pop/fs323738.ogg", "t": cs, "g": -7})

    tl = {"w": W, "h": H, "fps": FPS, "duration": round(total, 3), "caption_y": E.get("caption_y", 0.68), "logo_text": E.get("logo_text"),
          "logo": os.path.abspath(os.path.join(os.path.dirname(a.edit), E["logo"])) if E.get("logo") else None,
          "logo_dark_bg": os.path.abspath(os.path.join(os.path.dirname(a.edit), E["logo_dark_bg"])) if E.get("logo_dark_bg") else None,
          "cards": out_cards, "inserts": inserts, "cta": cta,
          "zooms": [{"s": o, "z": z} for o, z in zip(offs, zooms)], "sfx": sfx}
    json.dump(tl, open(os.path.join(a.out, "timeline.json"), "w"), indent=1)
    print(f"kept {len(keep)} segments, {total:.2f}s (from {E['end'] - E.get('start', 0):.2f}s); "
          f"{len(out_cards)} cards, {len(inserts)} inserts")
    if a.timeline_only:
        return

    # ---- 5. picture: normalise, cut, zoom, grade --------------------------------
    norm = os.path.join(a.out, "norm.mp4")
    if not os.path.exists(norm):
        sh(["ffmpeg", "-y", "-v", "error", "-i", a.raw, "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},"
            "unsharp=5:5:0.6:5:5:0,eq=contrast=1.06:saturation=1.10:gamma=0.98,vignette=PI/5",
            "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-g", "15",
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", norm.replace(".mp4", ".mov") if False else norm])
    fc, vlab, alab = [], [], []
    for k, ((s, e), z) in enumerate(zip(keep, zooms)):
        v = f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS"
        if z != 1.0:
            cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
            ax, ay = E.get("zoom_anchor", ANCHOR)
            x = int(min(max(ax * W - cw * ax, 0), W - cw))
            y = int(min(max(ay * H - ch * ay, 0), H - ch))
            v += f",crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos"
        fc.append(v + f",setsar=1[v{k}]")
        d = e - s
        fc.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={max(d - 0.012, 0):.3f}:d=0.012[a{k}]")
        vlab.append(f"[v{k}]"); alab.append(f"[a{k}]")
    n = len(keep)
    fc.append("".join(vlab) + f"concat=n={n}:v=1:a=0[vout]")
    fc.append("".join(alab) + f"concat=n={n}:v=0:a=1[aout]")
    script = os.path.join(a.out, "cut.fc"); open(script, "w").write(";\n".join(fc))
    sh(["ffmpeg", "-y", "-v", "error", "-i", norm, "-filter_complex_script", script,
        "-map", "[vout]", "-c:v", "libx264", "-crf", "15", "-preset", "fast", "-r", str(FPS),
        os.path.join(a.out, "base.mp4"),
        "-map", "[aout]", "-c:a", "pcm_s16le", os.path.join(a.out, "voice_raw.wav")])

    # ---- 6. audio: clean voice, music bed, sfx ----------------------------------
    voice = os.path.join(a.out, "voice.wav")
    sh(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(a.out, "voice_raw.wav"), "-af",
        "highpass=f=80,afftdn=nf=-28,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2,"
        "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", "48000", "-ac", "2", voice])
    ins_ = ["-i", voice]; parts = ["[0:a]asplit=2[vo][vosc]" if E.get("music") else "[0:a]volume=1[vo]"]; mix = ["[vo]"]; k = 1
    if E.get("music"):
        mpath = os.path.normpath(os.path.join(ROOT, "shorts", E["music"]))
        ins_ += ["-stream_loop", "-1", "-i", mpath]
        parts.append(f"[{k}:a]atrim=0:{total:.3f},loudnorm=I={E.get('music_lufs', -30)}:TP=-6,"
                     f"afade=t=in:d=0.6,afade=t=out:st={total - 1.5:.3f}:d=1.5,aresample=48000[mu]")
        parts.append("[mu][vosc]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=300[mud]")
        mix.append("[mud]"); k += 1
    for fx in sfx:
        ins_ += ["-i", os.path.join(SFX, fx["f"])]
        ms = int(fx["t"] * 1000)
        parts.append(f"[{k}:a]aresample=48000,volume={fx['g']}dB,adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]"); k += 1
    parts.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.89[out]")
    sh(["ffmpeg", "-y", "-v", "error", *ins_, "-filter_complex", ";".join(parts), "-map", "[out]",
        "-t", f"{total:.3f}", "-ar", "48000", os.path.join(a.out, "audio.wav")])
    print("base + audio ready in", a.out)


if __name__ == "__main__":
    main()
