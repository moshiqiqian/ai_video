import numpy as np, soundfile as sf
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SR = 48000
DUR = 22.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)

music = np.zeros(N)
BPM = 96
beat = 60 / BPM

# low pulse on every beat
for k in range(int(DUR / beat)):
    at = k * beat + 0.02
    i0 = int(at * SR)
    d = 0.32
    n = int(d * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt / 0.12) * (1 - np.exp(-tt / 0.004))
    tone = np.sin(2 * np.pi * 55 * tt) * 0.55 + np.sin(2 * np.pi * 110 * tt) * 0.25
    if i0 + n <= N:
        music[i0:i0 + n] += tone * env * 0.35

# soft tick on off-beats
for k in range(int(DUR / beat)):
    at = k * beat + beat / 2
    i0 = int(at * SR)
    n = int(0.04 * SR)
    if i0 + n > N:
        continue
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # cheap high-pass
    noise = np.diff(np.concatenate([[0], noise]))
    tick = noise * np.exp(-tt / 0.006) * 0.08
    music[i0:i0 + n] += tick

# quiet pad: two detuned sines, slow swell
pad = (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 220.6 * t)) * 0.012
pad *= np.clip(t / 3, 0, 1) * np.clip((DUR - t) / 3, 0, 1)
music += pad

# gentle fades
fade = int(0.4 * SR)
music[:fade] *= np.linspace(0, 1, fade)
music[-fade:] *= np.linspace(1, 0, fade)

music = music / max(1e-9, np.max(np.abs(music))) * 0.5
sf.write(HERE / "audio" / "music.wav", music.astype(np.float32), SR, subtype="FLOAT")
print("music.wav", round(DUR, 2))
