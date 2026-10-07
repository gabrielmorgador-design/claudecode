"""Original music bed + sound design for the 20s CentralGest TV spot.

Everything is synthesised here (no samples, no third-party audio), so there are
no rights to clear. 120 BPM in A minor / C major, with the bar grid anchored on
the 3.3s "IA" impact so every scene change lands on a beat. Event times mirror
the GSAP timeline in ../index.html.

Usage: python3 make_music.py <out.wav>   (48 kHz, 24-bit, stereo, un-normalised)
"""

import sys
import wave

import numpy as np

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)
verb_L = np.zeros(N)
verb_R = np.zeros(N)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(sig, t0, gain=1.0, pan=0.0, verb=0.0):
    """Add a mono signal at time t0 with constant-power pan and a reverb send."""
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    sig = sig[: N - i0] * gain
    gl = np.cos((pan + 1) * np.pi / 4)
    gr = np.sin((pan + 1) * np.pi / 4)
    L[i0 : i0 + len(sig)] += sig * gl
    R[i0 : i0 + len(sig)] += sig * gr
    if verb:
        verb_L[i0 : i0 + len(sig)] += sig * gl * verb
        verb_R[i0 : i0 + len(sig)] += sig * gr * verb


def tvec(d):
    return np.arange(int(d * SR)) / SR


def filt(x, lo=None, hi=None, order=2):
    """Zero-phase FFT band filter with Butterworth-like magnitude."""
    n = len(x)
    if n == 0:
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-6)) ** (2 * order))
    return np.fft.irfft(X * g, n)


def noise(d):
    return rng.standard_normal(int(d * SR))


def adsr(n, a, r, total):
    t = np.arange(n) / SR
    env = np.minimum(1, t / max(a, 1e-4))
    env *= np.clip((total - t) / max(r, 1e-4), 0, 1)
    return env


def saw(f, t, detune=0.0):
    ph = (f * (1 + detune) * t + rng.random()) % 1.0
    return 2 * ph - 1


# ---------------------------------------------------------------- music ----
BEAT = 0.5
GRID0 = 3.3  # bar 1 downbeat = the blue "IA" impact
CHORDS = [  # (start, length, voicing, bass root)
    (GRID0 + 0, 2, [57, 60, 64, 69], 45),  # Am
    (GRID0 + 2, 2, [53, 57, 60, 65], 41),  # F
    (GRID0 + 4, 2, [55, 60, 64, 67], 48),  # C
    (GRID0 + 6, 2, [55, 59, 62, 67], 43),  # G  (breakdown + click)
    (GRID0 + 8, 2, [57, 60, 64, 69], 45),  # Am
    (GRID0 + 10, 2, [53, 57, 60, 65], 41),  # F
    (GRID0 + 12, 0.5, [55, 59, 62, 67], 43),  # G  (turnaround)
]
FINAL_T = 15.8
FINAL = [48, 55, 60, 64, 67, 71, 74]  # Cmaj9

BREAK = (9.3, 10.3)  # drums out while the cursor travels; back in on the click


def in_break(t):
    return BREAK[0] <= t < BREAK[1]


# sidechain envelope from the kick pattern
kick_times = [GRID0 + k * BEAT for k in range(25) if not in_break(GRID0 + k * BEAT)]
duck = np.ones(N)
tt = np.arange(N) / SR
for kt in kick_times:
    m = tt >= kt
    duck[m] *= 1 - 0.5 * np.exp(-(tt[m] - kt) / 0.11)

# intro pad (0 – 3.3): soft, filtered, "waiting"
pad_bus = np.zeros(N)
t = tvec(3.4)
intro = sum(saw(hz(m), t, d) for m in [57, 60, 64] for d in (-0.003, 0.003))
intro = filt(intro, hi=900) * adsr(len(t), 1.2, 0.3, 3.4) * 0.05
pad_bus[: len(intro)] += intro

# main pads
for start, length, voicing, _ in CHORDS:
    dur = length + 0.35
    t = tvec(dur)
    sig = sum(saw(hz(m), t, d) for m in voicing for d in (-0.004, 0.0, 0.004))
    cutoff = 1300 if in_break(start + 0.1) else 2600
    sig = filt(sig, hi=cutoff) * adsr(len(t), 0.06, 0.35, dur) * 0.045
    i0 = int(start * SR)
    pad_bus[i0 : i0 + len(sig)] += sig[: N - i0]
pad_bus *= duck
place(pad_bus, 0, 1.0, 0.0, verb=0.5)

# bass: 8th-note pulses on the root, sub + filtered saw
for start, length, _, root in CHORDS:
    steps = int(length / (BEAT / 2))
    for k in range(steps):
        st = start + k * BEAT / 2
        if in_break(st):
            continue
        t = tvec(0.24)
        f = hz(root)
        s = np.sin(2 * np.pi * f * t) * 0.8 + filt(saw(f, t), hi=500) * 0.5
        s *= np.exp(-t / 0.13) * np.minimum(1, t / 0.004)
        place(s, st, 0.32 if k % 2 == 0 else 0.22)

