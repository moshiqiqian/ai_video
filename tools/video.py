"""视频工程管理：初始化、主题、校验、预览、渲染。

用法：
    python tools/video.py init 降息之后 --theme warm-paper --duration 45
    python tools/video.py status 降息之后
    python tools/video.py theme 降息之后 --set news-red
    python tools/video.py check 降息之后
    python tools/video.py preview 降息之后 --at 3,12,25
    python tools/video.py render 降息之后 --quality delivery
    python tools/video.py list
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
sys.path.insert(0, str(TOOLS))

import make as hf  # noqa: E402

SCENE_TYPES = ("title", "list", "quote", "image", "video", "ending")

SCRIPT_TPL = """在这里写下旁白文案。

建议结构：钩子（一句）→ 事实（两三句）→ 解读（两三句）→ 观点（一两句）。

字数参考：中文约 4.5 字/秒。45 秒约 200 字，20 秒约 90 字。
"""

SCENES_TPL = {
    "scenes": [
        {"type": "title", "kicker": "栏目名", "title": "标题", "sub": "副标题"},
        {"type": "list", "mark": "number", "rows": ["要点一", "要点二"]},
        {"type": "ending", "title": "结尾一句话", "accent": "结尾", "sub": "署名或行动号召"},
    ]
}


# ---------- 基础 ----------

def vdir(slug: str) -> Path:
    return VIDEOS / slug


def load_project(slug: str) -> dict:
    p = vdir(slug) / "project.json"
    if not p.exists():
        raise SystemExit(f"没有这个视频：{slug}（先 video.py init）")
    return json.loads(p.read_text(encoding="utf-8"))


def save_project(slug: str, proj: dict) -> None:
    (vdir(slug) / "project.json").write_text(
        json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")


def load_scenes(slug: str) -> dict:
    return json.loads((vdir(slug) / "scenes.json").read_text(encoding="utf-8"))


def load_transcript(slug: str) -> dict | None:
    p = vdir(slug) / "audio" / "transcript.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def audio_path(slug: str, proj: dict) -> Path:
    d = vdir(slug)
    if proj.get("engine") == "indextts" and proj.get("voice_pack"):
        return d / "audio" / f"vo_{proj['voice_pack']}.wav"
    return d / "audio" / "vo.mp3"


def py() -> str:
    return sys.executable


def npx() -> str:
    return shutil.which("npx") or "npx.cmd"


def run_make(slug: str, extra: list[str]) -> None:
    cmd = [py(), str(TOOLS / "make.py"), slug, *extra]
    subprocess.run(cmd, cwd=ROOT, check=True)


# ---------- init ----------

def cmd_init(a) -> None:
    d = vdir(a.slug)
    if (d / "project.json").exists():
        raise SystemExit(f"已存在：videos/{a.slug}")

    w, h = 1920, 1080
    if a.size:
        try:
            w, h = (int(x) for x in a.size.lower().replace("*", "x").split("x"))
        except Exception:
            raise SystemExit("--size 格式：1920x1080 或 1080x1920")

    proj = {
        "slug": a.slug,
        "theme": a.theme,
        "theme_overrides": {},
        "width": w, "height": h, "fps": 30,
        "engine": a.engine,
        "voice": a.voice,
        "voice_pack": a.voice_pack,
        "rate": "+0%",
        "subtitles": not a.no_subtitles,
        "target_seconds": a.duration,
        "created": str(date.today()),
    }

    (d / "audio").mkdir(parents=True, exist_ok=True)
    (d / "media").mkdir(parents=True, exist_ok=True)
    (d / "script.txt").write_text(SCRIPT_TPL, encoding="utf-8")
    (d / "scenes.json").write_text(
        json.dumps(SCENES_TPL, ensure_ascii=False, indent=2), encoding="utf-8")
    save_project(a.slug, proj)

    print(f"已创建 videos/{a.slug}")
    print(f"  主题   {a.theme}（{hf.THEMES[a.theme]['label']}）")
    print(f"  尺寸   {w}x{h}   目标时长 {a.duration}s")
    print(f"  配音   {a.engine}" + (f" · {a.voice_pack}" if a.voice_pack else f" · {a.voice}"))
    print("\n下一步：")
    print(f"  1. 改 videos/{a.slug}/script.txt     写文案")
    print(f"  2. 改 videos/{a.slug}/scenes.json    写画面")
    print(f"  3. python tools/video.py check {a.slug}")
    print(f"  4. python tools/video.py render {a.slug}")


# ---------- theme ----------

def cmd_theme(a) -> None:
    proj = load_project(a.slug)

    if a.set:
        if a.set not in hf.THEMES:
            raise SystemExit("可用主题：" + " / ".join(hf.THEMES))
        proj["theme"] = a.set
        save_project(a.slug, proj)
        print(f"已切换主题：{a.set}（{hf.THEMES[a.set]['label']}）")
        return

    if a.color:
        key, _, val = a.color.partition("=")
        if key not in ("bg", "ink", "muted", "accent", "sub_bg"):
            raise SystemExit("可覆盖：bg / ink / muted / accent / sub_bg")
        proj.setdefault("theme_overrides", {})[key] = val
        save_project(a.slug, proj)
        print(f"已覆盖 {key} = {val}")
        return

    cur = proj.get("theme", hf.DEFAULT_THEME)
    print(f"当前主题：{cur}\n")
    for name, t in hf.THEMES.items():
        mark = "←" if name == cur else " "
        print(f"  {name:<12} {t['label']:<10} bg={t['bg']} accent={t['accent']} {mark}")
    ov = proj.get("theme_overrides") or {}
    if ov:
        print("\n覆盖项：", json.dumps(ov, ensure_ascii=False))


# ---------- check ----------

def cmd_check(a) -> int:
    proj = load_project(a.slug)
    cfg = load_scenes(a.slug)
    scenes = cfg.get("scenes") or []
    script = (vdir(a.slug) / "script.txt").read_text(encoding="utf-8").strip()
    transcript = load_transcript(a.slug)
    media_file = vdir(a.slug) / "media" / "index.json"
    media = json.loads(media_file.read_text(encoding="utf-8")) if media_file.exists() else {}
    audio = audio_path(a.slug, proj)

    errors: list[str] = []
    warns: list[str] = []

    # 文案
    if not script or script.startswith("在这里写下旁白文案"):
        errors.append("script.txt 还是模板，没有填内容")
    else:
        est = len(script.replace("\n", "")) / 4.5
        target = proj.get("target_seconds") or 0
        if target and abs(est - target) > max(3, target * 0.4):
            warns.append(f"文案约 {est:.0f} 秒，和目标的 {target} 秒差得多")

    # 分镜
    if not scenes:
        errors.append("scenes.json 里没有镜头")
    if not (1 <= len(scenes) <= 12):
        warns.append(f"镜头数 {len(scenes)}，建议 3–8 个")

    for i, sc in enumerate(scenes, 1):
        t = sc.get("type")
        if t not in SCENE_TYPES:
            errors.append(f"第 {i} 个镜头类型未知：{t}")
            continue
        if t == "title":
            if len(sc.get("title", "")) > 16:
                errors.append(f"第 {i} 屏标题超过 16 字")
            if len(sc.get("sub", "")) > 28:
                warns.append(f"第 {i} 屏副标题超过 28 字")
            if len(sc.get("kicker", "")) > 20:
                warns.append(f"第 {i} 屏 kicker 超过 20 字")
        elif t == "list":
            rows = sc.get("rows") or []
            if not (1 <= len(rows) <= 5):
                errors.append(f"第 {i} 屏清单行数 {len(rows)}，应为 1–5")
            for j, r in enumerate(rows, 1):
                if len(r) > 12:
                    errors.append(f"第 {i} 屏第 {j} 行超过 12 字：{r}")
            if len(rows) >= 3:
                warns.append(f"第 {i} 屏有 {len(rows)} 行，逐行出现容易和语音对不齐，建议拆成两屏")
        elif t == "quote":
            if len(sc.get("text", "")) > 24:
                errors.append(f"第 {i} 屏金句超过 24 字")
        elif t == "ending":
            if len(sc.get("title", "")) > 14:
                warns.append(f"第 {i} 屏结尾标题超过 14 字")
        elif t in ("image", "video"):
            src = sc.get("src")
            if not src:
                errors.append(f"第 {i} 屏缺少 src")
            elif src not in media:
                errors.append(f"第 {i} 屏素材「{src}」不在素材库，用 media.py list 查看")

    # 时间
    if transcript:
        n = len(transcript.get("sentences", []))
        last = 0
        for i, sc in enumerate(scenes, 1):
            idx = sc.get("start_at_sentence")
            if idx is None:
                continue
            if not isinstance(idx, int) or idx < 1 or idx > n:
                errors.append(f"第 {i} 屏 start_at_sentence={idx}，但转写只有 {n} 句")
            elif idx <= last:
                errors.append(f"第 {i} 屏 start_at_sentence={idx} 没有递增（上一屏是 {last}）")
            else:
                last = idx
    else:
        if any("start_at_sentence" in sc for sc in scenes):
            warns.append("分镜用了 start_at_sentence，但没有 transcript.json（先跑 --transcribe）")

    # 时长
    if audio.exists():
        total = hf.duration(audio)
        if transcript:
            bounds = hf.pick_boundaries(hf.detect_pauses(audio), scenes, total, transcript)
        else:
            bounds = hf.pick_boundaries(hf.detect_pauses(audio), scenes, total)
        starts = [0.0] + bounds
        ends = bounds + [total]
        for i, (s, e) in enumerate(zip(starts, ends), 1):
            if e - s < 1.5:
                errors.append(f"第 {i} 屏只有 {e-s:.1f} 秒，太短（低于 1.5 秒）")
        target = proj.get("target_seconds") or 0
        if target and abs(total - target) > max(5, target * 0.35):
            warns.append(f"音频 {total:.1f} 秒，和目标 {target} 秒差得多")
    else:
        warns.append("还没有配音，时间相关检查已跳过")

    for e in errors:
        print(f"  [错误] {e}")
    for w in warns:
        print(f"  [提醒] {w}")

    if errors:
        print(f"\n{len(errors)} 个错误，{len(warns)} 个提醒 —— 先修错误")
    elif warns:
        print(f"\n0 个错误，{len(warns)} 个提醒 —— 可以出片")
    else:
        print("\n全部通过，可以出片")
    return 1 if errors else 0


# ---------- preview / render ----------

def build_html(slug: str, proj: dict) -> None:
    extra = []
    if proj.get("subtitles"):
        extra.append("--subtitles")
    if audio_path(slug, proj).exists():
        extra.append("--reuse-audio")
    run_make(slug, extra)


def cmd_preview(a) -> None:
    proj = load_project(a.slug)
    if not audio_path(a.slug, proj).exists():
        raise SystemExit("还没有配音，先跑：python tools/video.py render " + a.slug)
    build_html(a.slug, proj)

    times = a.at or "1,5,10"
    out = vdir(a.slug) / "qa"
    out.mkdir(exist_ok=True)
    subprocess.run([npx(), "--yes", "hyperframes@0.9.0", "snapshot", ".",
                    "--at", times, "-o", str(out), "--keep"], cwd=ROOT, check=True)
    print(f"\n截图 -> videos/{a.slug}/qa/")


def cmd_render(a) -> None:
    proj = load_project(a.slug)
    extra = ["--quality", a.quality]
    if proj.get("subtitles"):
        extra.append("--subtitles")
    if a.transcribe:
        extra.append("--transcribe")
    if a.reuse:
        extra.append("--reuse-audio")

    audio = audio_path(a.slug, proj)
    script_mtime = (vdir(a.slug) / "script.txt").stat().st_mtime
    if audio.exists() and audio.stat().st_mtime >= script_mtime:
        extra.append("--reuse-audio")

    run_make(a.slug, extra + ["--render"])

    if not a.no_qa:
        out = vdir(a.slug) / "qa"
        out.mkdir(exist_ok=True)
        total = hf.duration(audio)
        pts = [round(total * r, 1) for r in (0.1, 0.45, 0.8)]
        subprocess.run([npx(), "--yes", "hyperframes@0.9.0", "snapshot", ".",
                        "--at", ",".join(map(str, pts)), "-o", str(out), "--keep"],
                       cwd=ROOT, check=False)
        print(f"抽帧 -> videos/{a.slug}/qa/")


# ---------- status / list ----------

def cmd_status(a) -> None:
    proj = load_project(a.slug)
    d = vdir(a.slug)
    scenes = load_scenes(a.slug).get("scenes", [])
    audio = audio_path(a.slug, proj)
    print(f"视频      {a.slug}")
    print(f"主题      {proj.get('theme')}（{hf.THEMES.get(proj.get('theme'), {}).get('label', '?')}）")
    print(f"尺寸      {proj.get('width')}x{proj.get('height')}  {proj.get('fps')}fps")
    print(f"目标时长  {proj.get('target_seconds')}s")
    print(f"配音      {proj.get('engine')}"
          + (f" · {proj.get('voice_pack')}" if proj.get('voice_pack') else f" · {proj.get('voice')}"))
    print(f"字幕      {'开' if proj.get('subtitles') else '关'}")
    print(f"镜头      {len(scenes)} 个：" + " / ".join(s.get("type", "?") for s in scenes))
    print(f"文案      {len((d/'script.txt').read_text(encoding='utf-8').strip())} 字")
    if audio.exists():
        print(f"配音文件  {audio.relative_to(ROOT)}  {hf.duration(audio):.1f}s")
    else:
        print("配音文件  未生成")
    print(f"成片      {'有' if (d/'render.mp4').exists() else '无'}")
    media = d / "media" / "index.json"
    if media.exists():
        idx = json.loads(media.read_text(encoding="utf-8"))
        print(f"素材      {len(idx)} 个：" + "、".join(idx) if idx else "素材      无")


def cmd_list(a) -> None:
    if not VIDEOS.exists():
        print("还没有视频")
        return
    for d in sorted(VIDEOS.iterdir()):
        pj = d / "project.json"
        if not pj.exists():
            continue
        p = json.loads(pj.read_text(encoding="utf-8"))
        has = "✓" if (d / "render.mp4").exists() else " "
        print(f"  {has} {d.name:<20} {p.get('theme','?'):<12} {p.get('target_seconds','?')}s  "
              f"{p.get('engine','?')}")


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description="视频工程管理")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="新建视频")
    p.add_argument("slug")
    p.add_argument("--theme", default=hf.DEFAULT_THEME, choices=list(hf.THEMES))
    p.add_argument("--duration", type=int, default=45)
    p.add_argument("--size", default="1920x1080")
    p.add_argument("--engine", default="edge", choices=["edge", "indextts"])
    p.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    p.add_argument("--voice-pack")
    p.add_argument("--no-subtitles", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("theme", help="查看/切换主题")
    p.add_argument("slug")
    p.add_argument("--set", help="切换预设")
    p.add_argument("--color", help="覆盖单项，如 accent=#ff6600")
    p.set_defaults(func=cmd_theme)

    p = sub.add_parser("check", help="校验，不出片")
    p.add_argument("slug")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("preview", help="抽帧预览")
    p.add_argument("slug")
    p.add_argument("--at", help="时间点，如 3,12,25")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("render", help="出片")
    p.add_argument("slug")
    p.add_argument("--quality", default="looks", choices=["draft", "looks", "delivery"])
    p.add_argument("--transcribe", action="store_true")
    p.add_argument("--reuse", action="store_true", help="强制复用已有配音")
    p.add_argument("--no-qa", action="store_true", help="不抽帧")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("status", help="查看状态")
    p.add_argument("slug")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="列出所有视频")
    p.set_defaults(func=cmd_list)

    a = ap.parse_args()
    rc = a.func(a)
    if isinstance(rc, int):
        sys.exit(rc)


if __name__ == "__main__":
    main()
