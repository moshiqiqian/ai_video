"""Lemo 渲染链适配器：用 render(t) 页面逐帧出片。

用法：
    python tools/lemo.py doctor
    python tools/lemo.py still  <slug> 8.0
    python tools/lemo.py render <slug> [--fps 24] [--workers 3]

约定：
    videos/<slug>/film/        index.html + main.js + lines.json
    videos/<slug>/film/audio/  mix.wav（可选）
    videos/<slug>/output/      render.mp4
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"
CORE = ENGINE / "core"
VIDEOS = ROOT / "videos"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome() -> str | None:
    if os.environ.get("PLAYWRIGHT_CHROME"):
        p = os.environ["PLAYWRIGHT_CHROME"]
        return p if Path(p).exists() else None
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def run(cmd: list[str], **kw) -> None:
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)


def ensure_engine() -> dict:
    if not (CORE / "render" / "video.mjs").exists():
        raise SystemExit(f"缺少引擎：{CORE}\n先把 lemo-opuscar 的 core/ 放到 engine/core/")
    if not (ENGINE / "node_modules").exists():
        print("首次运行：安装 node 依赖 …")
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm:
            raise SystemExit("找不到 npm，请先安装 Node 20+")
        run([npm, "install", "--no-audit", "--no-fund", "--loglevel=error"], cwd=ENGINE)
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("找不到 Chrome/Edge。设置 PLAYWRIGHT_CHROME 指向浏览器可执行文件。")
    env = dict(os.environ, PLAYWRIGHT_CHROME=chrome)
    return env


def film_dir(slug: str) -> Path:
    d = VIDEOS / slug / "film"
    if not (d / "index.html").exists():
        raise SystemExit(f"{d} 下没有 index.html（render(t) 页面）")
    return d


def cmd_doctor(a) -> None:
    print("Lemo 渲染链体检")
    print("  engine:", ENGINE, "OK" if CORE.exists() else "缺失")
    print("  node  :", shutil.which("node") or "缺失")
    print("  ffmpeg:", shutil.which("ffmpeg") or "缺失")
    chrome = find_chrome()
    print("  chrome:", chrome or "缺失")
    print("  deps  :", "OK" if (ENGINE / "node_modules").exists() else "未安装（首次 render 会自动装）")


def cmd_still(a) -> None:
    env = ensure_engine()
    d = film_dir(a.slug)
    out = d / "stills"
    out.mkdir(exist_ok=True)
    run(["node", "core/render/still.mjs", str(d), *map(str, a.times),
         "--out", str(out)], cwd=ENGINE, env=env)


def cmd_render(a) -> None:
    env = ensure_engine()
    d = film_dir(a.slug)
    out_dir = VIDEOS / a.slug / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = d / "out" / "video.mp4"
    raw.parent.mkdir(exist_ok=True)

    print(f"[1/3] 逐帧渲染 {a.fps}fps × {a.workers} …")
    run(["node", "core/render/video.mjs", str(d), "--fps", str(a.fps),
         "--workers", str(a.workers), "--out", str(raw)], cwd=ENGINE, env=env)

    final = out_dir / "render.mp4"
    mix = d / "audio" / "mix.wav"
    print("[2/3] 合成音轨 …")
    if mix.exists():
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(raw), "-i", str(mix), "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    else:
        print("      没有 audio/mix.wav，输出无声片")
        shutil.copy2(raw, final)

    print("[3/3] 完成 ->", final)
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                           "format=duration,size", "-of", "json", str(final)],
                          capture_output=True, text=True).stdout
    try:
        meta = json.loads(info)["format"]
        print(f"      {float(meta['duration']):.2f}s  {int(meta['size'])/1024/1024:.2f} MB")
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)

    p = sub.add_parser("still")
    p.add_argument("slug")
    p.add_argument("times", nargs="+", type=float)
    p.set_defaults(fn=cmd_still)

    p = sub.add_parser("render")
    p.add_argument("slug")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--workers", type=int, default=3)
    p.set_defaults(fn=cmd_render)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
