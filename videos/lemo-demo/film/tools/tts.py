"""Generate per-line TTS, rebuild lines.json timings, and mix a full voice track."""
import asyncio, json, subprocess, sys
from pathlib import Path
import edge_tts

HERE = Path(__file__).resolve().parent.parent
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+4%"

LINES = [
    {"id": "l1", "t0": 0.9, "text": "不用剪辑软件，也不用生成模型。"},
    {"id": "l2", "t0": 6.2, "text": "每一帧，都是代码算出来的。"},
    {"id": "l3", "t0": 11.6, "text": "文字、图表、声音，同一条时间轴。"},
    {"id": "l4", "t0": 17.6, "text": "这就是下一版的做法。"},
]


def dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


async def main():
    ad = HERE / "audio"
    ad.mkdir(exist_ok=True)
    for ln in LINES:
        mp3 = ad / f"{ln['id']}.mp3"
        com = edge_tts.Communicate(ln["text"], VOICE, rate=RATE)
        await com.save(str(mp3))
        d = dur(mp3)
        ln["t1"] = round(ln["t0"] + d + 0.55, 2)
        ln["dur"] = round(d, 2)
        print(ln["id"], round(d, 2))

    (HERE / "lines.json").write_text(
        json.dumps([{k: v for k, v in l.items() if k != "dur"} for l in LINES],
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # voice track: place each line at its t0 on a 22 s silent bed
    inputs, filters = [], []
    for i, ln in enumerate(LINES):
        inputs += ["-i", str(ad / f"{ln['id']}.mp3")]
        ms = int(ln["t0"] * 1000)
        filters.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(LINES)))
    filters.append(f"{mix}amix=inputs={len(LINES)}:normalize=0,apad,atrim=0:22[out]")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", ";".join(filters), "-map", "[out]",
         "-ar", "48000", "-ac", "2", str(ad / "voice.wav")],
        check=True)
    print("voice.wav")


asyncio.run(main())
