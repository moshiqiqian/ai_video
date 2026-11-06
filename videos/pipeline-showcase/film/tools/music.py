import numpy as np, soundfile as sf
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SR = 48000
DUR = 48.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)

BPM = 96
beat = 60 / BPM
bar = beat * 4

# A minor: Am F C G, one bar each
CHORDS = [
    [220.00, 261.63, 329.63],   # Am
    [174.61, 220.00, 261.63],   # F
    [261.63, 329.63, 392.00],   # C
    [196.00, 246.94, 293.66],   # G
]

music = np.zeros(N)

def add(sig, at, gain=1.0):
    i = int(at * SR)
    if i >= N:
        return
    n = min(len(sig), N - i)
    music[i:i + n] += sig[:n] * gain

def env(n, a=0.004, d=0.25):
    tt = np.arange(n) / SR
    return (1 - np.exp(-tt / a)) * np.exp(-tt / d)

# sub pulse on beats
for k in range(int(DUR / beat)):
    n = int(0.28 * SR)
    tt = np.arange(n) / SR
    sig = np.sin(2 * np.pi * 55 * tt) * 0.5 + np.sin(2 * np.pi * 110 * tt) * 0.2
    add(sig * env(n, 0.004, 0.14), k * beat, 0.30)

# pad: one chord per bar, soft saw stack
for b in range(int(DUR / bar) + 1):
    ch = CHORDS[b % 4]
    at = b * bar
    n = int(bar * 1.05 * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for f in ch:
        for h in (1, 2, 3):
            sig += np.sin(2 * np.pi * f * h * tt) * (1 / h) * 0.05
    e = np.minimum(1, tt / 0.35) * np.minimum(1, (n / SR - tt) / 0.5)
    add(sig * e, at, 0.45)

# pluck arpeggio on eighths (high register, quiet)
for k in range(int(DUR / (beat / 2))):
    ch = CHORDS[int(k * beat / 2 / bar) % 4]
    f = ch[k % 3] * 2
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt / 0.05)
    add(sig, k * beat / 2, 0.055)

# transition sweeps at scene cuts
for cut in [4.8, 10.2, 15.0, 19.8, 24.6, 29.4, 34.2, 39.0, 44.0]:
    n = int(0.55 * SR)
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.diff(np.concatenate([[0], noise]))
    e = np.minimum(1, tt / 0.05) * np.exp(-np.maximum(0, tt - 0.45) / 0.03) * np.minimum(1, (0.55 - tt) / 0.08)
    add(noise * e, cut - 0.5, 0.10)

# sidechain-ish dip on each bar? keep flat; fades
fade = int(0.5 * SR)
music[:fade] *= np.linspace(0, 1, fade)
music[-fade:] *= np.linspace(1, 0, fade)
music = music / max(1e-9, np.max(np.abs(music))) * 0.55
sf.write(HERE / "audio" / "music.wav", music.astype(np.float32), SR, subtype="FLOAT")
print("music.wav", DUR)
