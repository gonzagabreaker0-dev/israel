"""Builds the reel's soundtrack: an original lo-fi bed, cinematic sound design
synced to the picture, and a trailer-style voice-over (festival + mbrola us2),
mixed in stereo with the music ducked under the voice.

    python3 audio/make_audio.py   -> out/music.wav, out/sfx.wav, out/voice.wav,
                                     out/mix.wav (everything), out/mix-novoice.wav
"""
import os
import subprocess
import wave

import numpy as np

SR = 44100
DUR = 60.0
N = int(SR * DUR)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

# Voice-over: (start s, line). Ellipses give the narrator trailer-style pauses.
VO = [
    (1.0, "Every great day... begins with one cup."),
    (4.9, "Welcome... to Israel Coffee Shop."),
    (10.6, "It starts... with the bean."),
    (13.9, "Hand picked. Fresh roasted."),
    (20.8, "Every shot... pulled to perfection."),
    (25.4, "Rich. Bold. Velvety."),
    (32.3, "Every cup... a little work of art."),
    (42.4, "Great coffee. Fast wifi. Space to create."),
    (46.6, "This... is your daily ritual."),
    (53.6, "Israel Coffee Shop."),
    (56.3, "Visit us today."),
]


# ------------------------------------------------------------------ io
def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def read_wav_mono(path):
    with wave.open(path, 'rb') as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x) * SR / sr) * sr / SR, np.arange(len(x)), x)
    return x


