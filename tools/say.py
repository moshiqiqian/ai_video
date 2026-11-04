"""用声音库里的音色生成语音（IndexTTS2）。

用法（先 conda activate indextts）：
    python tools/voice.py list                      # 看有哪些音色
    python tools/say.py 晓晓 --text "你好，世界" --out out.wav
    python tools/say.py 晓晓 --script videos/a/script.txt --out videos/a/audio/vo_晓晓.wav

不写 --out 时，默认输出到当前目录 <音色名>.wav。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "voices"
VENDOR = ROOT / "vendor" / "index-tts"
sys.path.insert(0, str(VENDOR))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("voice", help="声音库里的名字，用 voice.py list 查看")
    ap.add_argument("--text", default=None, help="直接给文字")
    ap.add_argument("--script", default=None, help="读这个文本文件")
    ap.add_argument("--out", default=None, help="输出 wav 路径")
    ap.add_argument("--fp16", action="store_true", default=True, help="半精度（默认开）")
    args = ap.parse_args()

    sample = VOICES / args.voice / "sample.wav"
    if not sample.exists():
        raise SystemExit(f"声音库里没有「{args.voice}」，先运行 python tools/voice.py list")

    if not args.text and not args.script:
        raise SystemExit("要给 --text 或 --script 之一")
    text = args.text or Path(args.script).read_text(encoding="utf-8").strip()

    out = Path(args.out) if args.out else ROOT / f"{args.voice}.wav"
    out = out if out.is_absolute() else (ROOT / out)
    out.parent.mkdir(parents=True, exist_ok=True)

    from indextts.infer_v2 import IndexTTS2

    tts = IndexTTS2(
        cfg_path=str(VENDOR / "checkpoints" / "config.yaml"),
        model_dir=str(VENDOR / "checkpoints"),
        use_fp16=args.fp16,
        use_cuda_kernel=False,
        use_deepspeed=False,
    )
    tts.infer(str(sample), text, str(out), verbose=True)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out)],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"{float(dur):.2f}s  ->  {out.relative_to(ROOT) if ROOT in out.parents else out}")


if __name__ == "__main__":
    main()
