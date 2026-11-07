#!/usr/bin/env python3
"""vid.py — one ffmpeg-based toolkit behind the video skills in .claude/skills/.

Every subcommand reads an input file and writes a new output; nothing is edited in place.

  probe          IN                          duration, size, fps, audio
  silence-cut    IN OUT [--noise -32] [--min 0.45] [--pad 0.08]
  trim           IN OUT --start S [--end E]  (or --keep "0-4.5,7-12")
  concat         OUT IN1 IN2 ...
  transcribe     IN [--out base] [--model small] [--lang en] [--translate]
  fillers        IN OUT [--words um,uh,like] [--min-silence 0.45]
  captions       IN SUBS OUT [--style reel|clean|bold|karaoke] [--pos bottom|middle]
  reframe        IN OUT [--mode crop|blur|fit] [--x 0.5] [--w 1080 --h 1920]
  grade          IN OUT [--look warm|teal-orange|film|cool|bw|punchy] [--lut file.cube]
  audio-clean    IN OUT [--denoise 12] [--lufs -14]
  music          IN MUSIC OUT [--music-db -18] [--duck]
  scenes         IN [--threshold 10]
  frames         IN DIR [--n 12] [--scenes]
  contact-sheet  IN OUT.jpg [--n 16] [--cols 4]
  clips          IN OUTDIR --ranges "12-41,95-130" [--vertical] [--captions SUBS]
  broll          IN BROLL OUT --at 5 [--dur 3] [--pip]
  thumbnail      IN OUT.jpg --text "HOOK" [--at 3.2] [--w 1280 --h 720]
  export         IN OUT [--preset reels|shorts|tiktok|youtube|square|web]

Transcription needs faster-whisper:  pip install faster-whisper
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

FFMPEG = shutil.which('ffmpeg') or 'ffmpeg'
FFPROBE = shutil.which('ffprobe') or 'ffprobe'
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p']
AENC = ['-c:a', 'aac', '-b:a', '192k']
FILLERS = ['um', 'uh', 'erm', 'er', 'ah', 'hmm', 'mm', 'like', 'you know', 'i mean', 'sort of', 'kind of', 'basically', 'actually', 'literally', 'so yeah']


def run(cmd, capture=False):
    if not capture:
        print('$', ' '.join(map(str, cmd)), file=sys.stderr)
    r = subprocess.run(list(map(str, cmd)), capture_output=capture, text=True)
    if r.returncode:
        if capture:
            sys.stderr.write(r.stderr[-3000:])
        sys.exit(f'command failed ({r.returncode})')
    return r


def ff(*args):
    return run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-nostats', '-y', *args])


def probe(path):
    r = run([FFPROBE, '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', path], capture=True)
    d = json.loads(r.stdout)
    v = next((s for s in d['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in d['streams'] if s['codec_type'] == 'audio'), None)
    fps = None
    if v and v.get('avg_frame_rate', '0/0') != '0/0':
        n, m = v['avg_frame_rate'].split('/')
        fps = round(int(n) / int(m), 3)
    return {
        'duration': float(d['format'].get('duration', 0)),
        'width': v and v['width'], 'height': v and v['height'], 'fps': fps,
        'has_audio': a is not None,
    }


def keep_segments(src, out, keep):
    """Re-encode only the [start, end] ranges in `keep` and join them."""
    keep = [(max(0, s), e) for s, e in keep if e - s > 0.05]
    if not keep:
        sys.exit('nothing left to keep')
    info = probe(src)
    parts, n = [], len(keep)
    for i, (s, e) in enumerate(keep):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];")
        if info['has_audio']:
            parts.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}];")
    if info['has_audio']:
        ins = ''.join(f'[v{i}][a{i}]' for i in range(n))
        graph = ''.join(parts) + f'{ins}concat=n={n}:v=1:a=1[v][a]'
        maps = ['-map', '[v]', '-map', '[a]', *AENC]
    else:
        ins = ''.join(f'[v{i}]' for i in range(n))
        graph = ''.join(parts) + f'{ins}concat=n={n}:v=1:a=0[v]'
        maps = ['-map', '[v]']
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
        f.write(graph)
    ff('-i', src, '-filter_complex_script', f.name, *maps, *ENC, '-movflags', '+faststart', out)
    os.unlink(f.name)
    kept = sum(e - s for s, e in keep)
    print(f'kept {len(keep)} segments, {kept:.1f}s of {info["duration"]:.1f}s ({info["duration"] - kept:.1f}s removed)')


def detect_silence(src, noise, min_dur):
    r = subprocess.run([FFMPEG, '-hide_banner', '-i', src, '-af', f'silencedetect=noise={noise}dB:d={min_dur}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    return list(zip(starts, ends + [probe(src)['duration']] * (len(starts) - len(ends))))


def invert(silences, dur, pad):
    keep, t = [], 0.0
    for s, e in silences:
        if s + pad > t:
            keep.append((t, min(dur, s + pad)))
        t = max(t, e - pad)
    if t < dur:
        keep.append((t, dur))
    return keep


def parse_ranges(text):
    out = []
    for part in text.split(','):
        a, b = part.strip().split('-')
        out.append((ts(a), ts(b)))
    return out


def ts(x):
    """'83.5', '1:23.5' or '0:01:23.5' -> seconds."""
    x = str(x).strip()
    sec = 0.0
    for p in x.split(':'):
        sec = sec * 60 + float(p)
    return sec


def srt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f'{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)) % 1000:03}'


def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f'{int(h)}:{int(m):02}:{s:05.2f}'


# ---------------------------------------------------------------- transcription
def transcribe(src, model='small', lang=None, translate=False):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit('transcription needs faster-whisper:  pip install faster-whisper')
    m = WhisperModel(model, device='auto', compute_type='int8')
    segs, info = m.transcribe(src, language=lang, task='translate' if translate else 'transcribe',
                              word_timestamps=True, vad_filter=True)
    words, lines = [], []
    for s in segs:
        lines.append({'start': s.start, 'end': s.end, 'text': s.text.strip()})
        for w in s.words or []:
            words.append({'start': w.start, 'end': w.end, 'word': w.word.strip()})
    return {'language': info.language, 'segments': lines, 'words': words}


def write_srt(segments, path):
    with open(path, 'w') as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")


def read_srt(path):
    blocks = re.split(r'\n\s*\n', open(path, encoding='utf-8-sig').read().strip())
    out = []
    for b in blocks:
        lines = b.strip().splitlines()
        tl = next((i for i, l in enumerate(lines) if '-->' in l), None)
        if tl is None:
            continue
        a, b2 = [x.strip().replace(',', '.') for x in lines[tl].split('-->')]
        out.append({'start': ts(a), 'end': ts(b2.split()[0]), 'text': ' '.join(lines[tl + 1:])})
    return out


def chunk_words(words, max_words=3, max_gap=0.6):
    """Group word timestamps into short caption chunks (for punchy reels captions)."""
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w['start'] - cur[-1]['end'] > max_gap or cur[-1]['word'][-1:] in '.?!,'):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


STYLES = {
    #        font size(% of height), primary, outline, outline w, shadow, bold, uppercase, box
    'reel':     (5.2, '&H00FFFFFF', '&H00000000', 6, 0, 1, True, False),
    'bold':     (6.0, '&H0000E5FF', '&H00000000', 7, 2, 1, True, False),
    'clean':    (3.6, '&H00FFFFFF', '&H80000000', 2, 0, 0, False, True),
    'karaoke':  (5.2, '&H00FFFFFF', '&H00000000', 6, 0, 1, True, False),
}


def build_ass(chunks_or_segments, w, h, style, pos, karaoke_words=None, font='Poppins'):
    size, prim, outc, outw, shadow, bold, upper, box = STYLES[style]
    fs = int(h * size / 100)
    align = {'bottom': 2, 'middle': 5, 'top': 8}[pos]
    marginv = int(h * (0.18 if pos == 'bottom' else 0.08))
    border = 3 if box else 1
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fs},{prim},&H0000E5FF,{outc},&H80000000,{-1 if bold else 0},0,0,0,100,100,0,0,{border},{outw},{shadow},{align},{int(w*0.08)},{int(w*0.08)},{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pop = r'{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}'
    if karaoke_words is not None:
        for ch in karaoke_words:
            text = ''.join(f"{{\\k{max(1, int((w_['end'] - w_['start']) * 100))}}}{w_['word']} " for w_ in ch)
            text = text.upper() if upper else text
            ev.append(f"Dialogue: 0,{ass_time(ch[0]['start'])},{ass_time(ch[-1]['end'] + 0.05)},Default,,0,0,0,,{pop}{text.strip()}")
    else:
        for s in chunks_or_segments:
            text = s['text'].upper() if upper else s['text']
            ev.append(f"Dialogue: 0,{ass_time(s['start'])},{ass_time(s['end'])},Default,,0,0,0,,{pop if style != 'clean' else ''}{text}")
    return hdr + '\n'.join(ev) + '\n'


def ffpath(p):
    """Escape a path for use inside an ffmpeg filter argument."""
    return os.path.abspath(p).replace('\\', '/').replace(':', r'\:').replace("'", r"\'")


def fonts_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, '..', 'fonts')
    return d if os.path.isdir(d) else None


def burn(src, ass_path, out):
    fd = fonts_dir()
    vf = f"ass='{ffpath(ass_path)}'" + (f":fontsdir='{ffpath(fd)}'" if fd else '')
    ff('-i', src, '-vf', vf, *ENC, '-c:a', 'copy', '-movflags', '+faststart', out)


# ---------------------------------------------------------------- commands
def cmd_probe(a):
    print(json.dumps(probe(a.input), indent=2))


def cmd_silence_cut(a):
    dur = probe(a.input)['duration']
    sil = detect_silence(a.input, a.noise, a.min)
    print(f'found {len(sil)} silences >= {a.min}s below {a.noise}dB')
    keep_segments(a.input, a.output, invert(sil, dur, a.pad))


def cmd_trim(a):
    if a.keep:
        keep_segments(a.input, a.output, parse_ranges(a.keep))
        return
    s = ts(a.start or 0)
    e = ts(a.end) if a.end else probe(a.input)['duration']
    ff('-ss', f'{s:.3f}', '-i', a.input, '-t', f'{e - s:.3f}', *ENC, *AENC, '-movflags', '+faststart', a.output)


def cmd_concat(a):
    n = len(a.inputs)
    info = probe(a.inputs[0])
    w, h, fps = info['width'], info['height'], info['fps'] or 30
    ins, graph = [], ''
    for i, p in enumerate(a.inputs):
        ins += ['-i', p]
        graph += f'[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}];'
        if probe(p)['has_audio']:
            graph += f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];'
        else:
            graph += f'anullsrc=r=48000:cl=stereo,atrim=0:{probe(p)["duration"]}[a{i}];'
    graph += ''.join(f'[v{i}][a{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[v][a]'
    ff(*ins, '-filter_complex', graph, '-map', '[v]', '-map', '[a]', *ENC, *AENC, '-movflags', '+faststart', a.output)


def cmd_transcribe(a):
    base = a.out or os.path.splitext(a.input)[0]
    t = transcribe(a.input, a.model, a.lang, a.translate)
    write_srt(t['segments'], base + '.srt')
    json.dump(t, open(base + '.words.json', 'w'), indent=1)
    with open(base + '.txt', 'w') as f:
        for s in t['segments']:
            f.write(f"[{s['start']:7.2f}] {s['text']}\n")
    print(f"language={t['language']}  -> {base}.srt, {base}.words.json, {base}.txt")


def cmd_fillers(a):
    fill = [w.strip().lower() for w in (a.words.split(',') if a.words else FILLERS)]
    t = transcribe(a.input, a.model, a.lang)
    words = t['words']
    norm = lambda s: re.sub(r"[^a-z' ]", '', s.lower()).strip()
    cut = []
    i = 0
    while i < len(words):
        hit = False
        for f in sorted(fill, key=lambda x: -len(x.split())):
            k = len(f.split())
            if ' '.join(norm(w['word']) for w in words[i:i + k]) == f:
                cut.append((words[i]['start'], words[i + k - 1]['end']))
                i += k
                hit = True
                break
        if not hit:
            i += 1
    print(f'filler words: {len(cut)}')
    cut += detect_silence(a.input, a.noise, a.min_silence)
    cut.sort()
    merged = []
    for s, e in cut:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    keep_segments(a.input, a.output, invert(merged, probe(a.input)['duration'], a.pad))


def cmd_captions(a):
    info = probe(a.input)
    w, h = info['width'], info['height']
    ass = tempfile.NamedTemporaryFile('w', suffix='.ass', delete=False).name
    if a.subs.endswith('.ass'):
        shutil.copy(a.subs, ass)
    elif a.subs.endswith('.json'):
        words = json.load(open(a.subs))['words']
        chunks = chunk_words(words, a.max_words)
        if a.style == 'karaoke':
            content = build_ass(None, w, h, a.style, a.pos, karaoke_words=chunks, font=a.font)
        else:
            segs = [{'start': c[0]['start'], 'end': c[-1]['end'] + 0.05, 'text': ' '.join(x['word'] for x in c)} for c in chunks]
            content = build_ass(segs, w, h, a.style, a.pos, font=a.font)
        open(ass, 'w').write(content)
    else:
        open(ass, 'w').write(build_ass(read_srt(a.subs), w, h, a.style, a.pos, font=a.font))
    burn(a.input, ass, a.output)
    os.unlink(ass)


def reframe_filter(mode, x, W, H):
    if mode == 'crop':
        return (f"scale=-2:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(iw-{W})*{x}:(ih-{H})/2,setsar=1")
    if mode == 'fit':
        return f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    # blur: blurred, zoomed copy fills the frame behind the full shot
    return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.08[bg];"
            f"[b]scale={W}:-2:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


def cmd_reframe(a):
    ff('-i', a.input, '-filter_complex', reframe_filter(a.mode, a.x, a.w, a.h), *ENC, '-c:a', 'copy', '-movflags', '+faststart', a.output)


LOOKS = {
    'warm': "colorbalance=rs=0.06:gs=0.01:bs=-0.06:rm=0.04:bm=-0.04,eq=saturation=1.08:contrast=1.04",
    'cool': "colorbalance=rs=-0.05:bs=0.07:rm=-0.03:bm=0.04,eq=saturation=0.98:contrast=1.05",
    'teal-orange': "colorbalance=rs=-0.08:gs=-0.02:bs=0.10:rh=0.10:gh=0.02:bh=-0.10,eq=saturation=1.12:contrast=1.08",
    'film': "curves=preset=medium_contrast,colorbalance=rs=0.03:bs=-0.02:rh=0.04:bh=-0.03,eq=saturation=0.9,noise=alls=6:allf=t,vignette=PI/5",
    'bw': "hue=s=0,curves=preset=increase_contrast,vignette=PI/5",
    'punchy': "eq=saturation=1.25:contrast=1.1:gamma=0.98,unsharp=5:5:0.6",
}


def cmd_grade(a):
    vf = f"lut3d='{ffpath(a.lut)}'" if a.lut else LOOKS[a.look]
    if a.strength < 1 and not a.lut:
        vf = f"split[o][g];[g]{vf}[gg];[o][gg]blend=all_mode=normal:all_opacity={a.strength}"
        ff('-i', a.input, '-filter_complex', vf, *ENC, '-c:a', 'copy', a.output)
    else:
        ff('-i', a.input, '-vf', vf, *ENC, '-c:a', 'copy', a.output)


def cmd_audio_clean(a):
    af = (f"highpass=f=80,lowpass=f=14000,afftdn=nr={a.denoise}:nf=-40,"
          "acompressor=threshold=-20dB:ratio=3:attack=10:release=200,"
          "equalizer=f=3000:t=q:w=1.2:g=2,"
          f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11")
    ff('-i', a.input, '-af', af, '-c:v', 'copy', *AENC, a.output)


def cmd_music(a):
    dur = probe(a.input)['duration']
    if a.duck:
        g = (f"[1:a]volume={a.music_db}dB,atrim=0:{dur},afade=t=out:st={max(0, dur - 2)}:d=2[m];"
             f"[0:a]asplit[v][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
             f"[v][md]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        g = (f"[1:a]volume={a.music_db}dB,atrim=0:{dur},afade=t=out:st={max(0, dur - 2)}:d=2[m];"
             f"[0:a][m]amix=inputs=2:duration=first:normalize=0[a]")
    if not probe(a.input)['has_audio']:
        g = f"[1:a]volume={a.music_db}dB,atrim=0:{dur},afade=t=out:st={max(0, dur - 2)}:d=2[a]"
    ff('-i', a.input, '-stream_loop', '-1', '-i', a.music, '-filter_complex', g, '-map', '0:v', '-map', '[a]',
       '-c:v', 'copy', *AENC, '-shortest', a.output)


def scene_times(src, threshold):
    r = subprocess.run([FFMPEG, '-hide_banner', '-i', src, '-vf', f'scdet=threshold={threshold}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    return [float(x) for x in re.findall(r'lavfi\.scd\.time: ([\d.]+)', r.stderr)]


def cmd_scenes(a):
    t = scene_times(a.input, a.threshold)
    dur = probe(a.input)['duration']
    bounds = [0.0] + t + [dur]
    for i in range(len(bounds) - 1):
        print(f'scene {i + 1:3}: {bounds[i]:8.2f} -> {bounds[i + 1]:8.2f}  ({bounds[i + 1] - bounds[i]:.2f}s)')
    print(f'{len(bounds) - 1} scenes, avg shot {dur / (len(bounds) - 1):.2f}s')


def sample_times(src, n, scenes=False):
    dur = probe(src)['duration']
    if scenes:
        t = [0.0] + scene_times(src, 10)
        return [min(dur - 0.05, x + 0.3) for x in t][:max(n, 1) * 4]
    return [dur * (i + 0.5) / n for i in range(n)]


def grab(src, t, out, width=None):
    vf = ['-vf', f'scale={width}:-2'] if width else []
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', *vf, '-q:v', '3', out])


def cmd_frames(a):
    os.makedirs(a.outdir, exist_ok=True)
    for t in sample_times(a.input, a.n, a.scenes):
        p = os.path.join(a.outdir, f't{t:08.2f}.jpg')
        grab(a.input, t, p, a.width)
        print(p)


def cmd_contact_sheet(a):
    dur = probe(a.input)['duration']
    rows = -(-a.n // a.cols)
    fps = a.n / dur
    vf = (f"fps={fps},scale={a.width}:-2,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,"
          f"tile={a.cols}x{rows}:padding=6:margin=6")
    ff('-i', a.input, '-vf', vf, '-frames:v', '1', '-q:v', '3', a.output)


def cmd_clips(a):
    os.makedirs(a.outdir, exist_ok=True)
    for i, (s, e) in enumerate(parse_ranges(a.ranges), 1):
        out = os.path.join(a.outdir, f'clip{i:02}.mp4')
        vf = []
        if a.vertical:
            vf = ['-filter_complex', reframe_filter(a.mode, 0.5, 1080, 1920)]
        ff('-ss', f'{s:.3f}', '-i', a.input, '-t', f'{e - s:.3f}', *vf, *ENC, *AENC, '-movflags', '+faststart', out)
        print(out)


def cmd_broll(a):
    info = probe(a.input)
    W, H = info['width'], info['height']
    dur = a.dur or probe(a.broll)['duration']
    if a.pip:
        pw = int(W * 0.38)
        ov = f"[1:v]trim=0:{dur},setpts=PTS-STARTPTS+{a.at}/TB,scale={pw}:-2[b];[0:v][b]overlay=W-w-{int(W*0.05)}:{int(H*0.08)}:enable='between(t,{a.at},{a.at + dur})'[v]"
    else:
        ov = (f"[1:v]trim=0:{dur},setpts=PTS-STARTPTS+{a.at}/TB,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"fade=t=in:st={a.at}:d=0.2:alpha=1,format=yuva420p[b];[0:v][b]overlay=0:0:enable='between(t,{a.at},{a.at + dur})'[v]")
    ff('-i', a.input, '-i', a.broll, '-filter_complex', ov, '-map', '[v]', '-map', '0:a?', *ENC, '-c:a', 'copy', a.output)


def cmd_thumbnail(a):
    t = a.at if a.at is not None else probe(a.input)['duration'] * 0.3
    text = a.text.replace("'", "’").replace(':', r'\:')
    fs = int(a.h * 0.16)
    font = a.fontfile or shutil.which('fc-match') and subprocess.run(['fc-match', '-f', '%{file}', 'DejaVu Sans:bold'], capture_output=True, text=True).stdout
    ffont = f":fontfile='{ffpath(font)}'" if font else ''
    vf = (f"scale={a.w}:{a.h}:force_original_aspect_ratio=increase,crop={a.w}:{a.h},eq=contrast=1.15:saturation=1.3,"
          f"drawbox=x=0:y=ih*0.62:w=iw:h=ih*0.38:color=black@0.55:t=fill,"
          f"drawtext=text='{text}'{ffont}:fontsize={fs}:fontcolor={a.color}:borderw={max(4, fs // 14)}:bordercolor=black:"
          f"x=(w-text_w)/2:y=h*0.81-text_h/2")
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', a.input, '-frames:v', '1', '-vf', vf, '-q:v', '2', a.output])
    print(a.output)


PRESETS = {
    'reels':   (1080, 1920, 30, '-14'), 'shorts': (1080, 1920, 30, '-14'), 'tiktok': (1080, 1920, 30, '-14'),
    'youtube': (1920, 1080, None, '-14'), 'square': (1080, 1080, 30, '-14'), 'web': (1280, 720, 30, '-16'),
}


def cmd_export(a):
    W, H, fps, lufs = PRESETS[a.preset]
    vf = reframe_filter('blur' if a.mode == 'blur' else 'fit' if a.mode == 'fit' else 'crop', 0.5, W, H)
    if fps:
        vf += f',fps={fps}'
    args = ['-i', a.input, '-filter_complex', vf]
    if probe(a.input)['has_audio']:
        args += ['-af', f'loudnorm=I={lufs}:TP=-1.5:LRA=11', *AENC]
    ff(*args, '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
       '-movflags', '+faststart', a.output)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)

    def c(name, fn, *pos):
        s = sp.add_parser(name)
        for x in pos:
            s.add_argument(x)
        s.set_defaults(fn=fn)
        return s

    c('probe', cmd_probe, 'input')
    s = c('silence-cut', cmd_silence_cut, 'input', 'output')
    s.add_argument('--noise', type=float, default=-32); s.add_argument('--min', type=float, default=0.45); s.add_argument('--pad', type=float, default=0.08)
    s = c('trim', cmd_trim, 'input', 'output'); s.add_argument('--start'); s.add_argument('--end'); s.add_argument('--keep')
    s = sp.add_parser('concat'); s.add_argument('output'); s.add_argument('inputs', nargs='+'); s.set_defaults(fn=cmd_concat)
    s = c('transcribe', cmd_transcribe, 'input'); s.add_argument('--out'); s.add_argument('--model', default='small'); s.add_argument('--lang'); s.add_argument('--translate', action='store_true')
    s = c('fillers', cmd_fillers, 'input', 'output'); s.add_argument('--words'); s.add_argument('--model', default='small'); s.add_argument('--lang')
    s.add_argument('--noise', type=float, default=-32); s.add_argument('--min-silence', type=float, default=0.45); s.add_argument('--pad', type=float, default=0.06)
    s = c('captions', cmd_captions, 'input', 'subs', 'output'); s.add_argument('--style', default='reel', choices=list(STYLES))
    s.add_argument('--pos', default='bottom', choices=['bottom', 'middle', 'top']); s.add_argument('--max-words', type=int, default=3); s.add_argument('--font', default='Poppins')
    s = c('reframe', cmd_reframe, 'input', 'output'); s.add_argument('--mode', default='blur', choices=['crop', 'blur', 'fit'])
    s.add_argument('--x', type=float, default=0.5); s.add_argument('--w', type=int, default=1080); s.add_argument('--h', type=int, default=1920)
    s = c('grade', cmd_grade, 'input', 'output'); s.add_argument('--look', default='warm', choices=list(LOOKS)); s.add_argument('--lut'); s.add_argument('--strength', type=float, default=1.0)
    s = c('audio-clean', cmd_audio_clean, 'input', 'output'); s.add_argument('--denoise', type=float, default=12); s.add_argument('--lufs', type=float, default=-14)
    s = c('music', cmd_music, 'input', 'music', 'output'); s.add_argument('--music-db', type=float, default=-18); s.add_argument('--duck', action='store_true')
    s = c('scenes', cmd_scenes, 'input'); s.add_argument('--threshold', type=float, default=10)
    s = c('frames', cmd_frames, 'input', 'outdir'); s.add_argument('--n', type=int, default=12); s.add_argument('--scenes', action='store_true'); s.add_argument('--width', type=int, default=768)
    s = c('contact-sheet', cmd_contact_sheet, 'input', 'output'); s.add_argument('--n', type=int, default=16); s.add_argument('--cols', type=int, default=4); s.add_argument('--width', type=int, default=360)
    s = c('clips', cmd_clips, 'input', 'outdir'); s.add_argument('--ranges', required=True); s.add_argument('--vertical', action='store_true'); s.add_argument('--mode', default='crop', choices=['crop', 'blur', 'fit'])
    s = c('broll', cmd_broll, 'input', 'broll', 'output'); s.add_argument('--at', type=float, required=True); s.add_argument('--dur', type=float); s.add_argument('--pip', action='store_true')
    s = c('thumbnail', cmd_thumbnail, 'input', 'output'); s.add_argument('--text', required=True); s.add_argument('--at', type=float)
    s.add_argument('--w', type=int, default=1280); s.add_argument('--h', type=int, default=720); s.add_argument('--color', default='#FFE600'); s.add_argument('--fontfile')
    s = c('export', cmd_export, 'input', 'output'); s.add_argument('--preset', default='reels', choices=list(PRESETS)); s.add_argument('--mode', default='blur', choices=['crop', 'blur', 'fit'])

    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