# ------------------------------------------------------------------ dsp helpers
def tt(n):
    return np.arange(n) / SR


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def band(x, lo, hi):
    """Static FFT band-pass."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def sweep(x, lo_fn, hi_fn, block=2048):
    """Time-varying band-pass via overlapped FFT blocks; lo_fn/hi_fn take progress 0..1."""
    hop = block // 2
    win = np.hanning(block)
    y = np.zeros(len(x) + block)
    xp = np.concatenate([x, np.zeros(block)])
    f = np.fft.rfftfreq(block, 1 / SR)
    for i in range(0, len(x), hop):
        p = i / max(1, len(x))
        X = np.fft.rfft(xp[i:i + block] * win)
        X[(f < lo_fn(p)) | (f > hi_fn(p))] = 0
        y[i:i + block] += np.fft.irfft(X, block)
    return y[:len(x)]


def reverb(x, sec=2.2, mix=0.35, seed=1):
    """Convolution reverb with a decaying-noise impulse response (stereo out)."""
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = tt(n)
    out = []
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-t * 6.9 / sec)
        ir = band(ir, 120, 7000)
        ir /= np.sqrt(np.sum(ir ** 2))
        L = len(x) + n
        wet = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
        out.append(x * (1 - mix) + wet * mix)
    return np.stack(out, 1)


def stereo(x, pan=0.0):
    """pan -1 (left) .. 1 (right); pan may be an array."""
    a = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def add(buf, x, at, gain=1.0):
    if x.ndim == 1:
        x = stereo(x)
    i = int(at * SR)
    j = min(len(buf), i + len(x))
    if j > i and i >= 0:
        buf[i:j] += x[:j - i] * gain


def env(n, a, r):
    t = tt(n)
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def norm(x, peak=1.0):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ sound design
def boom(sec=3.0, f0=55, f1=28):
    n = int(sec * SR); t = tt(n)
    sub = np.sin(2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t * 3)) / SR) * np.exp(-t * 1.6)
    thump = band(noise(sec), 30, 400) * np.exp(-t * 14)
    return norm(np.tanh(1.6 * (sub + 0.5 * norm(thump))))


def braam(sec=4.5):
    n = int(sec * SR); t = tt(n)
    x = sum(np.sign(np.sin(2 * np.pi * f * t + p)) * a for f, a, p in ((55, 1, 0), (55.4, .8, 1), (82.4, .6, 2), (110, .4, 3)))
    x = band(x, 30, 900)
    a = np.minimum(1, t / 0.25) * np.exp(-np.maximum(0, t - 0.6) * 1.1)
    return norm(np.tanh(x * 1.5) * a)


def whoosh(sec=1.4, lo=200, hi=5000):
    n = int(sec * SR); t = tt(n)
    x = sweep(noise(sec), lambda p: lo + 900 * p, lambda p: lo + 400 + (hi - lo) * np.sin(np.pi * p))
    return stereo(norm(x * np.sin(np.pi * t / sec) ** 3), np.linspace(-0.8, 0.8, n))


def riser(sec=4.0):
    n = int(sec * SR); t = tt(n); p = t / sec
    x = sweep(noise(sec), lambda q: 200 + 3000 * q, lambda q: 900 + 9000 * q)
    tone = np.sin(2 * np.pi * np.cumsum(110 + 770 * p ** 2) / SR)
    return norm((norm(x) + 0.35 * tone) * p ** 2.2)


def impact():
    hit = boom(3.2, 70, 30)
    snap = band(noise(0.5), 800, 9000) * env(int(0.5 * SR), 0.001, 0.05)
    x = np.zeros(len(hit)); x[:len(snap)] += 0.5 * snap
    return reverb(norm(hit + x), 2.8, 0.3)


def chime(freq=1318.5, sec=3.0):
    n = int(sec * SR); t = tt(n)
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.4), (2.76, .5, 2.5), (5.4, .25, 4), (8.93, .12, 6)))
    return reverb(norm(x), 3.5, 0.45, seed=3)


def click(freq=3000):
    n = int(0.03 * SR)
    return band(noise(0.03), freq * 0.6, freq * 1.8) * env(n, 0.0005, 0.004)


def bubble(f=600):
    n = int(0.05 * SR); t = tt(n)
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 6 * t)) / SR) * env(n, 0.002, 0.012)


def bed(seconds, lo, hi, flutter=0.0, rate=8):
    n = int(seconds * SR); t = tt(n)
    x = norm(band(noise(seconds), lo, hi))
    if flutter:
        m = np.convolve(rng.standard_normal(n), np.ones(int(SR / rate)) / int(SR / rate), 'same')
        x *= 1 + flutter * norm(m)
    return x


def fade(x, a, r):
    n = len(x); t = tt(n)
    e = np.minimum(1, t / max(a, 1e-3)) * np.clip((n / SR - t) / max(r, 1e-3), 0, 1)
    return x * (e[:, None] if x.ndim == 2 else e)


def sfx():
    S = np.zeros((N, 2))
    # --- intro: braam + deep hit on the title, riser into the first cut
    add(S, reverb(braam(), 3, 0.35), 0.15, 0.55)
    add(S, impact(), 1.15, 0.5)
    add(S, riser(4.2), 9.0 - 4.2, 0.3)
    # bean vortex: airy swirl + scattered ticks
    add(S, fade(stereo(bed(8.5, 300, 2500, 0.6, 3), np.sin(np.linspace(0, 6, int(8.5 * SR))) * 0.7), 1.5, 1), 0.3, 0.08)
    # --- cuts: whoosh into impact
    for tc, g in ((9, 0.75), (19, 0.6), (31, 0.7), (41, 0.6), (51, 0.65)):
        add(S, whoosh(1.4), tc - 1.0, 0.45)
        add(S, impact(), tc - 0.02, g)
    # --- roast: falling beans, ember crackle, slow-mo hero landing
    for _ in range(140):
        at = 9.3 + rng.random() * 9.5
        add(S, stereo(click(2000 + rng.random() * 3000), rng.random() * 1.6 - 0.8), at, 0.08 + 0.08 * rng.random())
    for _ in range(90):
        at = 9.2 + rng.random() * 9.6
        add(S, stereo(click(5000 + rng.random() * 4000) * 0.7, rng.random() * 2 - 1), at, 0.05)
    add(S, fade(stereo(bed(9.8, 60, 400, 0.4, 2)), 1, 1), 9.1, 0.1)  # roaster rumble
    hero = boom(1.6, 120, 60) * 0.7
    add(S, reverb(hero, 1.5, 0.3), 17.15, 0.35)
    for k in range(7):
        add(S, stereo(click(2500 + 400 * k), (k - 3) / 5), 17.18 + k * 0.035, 0.18)
    # --- espresso: machine hum, pump buzz, pour, steam
    n = int(11.5 * SR); t = tt(n)
    hum = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((50, 1), (100, .5), (150, .3), (300, .1)))
    add(S, fade(stereo(norm(hum) * (1 + 0.1 * np.sin(2 * np.pi * 0.3 * t))), 1.2, 1.5), 19.2, 0.07)
    n = int(8.2 * SR); t = tt(n)
    pump = norm(np.tanh(3 * np.sin(2 * np.pi * 118 * t)) * (1 + 0.3 * np.sin(2 * np.pi * 7 * t)))
    add(S, fade(stereo(band(pump, 80, 2000)), 0.15, 0.4), 20.0, 0.06)
    pour = bed(8.0, 300, 3500, 0.9, 25)
    pour = np.concatenate([pour, np.zeros(int(0.2 * SR))])
    for _ in range(260):
        i = int(rng.random() * 7.8 * SR)
        b = bubble(350 + rng.random() * 900)
        pour[i:i + len(b)] += 0.6 * b
    add(S, fade(stereo(norm(pour), 0.1), 0.3, 0.6), 20.25, 0.16)
    add(S, fade(stereo(bed(8, 2500, 12000, 0.3, 4), 0.3), 2, 2), 22.5, 0.05)  # steam
    # dive into the cup: bubbly swallow
    dive = np.zeros(int(0.8 * SR))
    for _ in range(60):
        i = int(rng.random() * 0.6 * SR)
        b = bubble(250 + rng.random() * 500)
        dive[i:i + len(b)] += b
    add(S, reverb(norm(dive), 1.2, 0.4), 30.55, 0.25)
    # --- latte: soft milk pour, steam
    milk = bed(6.6, 200, 2200, 0.7, 18)
    for _ in range(120):
        i = int(rng.random() * 6.4 * SR)
        b = bubble(250 + rng.random() * 500)
        milk[i:i + len(b)] += 0.4 * b
    add(S, fade(stereo(norm(milk), -0.1), 0.4, 0.5), 32.5, 0.12)
    add(S, fade(stereo(bed(4, 2500, 12000, 0.3, 4)), 1.5, 1.5), 37.5, 0.05)
    add(S, fade(stereo(bed(10, 100, 800, 0.2, 1)), 1, 1), 31, 0.04)  # room tone
    # --- counter: café ambience, cup sliding on wood, clinks
    murmur = bed(10.2, 250, 1400, 0.8, 4) + 0.4 * bed(10.2, 1400, 3500, 0.6, 6)
    add(S, fade(stereo(norm(murmur)), 1, 1.2), 40.9, 0.06)
    n = int(8.6 * SR); t = tt(n)
    u = np.clip((t - 0.2) / 8.4, 0, 1)
    speed = np.where(u < .5, 12 * u ** 2, 12 * (1 - u) ** 2) / 3  # derivative of easeInOut cubic, 0..1
    slide = band(noise(8.6), 700, 3200) * speed * (1 + 0.4 * norm(band(noise(8.6), 5, 40)))
    add(S, stereo(norm(slide), np.linspace(-0.7, 0.4, n)), 41.2, 0.09)
    for at, f in ((43.1, 2637), (45.8, 3136), (47.6, 2349)):
        add(S, chime(f, 1.2) * 0.5, at, 0.08)
    add(S, chime(1760, 2.0), 49.6, 0.08)  # cup settles
    # --- outro: reverse swell, spinning cube flutter, logo impact, shimmer
    n = int(3.2 * SR); t = tt(n); p = t / 3.2
    spin = band(noise(3.2), 300, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(22 * (1 - p) ** 2 + 1) / SR)) * (1 - p) ** 0.5
    add(S, stereo(norm(spin), np.sin(np.linspace(0, 12, n)) * 0.6), 51.0, 0.12)
    add(S, impact(), 54.15, 0.6)
    for k, f in enumerate((1318.5, 1760, 2637)):
        add(S, chime(f, 3), 53.4 + 0.35 * k, 0.12)
    add(S, reverb(boom(4.5, 45, 22), 3.5, 0.4), 58.3, 0.35)  # final low drop under the fade
    t = tt(N)
    S *= (np.clip((DUR - t) / 1.2, 0, 1))[:, None]
    return S


# ------------------------------------------------------------------ music
def note(freq, length, kind, amp):
    n = int(length * SR); t = tt(n)
    if kind == 'keys':
        w = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.001 * t) * np.exp(-t * 3)
             + 0.12 * np.sin(2 * np.pi * freq * 3.99 * t) * np.exp(-t * 6))
        return amp * w * (1 + 0.04 * np.sin(2 * np.pi * 5 * t)) * env(n, 0.01, 1.4)
    if kind == 'bass':
        return amp * (np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(4 * np.pi * freq * t)) * env(n, 0.01, 0.7)
    w = sum(np.sin(2 * np.pi * freq * d * t + p) for d, p in ((1, 0), (1.004, 1), (0.996, 2)))  # pad
    return amp * w / 3 * np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.2)


def music():
    L = np.zeros(N)

    def put(x, at):
        i = int(at * SR); j = min(N, i + len(x))
        if j > i:
            L[i:j] += x[:j - i]

    beat = 60 / 84; bar = beat * 4
    chords = [[53, 57, 60, 64, 67], [52, 55, 59, 62, 66], [50, 53, 57, 60, 64], [48, 52, 55, 59, 62]]
    roots = [41, 40, 38, 36]
    for b in range(int(DUR / bar) + 1):
        t0 = b * bar; ch, root = chords[b % 4], roots[b % 4]
        intro = b < 2
        for k, m in enumerate(ch):
            put(note(midi(m), 2.4, 'keys', 0.06), t0 + k * 0.012)
            if not intro:
                put(note(midi(m), 1.2, 'keys', 0.03), t0 + beat * 2.5 + k * 0.01)
        put(note(midi(ch[-1] + 12), 3.6, 'pad', 0.025), t0)
        put(note(midi(root - 12), 3.6, 'pad', 0.05), t0)  # cinematic low string
        if not intro:
            put(note(midi(root), beat * 1.6, 'bass', 0.22), t0)
            put(note(midi(root + 7), beat * 0.9, 'bass', 0.14), t0 + beat * 2.5)
        for q in range(4):
            tb = t0 + q * beat
            if not intro:
                if q in (0, 2) or (q == 3 and b % 2):
                    n = int(0.35 * SR); t = tt(n)
                    put(0.42 * np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 9), tb + (0.5 * beat if q == 3 else 0))
                if q in (1, 3):
                    n = int(0.25 * SR)
                    put(0.16 * np.convolve(rng.standard_normal(n) * env(n, 0.002, 0.07), np.ones(6) / 6, 'same'), tb + 0.02)
            for h in (0, 0.56):
                n = int(0.06 * SR)
                put((0.035 if intro else 0.05) * np.diff(rng.standard_normal(n + 1)) * env(n, 0.001, 0.012), tb + h * beat)
    L += (rng.random(N) > 0.9993) * rng.standard_normal(N) * 0.08
    k = np.exp(-np.arange(12) / 3.0); L = np.convolve(L, k / k.sum(), 'same')
    t = tt(N)
    L *= np.minimum(1, t / 1.5) * np.clip((DUR - t) / 2.5, 0, 1)
    return reverb(norm(L, 0.8), 1.6, 0.18, seed=5)


# ------------------------------------------------------------------ voice
def voice():
    V = np.zeros(N); spans = []
    tmp = os.path.join(OUT, 'vo'); os.makedirs(tmp, exist_ok=True)
    for i, (at, text) in enumerate(VO):
        txt, raw, fx = (os.path.join(tmp, f'l{i}.{e}') for e in ('txt', 'raw.wav', 'wav'))
        open(txt, 'w').write(text)
        subprocess.run(['text2wave', '-eval', '(voice_us2_mbrola)', '-eval', "(Parameter.set 'Duration_Stretch 1.12)", txt, '-o', raw], check=True)
        # trailer voice: deeper, slower, warm low end, compressed
        subprocess.run(['sox', raw, '-r', str(SR), fx, 'pitch', '-180', 'tempo', '-s', '0.95',
                        'bass', '+7', '120', 'treble', '+3', 'compand', '0.02,0.25', '-60,-60,-30,-14,0,-8', '-4', '-70', '0.02',
                        'norm', '-1'], check=True)
        x = read_wav_mono(fx)
        add_at = int(at * SR)
        V[add_at:add_at + len(x)] += x[:N - add_at]
        spans.append((at, at + len(x) / SR))
        print(f'line {i:2d}: {at:5.1f}s -> {at + len(x) / SR:5.1f}s  {text}')
    for (a0, b0), (a1, _) in zip(spans, spans[1:]):
        assert b0 < a1, f'voice lines overlap at {a1}s'
    return reverb(norm(V, 0.95), 2.4, 0.22, seed=9), spans


if __name__ == '__main__':
    M = music(); X = sfx(); Vo, spans = voice()
    for name, x in (('music', M), ('sfx', X), ('voice', Vo)):
        write_wav(os.path.join(OUT, name + '.wav'), norm(x, 0.95))
    t = tt(N); duck = np.ones(N)
    for a, b in spans:
        duck = np.minimum(duck, 1 - 0.7 * np.clip(np.minimum((t - a + 0.3) / 0.3, (b + 0.5 - t) / 0.5), 0, 1))
    bedmix = norm(M, 1) * 0.42 + norm(X, 1) * 0.8
    write_wav(os.path.join(OUT, 'mix-novoice.wav'), norm(bedmix, 0.95))
    mix = bedmix * duck[:, None] * 0.85 + norm(Vo, 1) * 0.9
    write_wav(os.path.join(OUT, 'mix.wav'), norm(mix, 0.95))
    print('wrote music.wav sfx.wav voice.wav mix.wav mix-novoice.wav')
