"""Original 10 s background track for the Black November motion (120 BPM, A minor).
Synthesised from scratch with numpy, so it is free to use in ads. Accents follow the video:
riser into the "50" impact at 0.65 s, swooshes on the % / ribbons, chime when the coupon lands.
Usage: python3 musica.py out.wav
"""
import sys, wave
import numpy as np

SR = 44100
DUR = 10.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)

BPM = 120
BEAT = 60 / BPM
START = 0.65                     # first downbeat = the "50" impact
beats = [START + i * BEAT for i in range(int((DUR - START) / BEAT) + 1)]


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff can be a scalar or an array (for sweeps)."""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def place(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    seg = sig[: N - i] * gain
    L[i:i + len(seg)] += seg * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(seg)] += seg * np.sqrt(0.5 * (1 + pan))


def env(length, a=0.002, d=0.2, curve=4.0):
    n = int(length * SR)
    x = np.arange(n) / SR
    e = np.minimum(x / a, 1.0) * np.exp(-curve * np.maximum(x - a, 0) / d)
    return e


def note(f):
    return 440.0 * 2 ** ((f - 69) / 12)


# ---------------- drums ----------------
def kick():
    n = int(0.45 * SR); x = np.arange(n) / SR
    f = 45 + 110 * np.exp(-x * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-x * 7) * 1.0 + rng.normal(0, 1, n) * np.exp(-x * 120) * 0.08


def clap():
    n = int(0.3 * SR); x = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    bursts = sum(np.exp(-np.maximum(x - d, 0) * 60) * (x >= d) for d in (0, 0.01, 0.022))
    body = noise * (bursts * 0.5 + np.exp(-x * 14) * 0.6)
    return body - lowpass(body, 900)


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR); x = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    hp = noise - lowpass(noise, 7000)
    return hp * np.exp(-x * (14 if open_ else 70))


K, C, HC, HO = kick(), clap(), hat(), hat(True)
for i, b in enumerate(beats):
    place(K, b, 0.95)
    if i % 2 == 1:
        place(C, b, 0.42)
    place(HC, b + BEAT / 2, 0.22, pan=0.25)
    place(HC, b + BEAT / 4, 0.09, pan=-0.2)
    place(HO, b + BEAT / 2, 0.08, pan=0.35) if i % 4 == 3 else None

# sidechain pump curve (ducks music on each kick)
pump = np.ones(N)
for b in beats:
    i = int(b * SR); n = int(BEAT * SR)
    seg = 1 - 0.65 * np.exp(-np.arange(n) / SR * 9)
    pump[i:i + n] = np.minimum(pump[i:i + n], seg[: max(0, min(n, N - i))])

# ---------------- harmony: Am - F - C - G (one chord per bar) ----------------
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55, 60], [55, 59, 62]]
bass_roots = [45, 41, 48, 43]
pad = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N)
bar = 4 * BEAT
for k in range(6):
    s = START + k * bar - (bar if k == 0 else 0) * 0  # bars start at the impact
    if s >= DUR:
        break
    ch = chords[k % 4]
    i0, i1 = int(max(s, 0) * SR), min(int((s + bar) * SR), N)
    x = np.arange(i1 - i0) / SR
    # pad: 3 detuned saws per voice
    for m in ch:
        for det in (-0.12, 0.0, 0.12):
            f = note(m + 12) * 2 ** (det / 12)
            pad[i0:i1] += (2 * ((x * f) % 1) - 1) * 0.05
    # bass: 8th-note offbeat pulse
    fb = note(bass_roots[k % 4])
    for j in range(8):
        a = s + j * BEAT / 2 + BEAT / 4
        n = int(BEAT / 2.2 * SR); xx = np.arange(n) / SR
        sig = (np.sin(2 * np.pi * fb * xx) + 0.35 * np.sin(4 * np.pi * fb * xx)) * np.exp(-xx * 5)
        i = int(a * SR)
        if i < N:
            bass[i:i + n] += sig[: N - i] * 0.5
    # pluck arpeggio, 16ths
    seq = (ch + [ch[0] + 12])
    for j in range(16):
        a = s + j * BEAT / 4
        f = note(seq[j % len(seq)] + 12)
        n = int(0.22 * SR); xx = np.arange(n) / SR
        sig = (2 * ((xx * f) % 1) - 1) * np.exp(-xx * 18) * 0.11
        i = int(a * SR)
        if i < N:
            arp[i:i + n] += sig[: N - i]

pad_cut = 600 + 2200 * np.clip((t - START) / 3.0, 0, 1)         # filter opens after the impact
pad = lowpass(pad, pad_cut) * pump * (t >= START - 0.05)
arp = lowpass(arp, 3800) * pump * (t >= START + 2 * bar * 0)
bass = lowpass(bass, 420) * pump
L += pad * 0.9 + arp * 0.55 + bass * 0.9
R += pad * 0.9 + np.roll(arp, int(0.09 * SR)) * 0.55 + bass * 0.9   # small stereo delay on the arp

# ---------------- intro riser and FX ----------------
n = int(START * SR); x = np.arange(n) / SR
noise = rng.normal(0, 1, n)
riser = lowpass(noise, 300 + 6000 * (x / START) ** 2) * (x / START) ** 2 * 0.35
riser += np.sin(2 * np.pi * np.cumsum(200 + 900 * (x / START) ** 2) / SR) * (x / START) ** 2 * 0.08
place(riser, 0.0, 1.0)

# impact on the "50"
n = int(1.6 * SR); x = np.arange(n) / SR
boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-x * 8)) / SR) * np.exp(-x * 2.6) * 0.9
crash = rng.normal(0, 1, n); crash = (crash - lowpass(crash, 3000)) * np.exp(-x * 3.2) * 0.22
place(boom + crash, START, 1.0)


def swoosh(length=0.45, up=True):
    n = int(length * SR); x = np.arange(n) / SR
    nz = rng.normal(0, 1, n)
    sweep = 500 + 5000 * ((x / length) if up else (1 - x / length))
    return lowpass(nz, sweep) * np.sin(np.pi * x / length) ** 2 * 0.5


place(swoosh(0.4), 0.95, 0.8, pan=0.6)     # % and OFF from the right
place(swoosh(0.5), 1.15, 0.6, pan=-0.6)    # ribbons
place(swoosh(0.55, up=False), 2.0, 0.7)    # coupon flies in

# chime when the coupon lands (A major-ish sparkle)
for k, m in enumerate([81, 88, 93]):
    n = int(1.2 * SR); x = np.arange(n) / SR
    f = note(m)
    sig = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2.01 * f * x)) * np.exp(-x * 4) * 0.13
    place(sig, 2.62 + k * 0.05, 1.0, pan=(-0.3, 0.0, 0.3)[k])

# ---------------- master ----------------
fade = np.clip((DUR - t) / 0.9, 0, 1) ** 1.5
L *= fade; R *= fade
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.15) / np.tanh(1.15)       # gentle saturation / glue
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('ok', sys.argv[1])
