"""Builds the soundtrack for the reel: an original lo-fi coffee-shop track,
transition whooshes, and a TTS voice-over (festival, cmu_us_slt_arctic_hts),
mixed with the music ducked under the voice.

    python3 audio/make_audio.py            -> out/music.wav, out/voice.wav, out/mix.wav
"""
import os
import subprocess
import wave

import numpy as np

SR = 44100
DUR = 60.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
os.makedirs(OUT, exist_ok=True)
N = int(SR * DUR)
rng = np.random.default_rng(7)

# Voice-over: (start time in seconds, line). Matches the on-screen captions.
VO = [
    (1.2, "Welcome to Israel Coffee Shop. Where great coffee meets great ideas."),
    (10.4, "It all starts with the bean. Hand picked, and freshly roasted, every morning."),
    (20.6, "Every shot is pulled to perfection. Rich. Bold. And velvety smooth."),
    (32.2, "Our baristas craft every cup, like a little work of art."),
    (42.2, "Great coffee. Fast wifi. And space to create. Make it your daily ritual."),
    (53.4, "Israel Coffee Shop. Visit us today."),
]


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype('<i2')
    if data.ndim == 1:
        data = np.stack([data, data], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def read_wav_mono(path):
    with wave.open(path, 'rb') as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x) * SR / sr) * sr / SR, np.arange(len(x)), x)
    return x


def env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def note(freq, length, kind='keys', amp=0.2):
    n = int(length * SR)
    t = np.arange(n) / SR
    if kind == 'keys':  # warm electric piano: fundamental + soft bell partials, slight detune
        w = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.001 * t) * np.exp(-t * 3)
             + 0.12 * np.sin(2 * np.pi * freq * 3.99 * t) * np.exp(-t * 6))
        w *= 1 + 0.04 * np.sin(2 * np.pi * 5 * t)  # tremolo
        return amp * w * env(n, 0.01, 1.4)
    if kind == 'bass':
        return amp * (np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(4 * np.pi * freq * t)) * env(n, 0.01, 0.7)
    if kind == 'pad':
        w = sum(np.sin(2 * np.pi * freq * d * t + p) for d, p in ((1, 0), (1.004, 1), (0.996, 2)))
        a = np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.2)
        return amp * w / 3 * a
    raise ValueError(kind)


def add(buf, x, at):
    i = int(at * SR)
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[: j - i]


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def music():
    L = np.zeros(N)
    bpm = 84
    beat = 60 / bpm
    bar = beat * 4
    # Fmaj9 – Em7 – Dm9 – Cmaj7 (lo-fi ii-V-ish loop)
    chords = [[53, 57, 60, 64, 67], [52, 55, 59, 62, 66], [50, 53, 57, 60, 64], [48, 52, 55, 59, 62]]
    roots = [41, 40, 38, 36]
    nbars = int(DUR / bar) + 1
    for b in range(nbars):
        t0 = b * bar
        ch, root = chords[b % 4], roots[b % 4]
        intro = b < 2
        # keys: chord stab on 1, softer re-hits with swing
        for k, m in enumerate(ch):
            add(L, note(midi(m), 2.4, 'keys', 0.06), t0 + k * 0.012)
            if not intro:
                add(L, note(midi(m), 1.2, 'keys', 0.03), t0 + beat * 2.5 + k * 0.01)
        add(L, note(midi(ch[-1] + 12), 3.6, 'pad', 0.025), t0)
        if not intro:
            add(L, note(midi(root), beat * 1.6, 'bass', 0.22), t0)
            add(L, note(midi(root + 7), beat * 0.9, 'bass', 0.14), t0 + beat * 2.5)
        # drums
        for q in range(4):
            tb = t0 + q * beat
            if not intro:
                if q in (0, 2) or (q == 3 and b % 2):
                    n = int(0.35 * SR); t = np.arange(n) / SR
                    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 9)
                    add(L, 0.42 * kick, tb + (0.5 * beat if q == 3 else 0))
                if q in (1, 3):
                    n = int(0.25 * SR)
                    sn = rng.standard_normal(n) * env(n, 0.002, 0.07)
                    sn = np.convolve(sn, np.ones(6) / 6, 'same')
                    add(L, 0.16 * sn, tb + 0.02)
            for h in (0, 0.56):  # swung hats
                n = int(0.06 * SR)
                hat = np.diff(rng.standard_normal(n + 1)) * env(n, 0.001, 0.012)
                add(L, (0.035 if intro else 0.05) * hat, tb + h * beat)
    # vinyl crackle + room tone
    crackle = (rng.random(N) > 0.9993) * rng.standard_normal(N) * 0.08
    hiss = np.convolve(rng.standard_normal(N) * 0.004, np.ones(20) / 20, 'same')
    L += crackle + hiss
    # lo-fi tone: gentle low-pass
    k = np.exp(-np.arange(12) / 3.0); k /= k.sum()
    L = np.convolve(L, k, 'same')
    # transition whooshes and the outro riser
    for tc in (9, 19, 31, 41, 51):
        n = int(1.6 * SR); t = np.arange(n) / SR
        w = rng.standard_normal(n)
        w = np.convolve(w, np.ones(30) / 30, 'same') * np.sin(np.pi * t / 1.6) ** 2
        add(L, 0.5 * w, tc - 0.9)
    n = int(3 * SR); t = np.arange(n) / SR
    add(L, 0.08 * np.sin(2 * np.pi * (200 + 600 * (t / 3) ** 2) * t) * (t / 3) ** 2, 48)
    # master fade
    t = np.arange(N) / SR
    L *= np.minimum(1, t / 1.5) * np.clip((DUR - t) / 2.5, 0, 1)
    return L / np.max(np.abs(L)) * 0.8


def voice():
    V = np.zeros(N)
    spans = []
    tmp = os.path.join(OUT, 'vo')
    os.makedirs(tmp, exist_ok=True)
    for i, (at, text) in enumerate(VO):
        txt, raw, fx = (os.path.join(tmp, f'l{i}.{e}') for e in ('txt', 'raw.wav', 'wav'))
        open(txt, 'w').write(text)
        subprocess.run(['text2wave', '-eval', '(voice_cmu_us_slt_arctic_hts)', txt, '-o', raw], check=True)
        # warmer, slightly slower, a touch of room
        subprocess.run(['sox', raw, '-r', str(SR), fx, 'tempo', '-s', '0.94', 'pitch', '-60',
                        'bass', '+4', 'treble', '+2', 'reverb', '18', '50', '60', 'norm', '-1'], check=True)
        x = read_wav_mono(fx)
        add(V, x, at)
        spans.append((at, at + len(x) / SR))
        print(f'line {i}: {at:5.1f}s -> {at + len(x) / SR:5.1f}s  {text}')
    return V / np.max(np.abs(V)) * 0.95, spans


if __name__ == '__main__':
    M = music()
    write_wav(os.path.join(OUT, 'music.wav'), M)
    Vo, spans = voice()
    write_wav(os.path.join(OUT, 'voice.wav'), Vo)
    # duck music ~9 dB under the voice, with smooth ramps
    t = np.arange(N) / SR
    duck = np.ones(N)
    for a, b in spans:
        duck = np.minimum(duck, 1 - 0.65 * np.clip(np.minimum((t - a + 0.3) / 0.3, (b + 0.4 - t) / 0.4), 0, 1))
    mix = M * duck * 0.75 + Vo
    write_wav(os.path.join(OUT, 'mix.wav'), mix / np.max(np.abs(mix)) * 0.95)
    print('wrote music.wav voice.wav mix.wav')
