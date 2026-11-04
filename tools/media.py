"""素材库：每个视频一个 media/，用名字引用，不用记路径。

用法：
    python tools/media.py add LangChain全家桶 图片.png --name 架构图
    python tools/media.py add LangChain全家桶 D:\\素材\\demo.mp4 --name 演示
    python tools/media.py add LangChain全家桶 D:\\大素材\\long.mp4 --name 长片段 --link
    python tools/media.py list LangChain全家桶
    python tools/media.py remove LangChain全家桶 架构图

目录结构：
    videos/<视频>/media/
        index.json      名字 -> 文件、类型、尺寸
        架构图.png
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".m4v"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac"}


def media_dir(slug: str) -> Path:
    return VIDEOS / slug / "media"


def load_index(slug: str) -> dict:
    p = media_dir(slug) / "index.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_index(slug: str, idx: dict) -> None:
    d = media_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def probe(path: Path, kind: str) -> dict:
    if kind == "image" and path.suffix.lower() in {".svg"}:
        return {}
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    try:
        j = json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        return {}
    st = (j.get("streams") or [{}])[0]
    info = {}
    if st.get("width"):
        info["w"], info["h"] = st["width"], st["height"]
    dur = j.get("format", {}).get("duration")
    if dur:
        info["duration"] = round(float(dur), 2)
    return info


def kind_of(ext: str) -> str:
    ext = ext.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    raise SystemExit(f"不支持的格式：{ext}")


def cmd_add(slug: str, src: Path, name: str | None, link: bool) -> None:
    if not (VIDEOS / slug).exists():
        raise SystemExit(f"没有这个视频：videos/{slug}")
    if not src.exists():
        raise SystemExit(f"找不到文件：{src}")

    kind = kind_of(src.suffix)
    name = name or src.stem
    idx = load_index(slug)
    if name in idx:
        raise SystemExit(f"素材名已存在：{name}（换 --name，或先 remove）")

    d = media_dir(slug)
    d.mkdir(parents=True, exist_ok=True)

    if link:
        rel = src.resolve().relative_to(ROOT) if ROOT in src.resolve().parents else src.resolve()
        entry = {"file": str(rel).replace("\\", "/"), "kind": kind, "linked": True}
    else:
        dest = d / src.name
        shutil.copy2(src, dest)
        entry = {"file": dest.name, "kind": kind}

    entry.update(probe(dest if not link else src, kind))
    entry["bytes"] = src.stat().st_size
    entry["added"] = str(date.today())
    idx[name] = entry
    save_index(slug, idx)

    where = entry["file"]
    print(f"已加入 videos/{slug}/media：{name} -> {where}")
    extra = " ".join(f"{k}={v}" for k, v in entry.items() if k in ("w", "h", "duration"))
    if extra:
        print(f"  {extra}")


def cmd_list(slug: str) -> None:
    idx = load_index(slug)
    if not idx:
        print("这个视频还没有素材。用 media.py add 添加。")
        return
    print(f"{'名字':<18} {'类型':<7} {'尺寸/时长':<16} 文件")
    for name, e in sorted(idx.items()):
        size = f"{e.get('w','?')}x{e.get('h','?')}" if e.get("kind") == "image" else f"{e.get('duration','?')}s"
        print(f"{name:<18} {e.get('kind',''):<7} {size:<16} {e.get('file','')}")


def cmd_remove(slug: str, name: str) -> None:
    idx = load_index(slug)
    if name not in idx:
        raise SystemExit(f"没有这个素材：{name}")
    e = idx.pop(name)
    if not e.get("linked"):
        f = media_dir(slug) / e["file"]
        if f.exists():
            f.unlink()
    save_index(slug, idx)
    print(f"已删除：{name}")


def cmd_show(slug: str, name: str) -> None:
    idx = load_index(slug)
    if name not in idx:
        raise SystemExit(f"没有这个素材：{name}")
    print(json.dumps({name: idx[name]}, ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["add", "list", "remove", "show"])
    ap.add_argument("slug")
    ap.add_argument("source", nargs="?", help="add 时的文件路径，或 remove/show 的素材名")
    ap.add_argument("--name", help="素材名，默认用文件名")
    ap.add_argument("--link", action="store_true", help="不复制，只记录原路径（大文件用）")
    args = ap.parse_args()

    if args.action == "add":
        if not args.source:
            raise SystemExit("用法：media.py add 视频名 文件 [--name 名字]")
        cmd_add(args.slug, Path(args.source), args.name, args.link)
    elif args.action == "list":
        cmd_list(args.slug)
    elif args.action == "remove":
        if not args.source:
            raise SystemExit("用法：media.py remove 视频名 素材名")
        cmd_remove(args.slug, args.source)
    else:
        if not args.source:
            raise SystemExit("用法：media.py show 视频名 素材名")
        cmd_show(args.slug, args.source)


if __name__ == "__main__":
    main()