# arpeggio pluck: 16ths through the chord, an octave up, with dotted-8th echo
pluck_bus = np.zeros(N)
pattern = [0, 1, 2, 3, 2, 1, 2, 3]
for start, length, voicing, _ in CHORDS:
    steps = int(length / (BEAT / 4))
    for k in range(steps):
        st = start + k * BEAT / 4
        m = voicing[pattern[k % len(pattern)]] + 12
        t = tvec(0.3)
        s = (np.sin(2 * np.pi * hz(m) * t) + 0.3 * np.sin(4 * np.pi * hz(m) * t)) * np.exp(-t / 0.09)
        g = 0.05 if in_break(st) else 0.075
        i0 = int(st * SR)
        pluck_bus[i0 : i0 + len(s)] += s[: N - i0] * g * (1.0 if k % 4 == 0 else 0.7)
# intro: sparse, slow plucks (a clock-like "waiting" feel)
for k in range(6):
    st = 0.3 + k * BEAT
    m = [69, 72, 76, 72, 69, 76][k]
    t = tvec(0.4)
    s = np.sin(2 * np.pi * hz(m) * t) * np.exp(-t / 0.12)
    i0 = int(st * SR)
    pluck_bus[i0 : i0 + len(s)] += s * 0.05
echo = np.zeros(N)
d = int(0.375 * SR)
echo[d:] += pluck_bus[:-d] * 0.33
echo[2 * d :] += pluck_bus[: -2 * d] * 0.12
place(pluck_bus, 0, 1.0, -0.15, verb=0.35)
place(echo, 0, 1.0, 0.35, verb=0.4)


# drums
def kick():
    t = tvec(0.4)
    f = 46 + 90 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.2)
    s += filt(noise(0.4), lo=2000) * np.exp(-t / 0.004) * 0.25
    return s


def clap():
    t = tvec(0.25)
    env = np.zeros_like(t)
    for o in (0, 0.011, 0.022):
        m = t >= o
        env[m] += np.exp(-(t[m] - o) / (0.09 if o == 0.022 else 0.006))
    return filt(noise(0.25), lo=900, hi=4500) * env


def hat(dec=0.03):
    t = tvec(0.12)
    return filt(noise(0.12), lo=7000) * np.exp(-t / dec)


for k in range(25):
    bt = GRID0 + k * BEAT
    if bt >= FINAL_T or in_break(bt):
        continue
    place(kick(), bt, 0.55)
    if k % 2 == 1:
        place(clap(), bt, 0.16, 0.0, verb=0.3)
    place(hat(), bt + BEAT / 2, 0.06, 0.3)
    place(hat(0.015), bt + BEAT / 4, 0.025, -0.3)
    place(hat(0.015), bt + 3 * BEAT / 4, 0.025, -0.3)
# snare fill into the final chord
for k, ft in enumerate(np.arange(15.3, 15.8, BEAT / 4)):
    place(clap(), ft, 0.07 + 0.03 * k, 0.0, verb=0.3)

# final chord: wide pad + bell, ringing out
t = tvec(4.1)
fin = sum(saw(hz(m), t, d) for m in FINAL for d in (-0.005, 0.005))
fin = filt(fin, hi=2400) * adsr(len(t), 0.02, 2.2, 4.1) * np.exp(-t / 2.4) * 0.05
place(fin, FINAL_T, 1.0, 0.0, verb=0.6)
place(np.sin(2 * np.pi * hz(36) * t) * np.exp(-t / 0.9) * 0.6, FINAL_T)

# ----------------------------------------------------------------- sfx ----


def whoosh(d, up=True):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = noise(d)
    lo = filt(x, hi=900)
    hi_ = filt(x, lo=2500, hi=9000)
    p = t / d
    e_lo = np.sin(np.pi * np.clip(p * (1.3 if up else 0.8), 0, 1)) ** 2
    e_hi = np.sin(np.pi * np.clip(p if up else 1 - p, 0, 1)) ** 3
    return lo * e_lo * 0.8 + hi_ * e_hi * 0.5


def riser(d):
    t = tvec(d)
    p = t / d
    x = filt(noise(d), lo=1500) * p**2.5 * 0.4
    f = 220 + 900 * p**2
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * p**2 * 0.15
    return x


def impact():
    t = tvec(1.4)
    f = 60 * np.exp(-t / 0.5) + 32
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    s += filt(noise(1.4), hi=2500) * np.exp(-t / 0.18) * 0.5
    return s


def pop(f=600):
    t = tvec(0.12)
    fr = f * (1 + 0.8 * np.exp(-t / 0.012))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.035)


def blip(m):
    t = tvec(0.18)
    return (np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(6 * np.pi * hz(m) * t)) * np.exp(-t / 0.05) * np.minimum(1, t / 0.002)


def key():
    t = tvec(0.04)
    return filt(noise(0.04), lo=1800, hi=7000) * np.exp(-t / 0.006) + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.01) * 0.6


def paper():
    t = tvec(0.18)
    return filt(noise(0.18), lo=200, hi=2200) * np.exp(-t / 0.05) + np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.04) * 0.5


def mouse_click():
    t = tvec(0.05)
    return filt(noise(0.05), lo=2500) * np.exp(-t / 0.003) + np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.006) * 0.5


