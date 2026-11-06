"""IndexTTS2 批量逐句配音：模型只加载一次，一句一个 WAV。

用法（在 indextts 环境）：
    python tools/say_lines.py xiaoxiao videos/<slug>/build/lines.json videos/<slug>/film/audio

会为每句写 <id>.wav 和 <id>.hash；文本没变就跳过，只补改动的句子。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "voices"
VENDOR = ROOT / "vendor" / "index-tts"
sys.path.insert(0, str(VENDOR))


def ff_dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    ap.add_argument("lines")
    ap.add_argument("outdir")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    sample = VOICES / args.voice / "sample.wav"
    if not sample.exists():
        raise SystemExit(f"没有音色：{sample}")

    lines = json.loads(Path(args.lines).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    todo = []
    for ln in lines:
        h = hashlib.sha1(ln["text"].encode("utf-8")).hexdigest()[:12]
        wav = outdir / f"{ln['id']}.wav"
        hf = outdir / f"{ln['id']}.hash"
        if not args.force and wav.exists() and hf.exists() and hf.read_text() == h:
            continue
        todo.append((ln, wav, hf, h))

    if not todo:
        print("全部命中缓存，无需生成")
    else:
        from indextts.infer_v2 import IndexTTS2
        print(f"加载模型，生成 {len(todo)} 句 …")
        tts = IndexTTS2(
            cfg_path=str(VENDOR / "checkpoints" / "config.yaml"),
            model_dir=str(VENDOR / "checkpoints"),
            use_fp16=True,
            use_cuda_kernel=False,
            use_deepspeed=False,
        )
        for ln, wav, hf, h in todo:
            tts.infer(str(sample), ln["text"], str(wav), verbose=False)
            hf.write_text(h)
            print(f"  {ln['id']}  {ff_dur(wav):.2f}s  {ln['text']}")

    durs = {ln["id"]: round(ff_dur(outdir / f"{ln['id']}.wav"), 3) for ln in lines}
    (outdir.parent.parent / "build" / "voice_durations.json").write_text(
        json.dumps(durs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(durs, ensure_ascii=False))


if __name__ == "__main__":
    main()
