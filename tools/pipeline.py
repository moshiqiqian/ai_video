"""六阶段新流水线：立项 → 文案 → 分镜 → 配音 → 混音 → 渲染。

与旧的 stage.py 并存，但新项目默认走这条：
    python tools/pipeline.py start <slug>
    python tools/pipeline.py brief <slug> --style swiss-motion --duration 48 --language zh
    python tools/pipeline.py script <slug> --file source/script.txt
    python tools/pipeline.py storyboard <slug>
    python tools/pipeline.py voice <slug>
    python tools/pipeline.py mix <slug>
    python tools/pipeline.py render <slug>
    python tools/pipeline.py confirm <slug> <stage>
    python tools/pipeline.py status <slug>

产物：
    build/lines.json      逐句文案 + t0/t1/dur
    build/timeline.json   段落与镜头时间
    film/index.html       render(t) 页面
    film/audio/mix.wav    混音
    output/render.mp4     成片
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
STAGES = ["brief", "script", "storyboard", "voice", "mix", "render"]
TOOLS = ROOT / "tools"


# ---------------------------------------------------------------- state
def vdir(slug: str) -> Path:
    return VIDEOS / slug


def load(slug: str) -> dict:
    p = vdir(slug) / "project.json"
    if not p.exists():
        raise SystemExit(f"没有这个项目：{slug}（先 start）")
    return json.loads(p.read_text(encoding="utf-8"))


def save(slug: str, proj: dict) -> None:
    (vdir(slug) / "project.json").write_text(
        json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")


def mark(proj: dict, stage: str) -> None:
    proj.setdefault("stages", {})[stage] = "done"
    # 下游标记过期
    idx = STAGES.index(stage)
    for s in STAGES[idx + 1:]:
        if proj["stages"].get(s) == "done":
            proj["stages"][s] = "stale"


def need(proj: dict, stage: str) -> None:
    for s in STAGES[:STAGES.index(stage)]:
        if proj["stages"].get(s) != "done":
            raise SystemExit(f"上一步 {s} 还没完成，先跑 {s}")


# ---------------------------------------------------------------- stages
def cmd_start(a) -> None:
    d = vdir(a.slug)
    if d.exists() and (d / "project.json").exists():
        raise SystemExit(f"已存在：{d}")
    for sub in ("source", "build", "film/audio", "output", "qa"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    proj = {
        "slug": a.slug,
        "pipeline": "lemo",
        "style": None,
        "duration": None,
        "language": "zh",
        "fps": 24,
        "stages": {},
    }
    save(a.slug, proj)
    print(f"已建立：{d}")
    print("下一步：pipeline.py brief ... --style <slug> --duration <秒> --language zh")


def cmd_brief(a) -> None:
    proj = load(a.slug)
    style_dir = ROOT / "engine" / "styles" / a.style
    if not style_dir.exists():
        raise SystemExit(f"引擎里没有这个风格：{a.style}（engine/styles/）")
    if a.duration <= 0:
        raise SystemExit("时长必须大于 0")
    proj.update(style=a.style, duration=float(a.duration),
                language=a.language, fps=a.fps,
                topic=a.topic or proj.get("topic", ""))
    mark(proj, "brief")
    save(a.slug, proj)
    (vdir(a.slug) / "source" / "brief.md").write_text(
        f"# 立项\n\n- 风格：{a.style}\n- 时长：{a.duration}s\n- 语言：{a.language}\n- FPS：{a.fps}\n- 主题：{proj['topic']}\n",
        encoding="utf-8")
    print(f"立项：{a.style} · {a.duration}s · {a.language} · {a.fps}fps")


def split_lines(text: str) -> list[str]:
    text = re.sub(r"\s+", "", text.strip())
    parts = re.split(r"(?<=[。！？!?；;])", text)
    return [p for p in (x.strip() for x in parts) if p]


def cmd_script(a) -> None:
    proj = load(a.slug)
    need(proj, "script")
    if a.file:
        text = Path(a.file).read_text(encoding="utf-8")
    elif a.text:
        text = a.text
    else:
        src = vdir(a.slug) / "source" / "script.txt"
        if not src.exists():
            raise SystemExit("没有文案：用 --text 或 --file，或放 source/script.txt")
        text = src.read_text(encoding="utf-8")
    lines = split_lines(text)
    if not lines:
        raise SystemExit("文案是空的")
    out = [{"id": f"l{i+1}", "text": s, "t0": None, "t1": None} for i, s in enumerate(lines)]
    (vdir(a.slug) / "source" / "script.txt").write_text(text, encoding="utf-8")
    (vdir(a.slug) / "build" / "lines.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    mark(proj, "script")
    save(a.slug, proj)
    print(f"文案 {len(lines)} 句，已拆成 build/lines.json")


def est_dur(text: str) -> float:
    # 中文口播约 4.6 字/秒，加句末停顿
    return max(1.2, len(text) / 4.6 + 0.55)


def cmd_storyboard(a) -> None:
    proj = load(a.slug)
    need(proj, "storyboard")
    d = vdir(a.slug)
    lines = json.loads((d / "build" / "lines.json").read_text(encoding="utf-8"))
    total = float(proj["duration"])
    t = 0.8
    scenes = []
    for i, ln in enumerate(lines):
        ln["t0"] = round(t, 2)
        ln["t1"] = round(t + est_dur(ln["text"]), 2)
        t = ln["t1"] + a.gap
        scenes.append({
            "id": f"s{i+1}", "line": ln["id"],
            "t0": ln["t0"], "t1": ln["t1"],
        })
        if ln["t1"] > total - 0.4:
            raise SystemExit(f"文案超出时长：{ln['id']} 预计到 {ln['t1']}s，总长 {total}s。缩短文案或加时长。")
    (d / "build" / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")
    timeline = {"duration": total, "fps": proj["fps"], "lines": lines, "scenes": scenes}
    (d / "build" / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    mark(proj, "storyboard")
    save(a.slug, proj)
    print(f"分镜 {len(scenes)} 段，预计结束 {t:.2f}s / {total}s")


def ffprobe_dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def cmd_voice(a) -> None:
    proj = load(a.slug)
    need(proj, "voice")
    d = vdir(a.slug)
    lines = json.loads((d / "build" / "lines.json").read_text(encoding="utf-8"))
    total = float(proj["duration"])
    ad = d / "film" / "audio"
    ad.mkdir(parents=True, exist_ok=True)

    import asyncio
    import edge_tts

    async def speak():
        for ln in lines:
            mp3 = ad / f"{ln['id']}.mp3"
            if not mp3.exists():
                await edge_tts.Communicate(ln["text"], a.voice, rate=a.rate).save(str(mp3))
            ln["dur"] = round(ffprobe_dur(mp3), 2)

    asyncio.run(speak())

    # 用实际时长重排；不够就整体后移，最后一句必须放得下
    t = lines[0]["t0"] if lines[0]["t0"] is not None else 0.8
    for i, ln in enumerate(lines):
        ln["t0"] = round(t, 2)
        ln["t1"] = round(t + ln["dur"] + 0.55, 2)
        t = ln["t1"] + 0.35
        if ln["t1"] > total - 0.3 and i == len(lines) - 1:
            raise SystemExit(f"最后一句到 {ln['t1']}s，超过总长 {total}s。缩短文案或加时长。")

    (d / "build" / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")
    tl = json.loads((d / "build" / "timeline.json").read_text(encoding="utf-8"))
    tl["lines"] = lines
    tl["scenes"] = [{"id": f"s{i+1}", "line": ln["id"], "t0": ln["t0"], "t1": ln["t1"]}
                    for i, ln in enumerate(lines)]
    (d / "build" / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "film" / "lines.json").write_text(
        json.dumps([{"id": x["id"], "t0": x["t0"], "t1": x["t1"], "text": x["text"]} for x in lines],
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # 拼成一条 voice.wav
    inputs, filters = [], []
    for i, ln in enumerate(lines):
        inputs += ["-i", str(ad / f"{ln['id']}.mp3")]
        ms = int(ln["t0"] * 1000)
        filters.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(lines)))
    filters.append(f"{mix}amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{total}[out]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
                    "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-ar", "48000", "-ac", "1", str(ad / "voice.wav")], check=True)

    mark(proj, "voice")
    save(a.slug, proj)
    print(f"配音 {len(lines)} 句，voice.wav，最后一句到 {lines[-1]['t1']}s")


def cmd_mix(a) -> None:
    proj = load(a.slug)
    need(proj, "mix")
    d = vdir(a.slug)
    ad = d / "film" / "audio"
    total = float(proj["duration"])
    music = ad / "music.wav"
    subprocess.run([sys.executable, str(TOOLS / "music_bed.py"),
                    "--duration", str(total), "--bpm", str(a.bpm),
                    "--out", str(music)], check=True)
    mix = ad / "mix.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(ad / "voice.wav"), "-i", str(music),
        "-filter_complex",
        "[1:a]volume=0.30[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[duck];"
        "[0:a][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "[a]", "-ar", "48000", "-ac", "2", str(mix)], check=True)
    mark(proj, "mix")
    save(a.slug, proj)
    print(f"混音 -> {mix.relative_to(ROOT)}")


def cmd_render(a) -> None:
    proj = load(a.slug)
    need(proj, "render")
    d = vdir(a.slug)
    if not (d / "film" / "index.html").exists():
        raise SystemExit("还没有 film/index.html（render(t) 页面）")
    subprocess.run([sys.executable, str(TOOLS / "lemo.py"), "render", a.slug,
                    "--workers", str(a.workers)], check=True)
    mp4 = d / "output" / "render.mp4"
    dur = ffprobe_dur(mp4)
    qa = d / "qa"
    qa.mkdir(exist_ok=True)
    shots = []
    for ratio in (0.08, 0.45, 0.85):
        shot = qa / f"at-{dur*ratio:.1f}s.jpg"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", f"{dur*ratio:.2f}", "-i", str(mp4), "-frames:v", "1", str(shot)],
                       check=False)
        if shot.exists():
            shots.append(str(shot.relative_to(ROOT)))
    info = {"duration": round(dur, 2), "bytes": mp4.stat().st_size, "qa": shots}
    (d / "build" / "render.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    mark(proj, "render")
    save(a.slug, proj)
    print(f"成片 {mp4.relative_to(ROOT)}  {dur:.2f}s  {mp4.stat().st_size/1024/1024:.2f} MB")


def cmd_confirm(a) -> None:
    proj = load(a.slug)
    if a.stage not in STAGES:
        raise SystemExit(f"未知阶段：{a.stage}")
    if proj["stages"].get(a.stage) != "done":
        raise SystemExit(f"{a.stage} 还没完成")
    proj.setdefault("confirmed", {})[a.stage] = True
    save(a.slug, proj)
    print(f"已确认：{a.stage}")


def cmd_status(a) -> None:
    proj = load(a.slug)
    print(f"项目 {a.slug} · {proj.get('style')} · {proj.get('duration')}s · {proj.get('fps')}fps")
    for s in STAGES:
        st = proj["stages"].get(s, "todo")
        ok = "x" if proj.get("confirmed", {}).get(s) else " "
        print(f"  [{ok}] {s:<11} {st}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start"); p.add_argument("slug"); p.set_defaults(fn=cmd_start)

    p = sub.add_parser("brief")
    p.add_argument("slug"); p.add_argument("--style", required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--language", default="zh"); p.add_argument("--fps", type=int, default=24)
    p.add_argument("--topic", default="")
    p.set_defaults(fn=cmd_brief)

    p = sub.add_parser("script")
    p.add_argument("slug"); p.add_argument("--text"); p.add_argument("--file")
    p.set_defaults(fn=cmd_script)

    p = sub.add_parser("storyboard"); p.add_argument("slug"); p.add_argument("--gap", type=float, default=0.35)
    p.set_defaults(fn=cmd_storyboard)

    p = sub.add_parser("voice")
    p.add_argument("slug"); p.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    p.add_argument("--rate", default="+8%")
    p.set_defaults(fn=cmd_voice)

    p = sub.add_parser("mix"); p.add_argument("slug"); p.add_argument("--bpm", type=float, default=96)
    p.set_defaults(fn=cmd_mix)

    p = sub.add_parser("render"); p.add_argument("slug"); p.add_argument("--workers", type=int, default=4)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("confirm"); p.add_argument("slug"); p.add_argument("stage")
    p.set_defaults(fn=cmd_confirm)

    p = sub.add_parser("status"); p.add_argument("slug"); p.set_defaults(fn=cmd_status)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