def bell(notes, d=1.6):
    t = tvec(d)
    s = np.zeros_like(t)
    for m in notes:
        f = hz(m)
        s += (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.15)) * np.exp(-t / 0.6)
    return s / len(notes)


def shimmer(d=0.9):
    s = np.zeros(int(d * SR) + SR)
    notes = [88, 91, 95, 100, 95, 100, 103]
    for k, m in enumerate(notes):
        b = bell([m], 0.8)
        i0 = int(k * 0.06 * SR)
        s[i0 : i0 + len(b)] += b * (1 - k * 0.08)
    return s


# S1: paper drops, badge, typing, underline swipe
for i in range(5):
    place(paper(), 0.38 + i * 0.13, 0.45, 0.25, verb=0.1)
place(pop(520), 0.95, 0.35, 0.4, verb=0.2)
for k in range(1, 20):
    place(key(), 1.15 + k * (1.6 / 19), 0.22 * (0.8 + 0.4 * rng.random()), 0.3)
place(whoosh(0.35), 1.02, 0.18, -0.4)
# the AI arrives
place(riser(1.1), 2.25, 0.7, 0.0, verb=0.3)
place(shimmer(), 2.7, 0.25, 0.3, verb=0.5)
place(whoosh(0.6), 2.85, 0.5, 0.2)
place(impact(), GRID0, 0.85, 0.0, verb=0.4)
# S2
place(pop(700), 3.42, 0.25, 0.0, verb=0.2)
place(whoosh(0.3), 4.7, 0.25, 0.3)
# S2 -> S3
place(whoosh(0.45, up=False), 6.05, 0.45, 0.0)
place(whoosh(0.4), 6.3, 0.3, -0.5)
place(whoosh(0.4), 6.37, 0.3, 0.5)
# reading beam: soft scanning tone
t = tvec(2.2)
scan = np.sin(2 * np.pi * (1200 + 300 * np.sin(2 * np.pi * 3 * t)) * t) * 0.04
scan += filt(noise(2.2), lo=4000, hi=9000) * 0.03
scan *= adsr(len(t), 0.2, 0.3, 2.2)
place(scan, 6.85, 1.0, -0.3, verb=0.3)


# field fills: ascending blips, matched to the beam timing
def t_at(y):
    return 6.9 + (y - 20) / 720 * 2.1


fills = [t_at(70) + 0.42, t_at(70) + 0.5, t_at(176) + 0.42] + [t_at(y) + 0.42 for y in (324, 376, 428, 480)] + [t_at(600) + 0.42]
scale = [76, 79, 81, 83, 84, 86, 88, 91]
for k, ft in enumerate(fills):
    place(blip(scale[k]), ft, 0.22, 0.4, verb=0.3)
# push-in, click, success
place(whoosh(0.8), 9.25, 0.5, 0.0, verb=0.2)
place(riser(0.7), 9.6, 0.3, 0.0)
place(mouse_click(), 10.32, 0.7, 0.2)
place(bell([84, 88, 91]), 10.42, 0.45, 0.0, verb=0.5)
place(impact(), 10.3, 0.35)
# morph -> S5
place(whoosh(0.5), 11.45, 0.4, 0.0)
place(pop(560), 11.8, 0.4, 0.0, verb=0.3)
place(pop(900), 12.05, 0.35, 0.0, verb=0.3)
# S5 swipes
place(whoosh(0.3), 13.32, 0.25, -0.3)
place(whoosh(0.3), 14.22, 0.25, 0.3)
# implode -> logo
rev = whoosh(0.5)[::-1]
place(rev, 15.3, 0.5, 0.0)
place(impact(), FINAL_T, 0.8, 0.0, verb=0.5)
place(shimmer(), 15.95, 0.3, 0.0, verb=0.6)

# ------------------------------------------------------------ mixdown ----
ir_t = tvec(1.8)
ir_L = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45)
ir_R = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45)
ir_L, ir_R = filt(ir_L, hi=6000), filt(ir_R, hi=6000)


def conv(x, ir):
    n = len(x) + len(ir)
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)]
    return y / np.sqrt(np.sum(ir**2))


L += conv(verb_L, ir_L) * 0.35
R += conv(verb_R, ir_R) * 0.35
L, R = filt(L, lo=28), filt(R, lo=28)

# fades: silent over the 2 black frames at each end (0.08s), gentle tail
fade = np.ones(N)
fade[: int(0.08 * SR)] = 0
tail0, tail1 = int(19.2 * SR), int(19.92 * SR)
fade[tail0:tail1] = np.linspace(1, 0, tail1 - tail0) ** 2
fade[tail1:] = 0
L *= fade
R *= fade

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L, R = np.tanh(L / peak * 1.4) / np.tanh(1.4) * 0.7, np.tanh(R / peak * 1.4) / np.tanh(1.4) * 0.7

pcm = (np.stack([L, R], axis=1) * (2**23 - 1)).astype(np.int32)
b24 = pcm.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(3)
    w.setframerate(SR)
    w.writeframes(b24)
print("ok", sys.argv[1])
