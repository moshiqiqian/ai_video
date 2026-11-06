"""生成一条低调的配乐床：低频脉冲 + 和弦垫 + 琶音 + 段落过渡。

用法：
    python tools/music_bed.py --duration 48 --bpm 96 --out film/audio/music.wav
"""
import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
CHORDS = [
    [220.00, 261.63, 329.63],   # Am
    [174.61, 220.00, 261.63],   # F
    [261.63, 329.63, 392.00],   # C
    [196.00, 246.94, 293.66],   # G
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=30)
    ap.add_argument("--bpm", type=float, default=96)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    dur, bpm = a.duration, a.bpm
    n_total = int(SR * dur)
    beat = 60 / bpm
    bar = beat * 4
    rng = np.random.default_rng(a.seed)
    buf = np.zeros(n_total)

    def add(sig, at, gain=1.0):
        i = int(at * SR)
        if i >= n_total:
            return
        n = min(len(sig), n_total - i)
        buf[i:i + n] += sig[:n] * gain

    def env(n, attack=0.004, decay=0.25):
        tt = np.arange(n) / SR
        return (1 - np.exp(-tt / attack)) * np.exp(-tt / decay)

    for k in range(int(dur / beat)):
        n = int(0.28 * SR)
        tt = np.arange(n) / SR
        sig = np.sin(2 * np.pi * 55 * tt) * 0.5 + np.sin(2 * np.pi * 110 * tt) * 0.2
        add(sig * env(n, 0.004, 0.14), k * beat, 0.30)

    for b in range(int(dur / bar) + 1):
        ch = CHORDS[b % 4]
        n = int(bar * 1.05 * SR)
        tt = np.arange(n) / SR
        sig = np.zeros(n)
        for f in ch:
            for h in (1, 2, 3):
                sig += np.sin(2 * np.pi * f * h * tt) * (1 / h) * 0.05
        e = np.minimum(1, tt / 0.35) * np.minimum(1, (n / SR - tt) / 0.5)
        add(sig * e, b * bar, 0.45)

    for k in range(int(dur / (beat / 2))):
        ch = CHORDS[int(k * beat / 2 / bar) % 4]
        f = ch[k % 3] * 2
        n = int(0.22 * SR)
        tt = np.arange(n) / SR
        sig = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt / 0.05)
        add(sig, k * beat / 2, 0.055)

    for cut in np.arange(bar * 4, dur, bar * 8):
        n = int(0.55 * SR)
        tt = np.arange(n) / SR
        noise = rng.standard_normal(n)
        noise = np.diff(np.concatenate([[0], noise]))
        e = np.minimum(1, tt / 0.05) * np.exp(-np.maximum(0, tt - 0.45) / 0.03) * np.minimum(1, (0.55 - tt) / 0.08)
        add(noise * e, cut - 0.5, 0.10)

    fade = int(0.5 * SR)
    buf[:fade] *= np.linspace(0, 1, fade)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf = buf / max(1e-9, np.max(np.abs(buf))) * 0.55

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, buf.astype(np.float32), SR, subtype="FLOAT")
    print(f"music: {out}  {dur:.1f}s  {bpm:g}bpm")


if __name__ == "__main__":
    main()
