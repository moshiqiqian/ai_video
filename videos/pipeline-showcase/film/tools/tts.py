"""逐句配音 → lines.json 时间 → 拼接整条 voice.wav"""
import asyncio, json, subprocess
from pathlib import Path
import edge_tts

HERE = Path(__file__).resolve().parent.parent
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+8%"
DUR = 48.0

LINES = [
    ("l1", 0.9, "这不是剪辑出来的片子。"),
    ("l2", 5.2, "从一句话开始，六步，全部由代码完成。"),
    ("l3", 10.4, "立项，定风格、时长和语言。"),
    ("l4", 15.2, "文案，拆成能对齐的句子。"),
    ("l5", 20.0, "分镜，每个镜头都有明确的秒数。"),
    ("l6", 24.8, "配音，一句一个文件，字幕跟着走。"),
    ("l7", 29.6, "混音，旁白、配乐、音效，一条时间轴。"),
    ("l8", 34.4, "渲染，一千多帧，一帧一帧算出来。"),
    ("l9", 39.2, "改一行，重出一版。"),
    ("l10", 44.2, "这套流程，已经跑在这台机器上。"),
]


def dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


async def main():
    ad = HERE / "audio"
    ad.mkdir(exist_ok=True)
    out = []
    for lid, t0, text in LINES:
        mp3 = ad / f"{lid}.mp3"
        if not mp3.exists():
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(mp3))
        d = dur(mp3)
        out.append({"id": lid, "t0": t0, "t1": round(t0 + d + 0.55, 2), "text": text})
        print(lid, f"{d:.2f}s", "->", round(t0 + d, 2))

    (HERE / "lines.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    inputs, filters = [], []
    for i, ln in enumerate(out):
        inputs += ["-i", str(ad / f"{ln['id']}.mp3")]
        ms = int(ln["t0"] * 1000)
        filters.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(out)))
    filters.append(f"{mix}amix=inputs={len(out)}:normalize=0,apad,atrim=0:{DUR},loudnorm=I=-18:TP=-2[out]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
                    "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-ar", "48000", "-ac", "1", str(ad / "voice.wav")], check=True)
    print("voice.wav")


asyncio.run(main())
