"""声音库：管理可复用的音色样本。

音色统一放在 voices/<名字>/ 下：
    sample.wav   5-10 秒的干净人声（24kHz 单声道）
    meta.json    说明信息

用法：
    python tools/voice.py list
    python tools/voice.py add 我的声音 录音.m4a --start 2 --dur 8 --label "本人"
    python tools/voice.py show 我的声音
    python tools/voice.py remove 我的声音
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "voices"


def voice_dir(name: str) -> Path:
    return VOICES / name


def read_meta(name: str) -> dict:
    p = voice_dir(name) / "meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def probe(path: Path) -> tuple[float, int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    j = json.loads(out.stdout or "{}")
    dur = float(j.get("format", {}).get("duration", 0) or 0)
    st = (j.get("streams") or [{}])[0]
    return dur, int(st.get("sample_rate", 0) or 0), int(st.get("channels", 0) or 0)


def cmd_list() -> None:
    if not VOICES.exists() or not any(VOICES.iterdir()):
        print("声音库是空的。用 voice.py add 添加。")
        return
    print(f"{'名字':<16} {'时长':>7}  {'标签':<18} 创建")
    for d in sorted(VOICES.iterdir()):
        if not d.is_dir():
            continue
        wav = d / "sample.wav"
        if not wav.exists():
            continue
        meta = read_meta(d.name)
        dur, _, _ = probe(wav)
        print(f"{d.name:<16} {dur:6.1f}s  {meta.get('label',''):<18} {meta.get('created','')}")


def cmd_show(name: str) -> None:
    d = voice_dir(name)
    if not d.exists():
        raise SystemExit(f"没有这个音色：{name}")
    meta = read_meta(name)
    dur, sr, ch = probe(d / "sample.wav")
    print(f"名字   {name}")
    print(f"文件   {d / 'sample.wav'}")
    print(f"时长   {dur:.2f}s")
    print(f"规格   {sr} Hz / {ch} 声道")
    for k, v in meta.items():
        print(f"{k:<6} {v}")


def cmd_add(name: str, src: Path, start: float, dur: float, label: str) -> None:
    if not src.exists():
        raise SystemExit(f"找不到文件：{src}")

    d = voice_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    dest = d / "sample.wav"

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-ss", str(start), "-t", str(dur), "-i", str(src),
           "-ac", "1", "-ar", "24000", str(dest)]
    subprocess.run(cmd, check=True)

    out_dur, sr, ch = probe(dest)
    if not (2.5 <= out_dur <= 20):
        print(f"警告：样本时长 {out_dur:.1f}s，建议 5-10 秒")

    meta = {
        "label": label or name,
        "source": str(src),
        "clip": f"{start}s + {dur}s",
        "duration": round(out_dur, 2),
        "sample_rate": sr,
        "channels": ch,
        "created": str(date.today()),
    }
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已加入声音库：{name}")
    print(f"  {dest.relative_to(ROOT)}  ({out_dur:.1f}s, {sr}Hz)")


def cmd_remove(name: str) -> None:
    d = voice_dir(name)
    if not d.exists():
        raise SystemExit(f"没有这个音色：{name}")
    shutil.rmtree(d)
    print(f"已删除：{name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["list", "add", "show", "remove"])
    ap.add_argument("name", nargs="?")
    ap.add_argument("source", nargs="?", help="add 时的源音频")
    ap.add_argument("--start", type=float, default=0.0, help="从第几秒开始截")
    ap.add_argument("--dur", type=float, default=8.0, help="截多长，默认 8 秒")
    ap.add_argument("--label", default="", help="备注名，如「本人」「晓晓」")
    args = ap.parse_args()

    if args.action == "list":
        cmd_list()
    elif args.action == "show":
        if not args.name:
            raise SystemExit("用法：voice.py show 名字")
        cmd_show(args.name)
    elif args.action == "remove":
        if not args.name:
            raise SystemExit("用法：voice.py remove 名字")
        cmd_remove(args.name)
    else:
        if not args.name or not args.source:
            raise SystemExit("用法：voice.py add 名字 源音频 [--start 0 --dur 8]")
        cmd_add(args.name, Path(args.source), args.start, args.dur, args.label)


if __name__ == "__main__":
    main()
