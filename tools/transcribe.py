"""FunASR 转写：给音频打上词级 / 句级时间戳。

用法（先 conda activate indextts）：
    python tools/transcribe.py LangChain全家桶
    python tools/transcribe.py LangChain全家桶 --audio audio/vo_indextts.wav

输出 videos/<名字>/audio/transcript.json：
    {
      "duration": 54.65,
      "sentences": [
        {"text": "LangChain 全家桶，", "start": 0.0, "end": 1.9},
        ...
      ],
      "words": [{"text": "LangChain", "start": 0.0, "end": 0.72}, ...]
    }
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--audio", default="audio/vo_indextts.wav")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    args = ap.parse_args()

    d = VIDEOS / args.slug
    audio = Path(args.audio)
    if not audio.is_absolute():
        audio = d / audio
    if not audio.exists():
        raise SystemExit(f"找不到音频：{audio}")

    from funasr import AutoModel

    print("加载模型（首次运行会下载约 1GB）…")
    model = AutoModel(
        model="paraformer-zh",
        vad_model="fsmn-vad",
        punc_model="ct-punc",
        device=args.device,
        disable_update=True,
    )

    print(f"转写 {audio.name} …")
    res = model.generate(
        input=str(audio),
        batch_size_s=300,
        sentence_timestamp=True,
    )

    item = res[0]
    punct = set("，。！？：；、,.!?:;\"'“”‘’（）()【】[]《》—…- ")
    sentences = []
    for s in item.get("sentence_info", []):
        text = s.get("text", "").strip()
        ts = s.get("timestamp", [])
        chars = list(text)
        plain = [c for c in chars if c.strip() and c not in punct]

        if len(ts) == len(chars):
            pairs = list(zip(chars, ts))
        elif len(ts) == len(plain):
            pairs = list(zip(plain, ts))
        else:
            # 时间戳对不上就按句子起止均分，保证字幕可用
            step = (s["end"] - s["start"]) / max(len(plain), 1)
            pairs = [(c, (s["start"] + i * step, s["start"] + (i + 1) * step))
                     for i, c in enumerate(plain)]

        words = [{"text": c, "start": round(t[0] / 1000, 3), "end": round(t[1] / 1000, 3)}
                 for c, t in pairs if c.strip()]
        sentences.append({
            "text": text,
            "start": round(s["start"] / 1000, 3),
            "end": round(s["end"] / 1000, 3),
            "words": words,
        })

    out = {
        "audio": audio.name,
        "duration": sentences[-1]["end"] if sentences else 0,
        "text": item.get("text", ""),
        "sentences": sentences,
    }
    dest = d / "build" / "transcript.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{len(sentences)} 句 -> {dest.relative_to(ROOT)}")
    for s in sentences:
        print(f"  {s['start']:7.2f} – {s['end']:7.2f}  {s['text']}")


if __name__ == "__main__":
    main()
