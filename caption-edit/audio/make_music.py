"""Original background music bed (A minor, 92 BPM, Am-F-C-G) for the captioned shorts.
Synthesised with numpy only, so it is royalty free.
    python3 make_music.py out.wav [seconds]
"""
import sys, wave
import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 95.0
BPM = 92
BEAT = 60 / BPM
BAR = BEAT * 4
N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)
Lw = np.zeros(N); Rw = np.zeros(N)  # reverb send

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def add(buf, x, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= N: return
    x = x[: N - i]
    buf[i:i + len(x)] += x * gain

def tone(freq, dur, harm=(1, .5, .25, .12), detune=0.0, att=0.02, rel=0.1, decay=None, vib=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for h, a in enumerate(harm, 1):
        y += a * np.sin(2 * np.pi * freq * h * (1 + detune) * t + (0.3 * np.sin(2 * np.pi * vib * t) if vib else 0))
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel)
    if decay: env *= np.exp(-t / decay)
    return y * np.clip(env, 0, 1)

# Am | F | C | G
PROG = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
nbars = int(DUR / BAR) + 1
for b in range(nbars):
    root, chord = PROG[b % 4]
    t0 = b * BAR
    # pad (soft, slow attack, slightly detuned pairs)
    for m in chord:
        for d, pan in ((-0.003, 0.35), (0.003, 0.65)):
            y = tone(hz(m), BAR + 0.6, harm=(1, .35, .15, .06), detune=d, att=0.9, rel=0.9, vib=0.25)
            add(L, y, t0, 0.055 * (1 - pan)); add(R, y, t0, 0.055 * pan)
            add(Lw, y, t0, 0.04); add(Rw, y, t0, 0.04)
    # bass from bar 2
    if b >= 2:
        y = tone(hz(root - 12), BAR - 0.05, harm=(1, .3), att=0.04, rel=0.25)
        add(L, y, t0, 0.20); add(R, y, t0, 0.20)
    # arpeggio plucks (8ths) from bar 1
    if b >= 1:
        order = [0, 1, 2, 1, 0, 1, 2, 1] if b % 2 == 0 else [0, 2, 1, 2, 0, 2, 1, 2]
        for k in range(8):
            m = chord[order[k]] + 12
            y = tone(hz(m), 0.9, harm=(1, .45, .2, .08), att=0.004, rel=0.05, decay=0.22)
            pan = 0.35 + 0.3 * (k % 2)
            g = 0.085 if (k % 2 == 0) else 0.06
            add(L, y, t0 + k * BEAT / 2, g * (1 - pan) * 2); add(R, y, t0 + k * BEAT / 2, g * pan * 2)
            add(Lw, y, t0 + k * BEAT / 2, 0.05); add(Rw, y, t0 + k * BEAT / 2, 0.05)
    # light kick on 1 & 3 and shaker, from bar 4
    if b >= 4:
        for beat in (0, 2):
            n = int(0.28 * SR); t = np.arange(n) / SR
            f = 50 + 70 * np.exp(-t * 28)
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
            add(L, y, t0 + beat * BEAT, 0.22); add(R, y, t0 + beat * BEAT, 0.22)
        for k in range(8):
            n = int(0.05 * SR)
            noise = rng.standard_normal(n); noise = np.diff(noise, prepend=0)  # crude high-pass
            y = noise * np.exp(-np.arange(n) / SR * 90)
            g = 0.035 if k % 2 else 0.02
            add(L, y, t0 + k * BEAT / 2 + BEAT / 4 * 0, g); add(R, y, t0 + k * BEAT / 2, g)

# reverb on send: exponentially decaying noise IR, FFT convolution
ir_n = int(1.8 * SR); ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 2.6)
ir = np.diff(ir, prepend=0) * 0.5 + ir * 0.5
def conv(x):
    n = len(x) + len(ir) - 1; nf = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:len(x)]
L += conv(Lw) * 0.35; R += conv(Rw[::-1])[::-1] * 0.0 + conv(Rw) * 0.35

# fades + normalise
fi, fo = int(2.5 * SR), int(5.0 * SR)
env = np.ones(N); env[:fi] = np.linspace(0, 1, fi) ** 1.5; env[-fo:] = np.linspace(1, 0, fo) ** 1.5
L *= env; R *= env
peak = max(np.abs(L).max(), np.abs(R).max()); L, R = L / peak * 0.7, R / peak * 0.7
out = (np.stack([L, R], 1) * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('wrote', sys.argv[1])
