"""阶段化的视频流水线：brief → script → storyboard → assets → voice → render

每个阶段单独执行、单独确认、单独记录状态。上游变了，下游自动标记为 stale。

用法：
    python tools/stage.py brief 降息之后 --from D:\\文章\\降息.md --duration 45
    python tools/stage.py script 降息之后
    python tools/stage.py confirm 降息之后 script
    python tools/stage.py storyboard 降息之后
    python tools/stage.py voice 降息之后
    python tools/stage.py render 降息之后 --quality delivery
    python tools/stage.py status 降息之后
    python tools/stage.py next 降息之后
    python tools/stage.py list
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
sys.path.insert(0, str(TOOLS))

import make as hf  # noqa: E402

STAGES = ["brief", "script", "storyboard", "assets", "voice", "render"]
DEPS = {
    "brief": [],
    "script": ["brief"],
    "storyboard": ["script"],
    "assets": ["storyboard"],
    "voice": ["script"],
    "render": ["storyboard", "voice"],
}
TITLES = {
    "brief": "立项",
    "script": "文案",
    "storyboard": "分镜",
    "assets": "素材",
    "voice": "配音",
    "render": "渲染",
}


# ---------- 通用 ----------

def vdir(slug: str) -> Path:
    return VIDEOS / slug


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def disp_len(s: str) -> float:
    """显示宽度：中文算 1，英文/数字算 0.5。"""
    import unicodedata
    w = 0.0
    for ch in s:
        if ch.isspace():
            continue
        w += 1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.5
    return w


def sha1_files(paths: list[Path]) -> str:
    h = hashlib.sha1()
    for p in paths:
        if p.exists() and p.is_file():
            h.update(p.read_bytes())
        else:
            h.update(b"<missing>")
    return h.hexdigest()[:16]


def load(slug: str) -> dict:
    p = vdir(slug) / "project.json"
    if not p.exists():
        raise SystemExit(f"没有这个视频：{slug}\n  先运行：python tools\\stage.py brief {slug}")
    proj = json.loads(p.read_text(encoding="utf-8"))
    if "stages" not in proj:
        migrate(proj)
        save(slug, proj)
    return proj


def migrate(proj: dict) -> None:
    """旧版 project.json（video.py 时代）补上阶段状态。"""
    d = vdir(proj["slug"])
    stages = {}

    def done(name, ok, artifacts):
        stages[name] = {"status": "done" if ok else "pending", "at": now(),
                        "confirmed": bool(ok), "artifacts": artifacts}

    done("brief", False, [])
    if not stages["brief"]["status"] == "done":
        stages["brief"] = {"status": "skipped", "at": now(), "confirmed": True, "artifacts": []}

    script = (d / "script.txt")
    done("script", script.exists() and bool(script.read_text(encoding="utf-8").strip()),
         ["script.txt", "script.json"])
    done("storyboard", (d / "scenes.json").exists(), ["scenes.json", "storyboard.md"])
    done("assets", (d / "media" / "index.json").exists(), ["media/index.json"])
    if not (d / "media" / "index.json").exists():
        stages["assets"] = {"status": "skipped", "at": now(), "confirmed": True, "artifacts": []}
    audio = (d / "audio")
    has_audio = any(audio.glob("vo.*")) if audio.exists() else False
    done("voice", has_audio, ["audio/"])
    done("render", (d / "render.mp4").exists(), ["render.mp4", "render.json"])
    proj["stages"] = stages


def save(slug: str, proj: dict) -> None:
    (vdir(slug) / "project.json").write_text(
        json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")


def stage_out(proj: dict, name: str) -> Path:
    d = vdir(proj["slug"])
    return {
        "brief": d / "brief.md",
        "script": d / "script.txt",
        "storyboard": d / "scenes.json",
        "assets": d / "media" / "index.json",
        "voice": vdir(proj["slug"]) / "voice.json",
        "render": d / "render.mp4",
    }[name]


def stage_status(slug: str, proj: dict, name: str, _seen: set | None = None) -> str:
    _seen = _seen or set()
    if name in _seen:
        return proj.get("stages", {}).get(name, {}).get("status", "pending")
    _seen.add(name)

    st = proj.get("stages", {}).get(name, {})
    status = st.get("status", "pending")
    if status in ("skipped", "pending"):
        return status

    # 上游过期 → 本阶段也过期（级联）
    for d in DEPS[name]:
        ds = proj.get("stages", {}).get(d, {}).get("status")
        if ds in (None, "pending"):
            continue
        if stage_status(slug, proj, d, set(_seen)) in ("stale", "pending"):
            return "stale"

    # 上游产物变了？
    files = [stage_out(proj, d) for d in DEPS[name]
             if proj.get("stages", {}).get(d, {}).get("status") not in (None, "pending", "skipped")]
    current = sha1_files(files)
    if st.get("input_hash") and st["input_hash"] != current:
        return "stale"
    return status


def mark(slug: str, proj: dict, name: str, status: str = "done", artifacts: list[str] | None = None) -> None:
    deps = DEPS[name]
    files = [stage_out(proj, d) for d in deps if proj.get("stages", {}).get(d, {}).get("status") not in (None, "pending", "skipped")]
    proj.setdefault("stages", {})[name] = {
        "status": status,
        "at": now(),
        "input_hash": sha1_files(files),
        "confirmed": false_placeholder(),
        "artifacts": artifacts or [],
    }


def false_placeholder() -> bool:
    return False


def require_deps(slug: str, proj: dict, name: str, force: bool) -> None:
    for d in DEPS[name]:
        st = proj.get("stages", {}).get(d, {})
        if st.get("status") == "skipped":
            continue
        if st.get("status") != "done":
            if force:
                print(f"  [提醒] 上游 {d} 未完成，已按 --force 继续")
                continue
            raise SystemExit(
                f"上游「{TITLES[d]}」还没完成（当前 {st.get('status','pending')}）\n"
                f"  先运行：python tools\\stage.py {d} {slug}\n"
                f"  或加 --force 跳过检查"
            )
        if not st.get("confirmed") and not force:
            raise SystemExit(
                f"上游「{TITLES[d]}」还没确认\n"
                f"  看过产物后运行：python tools\\stage.py confirm {slug} {d}"
            )


# ---------- P0 brief ----------

def strip_md(text: str) -> tuple[str, dict]:
    """清洗 markdown，返回 (正文, 结构信息)。"""
    info = {"title": "", "headings": [], "quotes": [], "lists": [], "images": [], "removed": {}}

    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        fm = m.group(1)
        t = re.search(r"^title:\s*(.+)$", fm, re.M)
        if t:
            info["title"] = t.group(1).strip().strip("\"'")
        text = text[m.end():]
        info["removed"]["frontmatter"] = 1

    codes = re.findall(r"```.*?```", text, re.S)
    info["removed"]["code_blocks"] = len(codes)
    text = re.sub(r"```.*?```", "\n", text, flags=re.S)

    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    info["images"] = imgs
    info["removed"]["images"] = len(imgs)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.M)
    text = re.sub(r"^>\s?", "", text, flags=re.M)

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            h = s.lstrip("#").strip()
            if h:
                info["headings"].append(h)
            continue
        bold = re.findall(r"\*\*(.+?)\*\*", s)
        info["quotes"].extend([b.strip() for b in bold if len(b.strip()) >= 8])

    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), info


def classify(chars: int, target: int, avg_sentence: float) -> tuple[str, str]:
    ratio = chars / max(target * 4.5, 1)
    if ratio <= 1.15 and avg_sentence <= 32:
        return "A", "已接近口播稿，直接分句即可"
    if ratio <= 3:
        return "B", f"文章体，需压缩到约 {int(target*4.5)} 字（约 {100/max(ratio,0.01):.0f}%）"
    if ratio <= 6:
        return "C", "偏长，建议只取核心段落"
    return "D", "信息密度过高，建议重写而不是压缩"


def cmd_brief(a) -> None:
    slug = a.slug
    d = vdir(slug)
    if (d / "project.json").exists() and not a.force:
        raise SystemExit(f"已存在：videos/{slug}（要重建加 --force）")

    target = a.duration
    src_text, info = "", {"title": "", "headings": [], "quotes": [], "lists": [], "images": [], "removed": {}}
    src_path = None

    if a.from_:
        src = Path(a.from_)
        if not src.exists():
            raise SystemExit(f"找不到文稿：{src}")
        raw = src.read_text(encoding="utf-8", errors="ignore")
        src_text, info = strip_md(raw)
        (d / "source").mkdir(parents=True, exist_ok=True)
        src_path = d / "source" / src.name
        src_path.write_text(raw, encoding="utf-8")

    body = src_text or "（还没有文案，请在 script.txt 里写）"
    chars = len(re.sub(r"\s", "", src_text))
    sentences = [s for s in re.split(r"[。！？!?]", src_text) if s.strip()]
    avg = (chars / len(sentences)) if sentences else 0
    kind, advice = classify(chars, target, avg)

    proj = {
        "slug": slug,
        "theme": a.theme,
        "theme_overrides": {},
        "width": a.width, "height": a.height, "fps": 30,
        "engine": a.engine,
        "voice": a.voice,
        "voice_pack": a.voice_pack,
        "rate": "+0%",
        "subtitles": not a.no_subtitles,
        "target_seconds": target,
        "source": {"file": str(src_path.relative_to(d)) if src_path else "", "chars": chars, "kind": kind},
        "created": now(),
        "stages": {},
    }

    (d / "audio").mkdir(parents=True, exist_ok=True)
    (d / "media").mkdir(parents=True, exist_ok=True)
    (d / "script.txt").write_text((src_text or "") + "\n", encoding="utf-8")

    # 种子分镜：标题 + 两条要点 + 结尾，用户在此基础上改
    title = (info.get("title") or slug)[:16]
    heads = [h for h in info.get("headings", []) if 0 < len(h) <= 12][:2]
    if not heads:
        heads = ["要点一", "要点二"]
    (d / "scenes.json").write_text(json.dumps({
        "scenes": [
            {"type": "title", "kicker": "", "title": title, "sub": ""},
            {"type": "list", "mark": "number", "rows": heads},
            {"type": "ending", "title": "关注我", "accent": "关注", "sub": ""},
        ]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    brief = [
        f"# 立项 · {slug}",
        "",
        f"- 目标时长：{target} 秒（约 {int(target*4.5)} 字）",
        f"- 风格：{a.theme}（{hf.THEMES[a.theme]['label']}）",
        f"- 尺寸：{a.width}x{a.height}",
        f"- 配音：{a.engine}" + (f" · {a.voice_pack}" if a.voice_pack else f" · {a.voice}"),
        f"- 来源：{src_path.name if src_path else '无（手写）'}" + (f"（{chars} 字）" if chars else ""),
        "",
    ]
    if src_text:
        brief += [
            "## 体检",
            "",
            f"- 字数：{chars}",
            f"- 句子数：{len(sentences)}",
            f"- 平均句长：{avg:.0f} 字（口播上限 40）",
            f"- 类型：{kind}",
            f"- 建议：{advice}",
            "",
        ]
        if info["removed"]:
            brief.append("- 已清理：" + "、".join(f"{k} {v} 处" for k, v in info["removed"].items() if v))
            brief.append("")
        if info["title"]:
            brief += ["## 候选标题", "", f"- {info['title']}", ""]
        if info["headings"]:
            brief += ["## 小标题（可作分屏）", ""] + [f"- {h}" for h in info["headings"][:8]] + [""]
        if info["quotes"]:
            brief += ["## 金句候选（原文加粗）", ""] + [f"- {q}" for q in info["quotes"][:6]] + [""]
        if info["images"]:
            brief += ["## 图片（需手动入库）", ""] + [f"- {p}" for p in info["images"][:8]] + [""]
        brief += ["## 需要你决定", "",
                  "1. 全文压缩，还是只取其中几段？",
                  "2. 标题用原文，还是另起一个？",
                  "3. 有没有必须保留的句子？",
                  ""]

    (d / "brief.md").write_text("\n".join(brief), encoding="utf-8")
    mark(slug, proj, "brief", artifacts=["brief.md"])
    for s in STAGES[1:]:
        proj.setdefault("stages", {})[s] = {"status": "pending"}
    save(slug, proj)

    print(f"已立项 videos/{slug}")
    print(f"  主题 {a.theme}  目标 {target}s  共 {chars} 字（{kind} 类）")
    print(f"  产物 brief.md、script.txt（原文已清洗写入）")
    if src_text:
        print(f"\n  建议：{advice}")
    print(f"\n下一步：看 brief.md，确认后运行")
    print(f"  python tools\\stage.py confirm {slug} brief")
    print(f"  python tools\\stage.py script {slug}")


# ---------- P1 script ----------

def cmd_script(a) -> None:
    slug = a.slug
    proj = load(slug)
    require_deps(slug, proj, "script", a.force)

    text = (vdir(slug) / "script.txt").read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("script.txt 是空的")

    chars = len(re.sub(r"\s", "", text))
    target = proj.get("target_seconds", 45)
    est = chars / 4.5
    sentences = [s.strip() for s in re.split(r"[。！？!?]", text) if s.strip()]
    long_sents = [s for s in sentences if len(s) > 40]

    data = {
        "chars": chars,
        "estimated_seconds": round(est, 1),
        "target_seconds": target,
        "sentences": [{"i": i + 1, "text": s + "。", "chars": len(s)} for i, s in enumerate(sentences)],
        "long_sentences": long_sents,
    }
    (vdir(slug) / "script.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    mark(slug, proj, "script", artifacts=["script.txt", "script.json"])
    save(slug, proj)

    print(f"文案 {chars} 字，预计 {est:.1f} 秒（目标 {target}s）")
    if long_sents:
        print(f"  [提醒] {len(long_sents)} 句超过 40 字，TTS 会念得吃力：")
        for s in long_sents[:3]:
            print(f"    - {s[:30]}…")
    if abs(est - target) > max(5, target * 0.35):
        print(f"  [提醒] 和目标的 {target} 秒差得多")

    print(f"\n共 {len(sentences)} 句。逐句清单见 script.json")
    print(f"下一步：")
    print(f"  python tools\\stage.py confirm {slug} script")
    print(f"  python tools\\stage.py storyboard {slug}")


# ---------- P2 storyboard ----------

def cmd_storyboard(a) -> None:
    slug = a.slug
    proj = load(slug)
    require_deps(slug, proj, "storyboard", a.force)

    scenes_file = vdir(slug) / "scenes.json"
    if not scenes_file.exists():
        raise SystemExit("缺少 scenes.json")

    cfg = json.loads(scenes_file.read_text(encoding="utf-8"))
    scenes = cfg.get("scenes") or []
    if not scenes:
        raise SystemExit("scenes.json 里没有镜头")

    script = json.loads((vdir(slug) / "script.json").read_text(encoding="utf-8")) if (vdir(slug) / "script.json").exists() else {}
    transcript = None
    tp = vdir(slug) / "audio" / "transcript.json"
    if tp.exists():
        transcript = json.loads(tp.read_text(encoding="utf-8"))
    n_sent = len(transcript.get("sentences", [])) if transcript else 0

    rows, errors, warns = [], [], []
    for i, sc in enumerate(scenes, 1):
        t = sc.get("type", "?")
        idx = sc.get("start_at_sentence")
        content = ""
        if t == "title":
            content = sc.get("title", "")
        elif t == "list":
            content = " / ".join(sc.get("rows", []))
        elif t == "quote":
            content = sc.get("text", "")
        elif t == "ending":
            content = sc.get("title", "")
        elif t in ("image", "video"):
            content = sc.get("src", "")
        rows.append(f"| {i} | {idx if idx else '-'} | {t} | {content} |")

        if t == "list" and len(sc.get("rows", [])) > 2:
            warns.append(f"第 {i} 屏清单 {len(sc['rows'])} 行，逐行出现容易和语音错位")
        if t == "list":
            for j, r in enumerate(sc.get("rows", []), 1):
                if disp_len(r) > 12:
                    errors.append(f"第 {i} 屏第 {j} 行超过 12 字宽：{r}")
        if t == "title" and disp_len(sc.get("title", "")) > 16:
            errors.append(f"第 {i} 屏标题超过 16 字宽：{sc.get('title')}")
        if t == "quote" and disp_len(sc.get("text", "")) > 24:
            errors.append(f"第 {i} 屏金句超过 24 字宽")
        if idx and n_sent and not (1 <= idx <= n_sent):
            errors.append(f"第 {i} 屏 start_at_sentence={idx}，但转写只有 {n_sent} 句")
        elif idx and not n_sent:
            warns.append(f"第 {i} 屏用了 start_at_sentence={idx}，但还没有转写，暂时无法校验")

    md = ["| 屏 | 从第几句 | 类型 | 内容 |", "|---|---|---|---|"] + rows
    (vdir(slug) / "storyboard.md").write_text("# 分镜\n\n" + "\n".join(md) + "\n", encoding="utf-8")

    for e in errors:
        print(f"  [错误] {e}")
    for w in warns:
        print(f"  [提醒] {w}")
    if errors:
        raise SystemExit("分镜有错误，先改 scenes.json")

    mark(slug, proj, "storyboard", artifacts=["scenes.json", "storyboard.md"])
    save(slug, proj)

    print("\n" + "\n".join(md))
    print(f"\n下一步：")
    print(f"  python tools\\stage.py confirm {slug} storyboard")
    print(f"  python tools\\stage.py assets {slug}")


# ---------- P3 assets ----------

def cmd_assets(a) -> None:
    slug = a.slug
    proj = load(slug)
    require_deps(slug, proj, "assets", a.force)

    cfg = json.loads((vdir(slug) / "scenes.json").read_text(encoding="utf-8"))
    need = [sc["src"] for sc in cfg.get("scenes", []) if sc.get("type") in ("image", "video") and sc.get("src")]
    idx_file = vdir(slug) / "media" / "index.json"
    idx = json.loads(idx_file.read_text(encoding="utf-8")) if idx_file.exists() else {}
    missing = [n for n in need if n not in idx]

    if not need:
        proj.setdefault("stages", {})["assets"] = {"status": "skipped", "at": now(), "confirmed": True}
        save(slug, proj)
        print("这支视频没有素材需求，已跳过")
        print(f"下一步：python tools\\stage.py voice {slug}")
        return

    if missing:
        print("缺少素材：" + "、".join(missing))
        print("用命令加入：")
        for n in missing:
            print(f'  python tools\\media.py add {slug} D:\\路径\\文件.png --name "{n}"')
        raise SystemExit("补齐素材后重跑")

    mark(slug, proj, "assets", artifacts=["media/index.json"])
    save(slug, proj)
    print(f"素材齐全（{len(need)} 个）：" + "、".join(need))
    print(f"\n下一步：")
    print(f"  python tools\\stage.py confirm {slug} assets")
    print(f"  python tools\\stage.py voice {slug}")


# ---------- P4 voice ----------

def voice_file(proj: dict) -> Path:
    d = vdir(proj["slug"])
    if proj.get("engine") == "indextts" and proj.get("voice_pack"):
        return d / "audio" / f"vo_{proj['voice_pack']}.wav"
    return d / "audio" / "vo.mp3"


def cmd_voice(a) -> None:
    slug = a.slug
    proj = load(slug)
    require_deps(slug, proj, "voice", a.force)

    if a.engine:
        proj["engine"] = a.engine
    if a.voice_pack:
        proj["voice_pack"] = a.voice_pack
    if a.voice:
        proj["voice"] = a.voice

    text = (vdir(slug) / "script.txt").read_text(encoding="utf-8").strip()
    out = voice_file(proj)
    out.parent.mkdir(parents=True, exist_ok=True)

    if proj.get("engine") == "indextts":
        pack = proj.get("voice_pack")
        if not pack:
            raise SystemExit("IndexTTS2 需要 voice_pack，先用 voice.py add 加音色")
        print(f"配音 IndexTTS2 · {pack}（约 {len(text)/4.5*9/60:.1f} 分钟）")
        conda = __import__("os").environ.get("CONDA_EXE") or shutil.which("conda") or "conda"
        subprocess.run([conda, "run", "--no-capture-output", "-n", "indextts",
                        "python", str(TOOLS / "say.py"), pack,
                        "--script", str(vdir(slug) / "script.txt"), "--out", str(out)],
                       cwd=ROOT, check=True)
    else:
        print(f"配音 edge-tts · {proj.get('voice')}")
        import asyncio
        asyncio.run(hf.synth(text, proj.get("voice", "zh-CN-XiaoxiaoNeural"),
                             proj.get("rate", "+0%"), out))

    dur = hf.duration(out)
    (vdir(slug) / "voice.json").write_text(json.dumps({
        "engine": proj.get("engine"),
        "voice": proj.get("voice"),
        "voice_pack": proj.get("voice_pack"),
        "file": out.relative_to(vdir(slug)).as_posix(),
        "duration": round(dur, 2),
        "generated_at": now(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    mark(slug, proj, "voice", artifacts=[out.relative_to(vdir(slug)).as_posix(), "voice.json"])
    save(slug, proj)

    print(f"音频 {dur:.2f} 秒 -> {out.relative_to(ROOT)}")
    print(f"\n先听一遍：start {out}")
    print(f"下一步：")
    print(f"  python tools\\stage.py confirm {slug} voice")
    print(f"  python tools\\stage.py render {slug}")


# ---------- P5 render ----------

def cmd_render(a) -> None:
    slug = a.slug
    proj = load(slug)
    require_deps(slug, proj, "render", a.force)

    d = vdir(slug)
    audio = voice_file(proj)
    if not audio.exists():
        raise SystemExit("还没有配音，先运行 voice 阶段")

    extra = ["--quality", a.quality]
    if proj.get("subtitles"):
        extra.append("--subtitles")
    if a.transcribe and proj.get("subtitles"):
        extra.append("--transcribe")
    extra.append("--reuse-audio")
    extra.append("--render")

    subprocess.run([sys.executable, str(TOOLS / "make.py"), slug, *extra], cwd=ROOT, check=True)

    mp4 = d / "render.mp4"
    if not mp4.exists():
        raise SystemExit("渲染失败，没有生成 render.mp4")

    qa = d / "qa"
    qa.mkdir(exist_ok=True)
    npx = shutil.which("npx") or "npx.cmd"
    total = hf.duration(audio)
    pts = [round(total * r, 1) for r in (0.08, 0.45, 0.85)]
    subprocess.run([npx, "--yes", "hyperframes@0.9.0", "snapshot", ".",
                    "--at", ",".join(map(str, pts)), "-o", str(qa), "--keep"],
                   cwd=ROOT, check=False)

    info = {
        "quality": a.quality,
        "duration": round(total, 2),
        "bytes": mp4.stat().st_size,
        "rendered_at": now(),
        "qa": [p.name for p in sorted(qa.glob("*.png"))],
    }
    (d / "render.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    mark(slug, proj, "render", artifacts=["render.mp4", "render.json", "qa/"])
    save(slug, proj)

    print(f"\n成片 {mp4.relative_to(ROOT)}  {total:.1f}s  {mp4.stat().st_size/1024/1024:.1f} MB")
    print(f"抽帧 {len(info['qa'])} 张 -> videos/{slug}/qa/")
    print(f"\n下一步：")
    print(f"  python tools\\stage.py confirm {slug} render")
    print(f"  或回到文案：python tools\\stage.py script {slug}")


# ---------- confirm / status / next / list ----------

def cmd_confirm(a) -> None:
    slug = a.slug
    proj = load(slug)
    st = proj.get("stages", {}).get(a.stage)
    if not st:
        raise SystemExit(f"没有这个阶段：{a.stage}")
    if stage_status(slug, proj, a.stage) == "stale":
        raise SystemExit(f"「{TITLES[a.stage]}」已过期（上游改过），先重跑：\n"
                         f"  python tools\\stage.py {a.stage} {slug}")
    if st.get("status") not in ("done", "skipped"):
        raise SystemExit(f"「{TITLES[a.stage]}」还没产出（{st.get('status')}），先跑该阶段")
    st["confirmed"] = True
    st["confirmed_at"] = now()
    save(slug, proj)
    print(f"已确认：{TITLES[a.stage]}")
    nxt = next_stage(proj)
    if nxt:
        print(f"下一步：python tools\\stage.py {nxt} {slug}")
    else:
        print("全部阶段完成")


def next_stage(proj: dict) -> str | None:
    slug = proj.get("slug", "")
    for s in STAGES:
        st = proj.get("stages", {}).get(s, {})
        if st.get("status") == "skipped":
            continue
        status = stage_status(slug, proj, s) if slug else st.get("status", "pending")
        if status in (None, "pending", "stale"):
            return s
        if status == "done" and not st.get("confirmed"):
            return s
    return None


def cmd_theme(a) -> None:
    slug = a.slug
    proj = load(slug)

    if a.set:
        if a.set not in hf.THEMES:
            raise SystemExit("可用主题：" + " / ".join(hf.THEMES))
        proj["theme"] = a.set
        save(slug, proj)
        print(f"已切换主题：{a.set}（{hf.THEMES[a.set]['label']}）")
        print(f"重新渲染：python tools\\stage.py render {slug}")
        return

    if a.color:
        key, _, val = a.color.partition("=")
        if key not in ("bg", "ink", "muted", "accent", "sub_bg"):
            raise SystemExit("可覆盖：bg / ink / muted / accent / sub_bg")
        proj.setdefault("theme_overrides", {})[key] = val
        save(slug, proj)
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


def cmd_status(a) -> None:
    slug = a.slug
    proj = load(slug)
    print(f"视频 {slug}   {proj.get('target_seconds')}s   {proj.get('theme')}")
    print(f"{'阶段':<8}{'状态':<10}{'确认':<6}产物")
    print("-" * 62)
    for s in STAGES:
        st_status = stage_status(slug, proj, s)
        st = proj.get("stages", {}).get(s, {})
        conf = "✓" if st.get("confirmed") else ""
        label = {"pending": "待做", "done": "完成", "stale": "过期", "skipped": "跳过"}.get(st_status, st_status)
        arts = ", ".join(st.get("artifacts", [])[:2])
        print(f"{TITLES[s]:<8}{label:<10}{conf:<6}{arts}")
    nxt = next_stage(proj)
    print()
    if nxt:
        print(f"下一步：python tools\\stage.py {nxt} {slug}")
    else:
        print("全部完成")


def cmd_next(a) -> None:
    proj = load(a.slug)
    nxt = next_stage(proj)
    if not nxt:
        print("全部阶段完成")
        return
    status = stage_status(a.slug, proj, nxt)
    if status == "stale":
        print(f"「{TITLES[nxt]}」已过期（上游改过），需要重跑：")
        print(f"  python tools\\stage.py {nxt} {a.slug}")
    elif status == "done":
        print(f"「{TITLES[nxt]}」已产出，等待确认：")
        print(f"  python tools\\stage.py confirm {a.slug} {nxt}")
    else:
        print(f"下一阶段：{TITLES[nxt]}")
        print(f"  python tools\\stage.py {nxt} {a.slug}")


def cmd_list(a) -> None:
    if not VIDEOS.exists():
        print("还没有视频")
        return
    for d in sorted(VIDEOS.iterdir()):
        pj = d / "project.json"
        if not pj.exists():
            continue
        proj = json.loads(pj.read_text(encoding="utf-8"))
        if "stages" not in proj:
            continue
        done = sum(1 for s in STAGES if proj["stages"].get(s, {}).get("status") in ("done", "skipped"))
        print(f"  {done}/{len(STAGES)}  {d.name:<18} {proj.get('theme','?'):<12} {proj.get('target_seconds','?')}s")


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description="阶段化视频流水线")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("brief", help="立项：导入文稿、定参数")
    p.add_argument("slug")
    p.add_argument("--from", dest="from_", help="导入 md/txt 文稿")
    p.add_argument("--duration", type=int, default=45)
    p.add_argument("--theme", default=hf.DEFAULT_THEME, choices=list(hf.THEMES))
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--engine", default="edge", choices=["edge", "indextts"])
    p.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    p.add_argument("--voice-pack")
    p.add_argument("--no-subtitles", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("script", help="检查文案")
    p.add_argument("slug")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_script)

    p = sub.add_parser("storyboard", help="校验分镜并生成表")
    p.add_argument("slug")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_storyboard)

    p = sub.add_parser("assets", help="检查素材")
    p.add_argument("slug")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_assets)

    p = sub.add_parser("voice", help="生成配音")
    p.add_argument("slug")
    p.add_argument("--engine", choices=["edge", "indextts"])
    p.add_argument("--voice")
    p.add_argument("--voice-pack")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_voice)

    p = sub.add_parser("render", help="渲染成片")
    p.add_argument("slug")
    p.add_argument("--quality", default="looks", choices=["draft", "looks", "delivery"])
    p.add_argument("--transcribe", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("theme", help="查看/切换主题")
    p.add_argument("slug")
    p.add_argument("--set", help="切换预设")
    p.add_argument("--color", help="覆盖单项，如 accent=#ff6600")
    p.set_defaults(func=cmd_theme)

    p = sub.add_parser("confirm", help="确认某阶段")
    p.add_argument("slug")
    p.add_argument("stage", choices=STAGES)
    p.set_defaults(func=cmd_confirm)

    p = sub.add_parser("status", help="查看进度")
    p.add_argument("slug")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("next", help="下一步做什么")
    p.add_argument("slug")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("list", help="列出所有视频")
    p.set_defaults(func=cmd_list)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
