"""一条命令出片，按「视频」隔离。

每个视频一个文件夹，声音、画面、设置、成片都在里面，互不覆盖。

    python tools/make.py new 降息之后          # 新建一个视频文件夹
    python tools/make.py 降息之后              # 只生成（配音 + 画面）
    python tools/make.py 降息之后 --render     # 生成并渲染
    python tools/make.py 降息之后 --reuse-audio   # 只改画面，不重新配音

目录：
    videos/<名字>/
        script.txt      旁白文案
        scenes.json     画面结构 + 音色设置
        audio/vo.mp3    配音（自动生成）
        render.mp4      成片
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
DEFAULT_FONT = '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif'

SCRIPT_TPL = """这是一个测试。我想验证三件事：配音能不能生成，画面能不能渲染，最后出来的视频效果到底怎么样。
"""

SCENES_TPL = {
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "+0%",
    "scenes": [
        {"type": "title", "kicker": "栏目名", "title": "标题", "sub": "副标题"},
        {"type": "list", "mark": "1", "rows": ["要点一", "要点二", "要点三"]},
        {"type": "ending", "title": "关注我", "accent": "关注", "sub": "每周三期"},
    ],
}


# ---------- 音频 ----------

async def synth(text: str, voice: str, rate: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    await edge_tts.Communicate(text, voice, rate=rate).save(str(out))


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def detect_pauses(path: Path, threshold_db: int = -35, min_gap: float = 0.18):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af",
         f"silencedetect=noise={threshold_db}dB:d={min_gap}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
    )
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    return [(s, e, e - s) for s, e in zip(starts, ends) if e > s]


def snap_to_pause(t: float, pauses, window: float = 0.9) -> float:
    cand = [(abs((p[0] + p[1]) / 2 - t), (p[0] + p[1]) / 2) for p in pauses]
    if not cand:
        return t
    dist, at = min(cand)
    return at if dist <= window else t


def load_transcript(d: Path):
    p = d / "audio" / "transcript.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _norm(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", s).lower()


def match_sentence(text: str, sentences):
    """在转写句子里找最接近的一句，返回它的起点（秒）。"""
    import difflib
    key = _norm(text)
    if not key:
        return None
    best, best_score = None, 0.0
    for s in sentences:
        score = difflib.SequenceMatcher(None, key, _norm(s["text"])).ratio()
        if score > best_score:
            best, best_score = s, score
    return best["start"] if best and best_score >= 0.45 else None


def pick_boundaries(pauses, scenes, total: float, transcript=None, min_scene: float = 2.2):
    n = len(scenes)
    if n <= 1:
        return []

    sentences = (transcript or {}).get("sentences", [])
    usable = [p for p in pauses if p[1] < total - 0.25 and p[2] >= 0.12]
    bounds, prev = [], 0.0

    for i in range(1, n):
        sc = scenes[i]
        b = None

        # 1) 按句子编号（1 起）
        if sentences and sc.get("start_at_sentence") is not None:
            idx = int(sc["start_at_sentence"]) - 1
            if 0 <= idx < len(sentences):
                b = sentences[idx]["start"]

        # 2) 按文字匹配
        if b is None and sentences and sc.get("at_text"):
            b = match_sentence(sc["at_text"], sentences)

        # 3) 手动 hint（吸附到停顿）
        if b is None and sc.get("hint") is not None:
            b = snap_to_pause(float(sc["hint"]), usable)

        # 4) 兜底：均分 + 找停顿
        if b is None:
            ideal = total * i / n
            lo = max(prev + min_scene, ideal - total * 0.12)
            hi = min(total - min_scene * (n - i), ideal + total * 0.12)
            cand = [p for p in usable
                    if lo <= (p[0] + p[1]) / 2 <= hi and p[0] > prev + min_scene]
            if cand:
                best = max(cand, key=lambda p: p[2] - 1.5 * abs((p[0] + p[1]) / 2 - ideal))
                b = (best[0] + best[1]) / 2
            elif lo <= ideal <= hi:
                b = ideal
            else:
                b = min(max(ideal, lo), total - min_scene * (n - i))

        b = min(max(b, prev + 0.5), total - 0.3)
        bounds.append(b)
        prev = b

    return bounds


# ---------- HTML ----------

CSS = """
      @font-face { font-family: "Microsoft YaHei UI"; src: local("Microsoft YaHei UI"); }
      @font-face { font-family: "Microsoft YaHei"; src: local("Microsoft YaHei"); }
      @font-face { font-family: "PingFang SC"; src: local("PingFang SC"); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        width: %(W)dpx; height: %(H)dpx; overflow: hidden;
        background: #0a0e13; color: #f4f7fb; font-family: %(FONT)s;
      }
      #root {
        position: relative; width: 100%%; height: 100%%;
        background: radial-gradient(1100px 700px at 50%% 42%%, rgba(94,234,212,0.10), transparent 70%%), #0a0e13;
      }
      .clip {
        position: absolute; inset: 0; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; padding: 0 120px;
      }
      .kicker { font-size: 30px; letter-spacing: .32em; color: #5eead4; margin-bottom: 34px; }
      h1 { font-size: 120px; font-weight: 700; letter-spacing: -.02em; line-height: 1.12; }
      .sub { font-size: 40px; color: #8b9bb0; margin-top: 40px; letter-spacing: .04em; }
      .rows { display: flex; flex-direction: column; gap: 44px; }
      .row { display: flex; align-items: center; gap: 32px; font-size: 58px; font-weight: 500; }
      .row .mark { font-size: 50px; color: #5eead4; flex: none; }
      .quote { font-size: 64px; line-height: 1.5; max-width: 1500px; color: #e6edf6; }
      .accent { color: #5eead4; }
      .figwrap { display: flex; flex-direction: column; align-items: center; gap: 26px; padding-bottom: 150px; }
      .fig { max-width: 1420px; max-height: 680px; object-fit: contain; border-radius: 18px; }
      .figcap { font-size: 38px; color: #8b9bb0; letter-spacing: .02em; }
      .vid { max-width: 1620px; max-height: 860px; border-radius: 18px; }
      .subs { position: absolute; left: 0; right: 0; bottom: 84px; z-index: 10; text-align: center; }
      .cue {
        position: absolute; left: 50%%; transform: translateX(-50%%); bottom: 0;
        max-width: 1500px; font-size: 40px; line-height: 1.45; font-weight: 500;
        color: #fff; opacity: 0;
        text-shadow: 0 2px 18px rgba(0,0,0,0.85);
        padding: 8px 26px; border-radius: 12px;
        background: rgba(6, 10, 16, 0.62);
      }
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def split_long(cue: dict, limit: int = 16):
    """把过长的字幕按标点拆成多条，时间按字数比例分配。"""
    text = cue["text"]
    if len(text) <= limit:
        return [cue]
    parts = re.findall(r"[^，。！？、；：,.!?;:]+[，。！？、；：,.!?;:]?", text)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= limit:
            cur += p
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    if len(chunks) <= 1:
        return [cue]

    total_chars = sum(len(c) for c in chunks) or 1
    t0, out = cue["start"], []
    for ch in chunks:
        d = (cue["end"] - cue["start"]) * len(ch) / total_chars
        out.append({"text": ch.strip(), "start": round(t0, 3), "end": round(t0 + d, 3)})
        t0 += d
    return out


def build_cues(script_text: str, transcript: dict):
    """把脚本文字按句子切成字幕条，时间取自 ASR 的逐字时间戳。"""
    import difflib

    # ASR 逐字时间
    asr_chars, asr_times = [], []
    for s in transcript.get("sentences", []):
        for w in s.get("words", []):
            asr_chars.append(w["text"])
            asr_times.append((w["start"], w["end"]))
    if not asr_chars:
        return []

    asr_key = "".join(asr_chars).lower()

    # 脚本 → 只保留有意义的字符，记录原始位置
    keep, idx_map = [], []
    for i, ch in enumerate(script_text):
        if ch.strip() and ch not in "，。！？：；、,.!?:;\"'“”‘’（）()【】[]《》—…-":
            keep.append(ch.lower())
            idx_map.append(i)
    target = "".join(keep)

    # 对齐
    times = [None] * len(target)
    sm = difflib.SequenceMatcher(None, asr_key, target, autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            if b + k < len(times) and a + k < len(asr_times):
                times[b + k] = asr_times[a + k]

    # 填充没对上的
    last = None
    for i in range(len(times)):
        if times[i] is None:
            times[i] = last
        else:
            last = times[i]
    last = None
    for i in range(len(times) - 1, -1, -1):
        if times[i] is None:
            times[i] = last
        else:
            last = times[i]
    if all(t is None for t in times):
        return []

    # 按原脚本的标点切句
    cues, start = [], 0
    for i, ch in enumerate(script_text):
        if ch in "。！？!?" or i == len(script_text) - 1:
            text = script_text[start:i + 1].strip()
            if text:
                j0 = next((k for k, orig in enumerate(idx_map) if orig >= start), None)
                j1 = max((k for k, orig in enumerate(idx_map) if orig <= i), default=None)
                if j0 is not None and j1 is not None and times[j0] and times[j1]:
                    cues.append({
                        "text": text,
                        "start": round(times[j0][0], 3),
                        "end": round(times[j1][1] + 0.25, 3),
                    })
            start = i + 1

    # 顺序修正，避免重叠
    for i in range(len(cues) - 1):
        if cues[i]["end"] > cues[i + 1]["start"]:
            cues[i]["end"] = max(cues[i]["start"] + 0.4, cues[i + 1]["start"] - 0.02)
    cues = [c for c in cues if c["end"] - c["start"] > 0.3]

    # 过长拆条
    out = []
    for c in cues:
        out.extend(split_long(c))
    return out


def subs_html(cues, total: float) -> str:
    items = "\n".join(
        f'        <div id="cue{i}" class="cue">{esc(c["text"])}</div>'
        for i, c in enumerate(cues))
    return f'      <div class="subs">\n{items}\n      </div>'


def subs_timeline(cues) -> list[str]:
    out = []
    for i, c in enumerate(cues):
        out.append(f'      tl.set("#cue{i}", {{ opacity: 1 }}, {c["start"]:.2f})')
        out.append(f'        .set("#cue{i}", {{ opacity: 0 }}, {c["end"]:.2f})')
    return out


def build_html(scenes, bounds, audio_rel, total, width, height, cues=None, media_url=None):
    starts = [0.0] + bounds
    ends = bounds + [total]
    sections, tl = [], []

    for i, sc in enumerate(scenes):
        s, e = starts[i], ends[i]
        sid = f"s{i+1}"
        kind = sc.get("type", "title")

        if kind == "title":
            body = (f'<div id="k{i}" class="kicker">{esc(sc.get("kicker",""))}</div>\n'
                    f'        <h1 id="t{i}">{esc(sc.get("title",""))}</h1>\n'
                    f'        <div id="sub{i}" class="sub">{esc(sc.get("sub",""))}</div>')
            tl.append(f'      tl.from("#k{i}", {{ opacity: 0, y: 18, duration: 0.45, ease: "power2.out" }}, {s+0.15:.2f})')
            tl.append(f'        .from("#t{i}", {{ y: 56, duration: 0.75, ease: "power3.out" }}, {s+0.3:.2f})')
            tl.append(f'        .from("#sub{i}", {{ opacity: 0, duration: 0.5, ease: "power2.out" }}, {s+0.8:.2f})')
            tl.append(f'        .to(["#k{i}", "#t{i}", "#sub{i}"], {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {max(s+0.4, e-0.5):.2f});')

        elif kind == "list":
            rows = sc.get("rows", [])
            mark = sc.get("mark", "✓")
            def m(j):
                return str(j + 1) if mark == "number" else mark
            items = "\n".join(
                f'          <div id="r{i}_{j}" class="row"><span class="mark">{esc(m(j))}</span>'
                f'<span>{esc(r)}</span></div>' for j, r in enumerate(rows))
            body = f'        <div class="rows">\n{items}\n        </div>'
            gap = max(e - s - 1.0, 0.6) / max(len(rows), 1)
            for j in range(len(rows)):
                tl.append(f'      tl.from("#r{i}_{j}", {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, {s + 0.2 + j * gap:.2f})')
            tl.append(f'        .to("#s{i+1} .rows", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.45):.2f});')

        elif kind == "quote":
            body = f'        <div id="q{i}" class="quote">{esc(sc.get("text",""))}</div>'
            tl.append(f'      tl.from("#q{i}", {{ opacity: 0, y: 30, duration: 0.6, ease: "power2.out" }}, {s+0.2:.2f})')
            tl.append(f'        .to("#q{i}", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.45):.2f});')

        elif kind == "image":
            if not media_url:
                raise SystemExit(f"第 {i+1} 个镜头用了 image，但没有素材库")
            url = media_url(sc.get("src", ""))
            cap = esc(sc.get("caption", ""))
            body = (f'        <div class="figwrap">\n'
                    f'          <img id="fig{i}" class="fig" src="{url}" />\n'
                    + (f'          <div id="cap{i}" class="figcap">{cap}</div>\n' if cap else "")
                    + '        </div>')
            tl.append(f'      tl.fromTo("#fig{i}", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }}, {s+0.15:.2f})')
            if cap:
                tl.append(f'        .from("#cap{i}", {{ opacity: 0, duration: 0.45, ease: "power2.out" }}, {s+0.55:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.4):.2f});')

        elif kind == "video":
            if not media_url:
                raise SystemExit(f"第 {i+1} 个镜头用了 video，但没有素材库")
            url = media_url(sc.get("src", ""))
            dur = e - s
            body = (f'        <video id="vid{i}" class="vid" src="{url}" muted playsinline\n'
                    f'               data-start="0" data-duration="{dur:.2f}"></video>')
            tl.append(f'      tl.fromTo("#vid{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, {s+0.1:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {max(s+0.3, e-0.35):.2f});')

        else:
            title = sc.get("title", "")
            accent = sc.get("accent", "")
            if accent and accent in title:
                title = title.replace(accent, f'<span class="accent">{esc(accent)}</span>', 1)
            else:
                title = esc(title)
            body = (f'        <h1 id="t{i}" class="big">{title}</h1>\n'
                    f'        <div id="sub{i}" class="sub">{esc(sc.get("sub",""))}</div>')
            tl.append(f'      tl.fromTo("#t{i}", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.65, ease: "power3.out" }}, {s+0.2:.2f})')
            tl.append(f'        .from("#sub{i}", {{ opacity: 0, duration: 0.5, ease: "power2.out" }}, {s+0.7:.2f})')
            tl.append(f'        .to("#t{i}", {{ scale: 1.03, duration: {max(e - s - 1.0, 0.6):.2f}, ease: "none" }}, {s+1.0:.2f});')

        sections.append(
            f'      <section id="{sid}" class="clip" data-start="{s:.2f}" data-duration="{e-s:.2f}">\n'
            f'{body}\n      </section>')

    css = CSS % {"W": width, "H": height, "FONT": DEFAULT_FONT}
    sub_layer = subs_html(cues, total) if cues else ""
    sub_js = "\n".join(subs_timeline(cues)) if cues else ""
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>{css}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0"
         data-width="{width}" data-height="{height}" data-duration="{total:.2f}">
      <audio id="vo" src="{audio_rel}" data-start="0" data-duration="{total:.2f}"></audio>

{chr(10).join(sections)}
{sub_layer}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tl)}
{sub_js}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


# ---------- 命令 ----------

def cmd_new(slug: str) -> None:
    d = VIDEOS / slug
    if d.exists():
        print(f"已存在：videos/{slug}")
        return
    (d / "audio").mkdir(parents=True)
    (d / "script.txt").write_text(SCRIPT_TPL, encoding="utf-8")
    (d / "scenes.json").write_text(
        json.dumps(SCENES_TPL, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已创建 videos/{slug}")
    print(f"  改 videos/{slug}/script.txt   文案")
    print(f"  改 videos/{slug}/scenes.json  画面")
    print(f"  然后 python tools/make.py {slug} --render")


def cmd_build(slug: str, args) -> None:
    d = VIDEOS / slug
    if not d.exists():
        raise SystemExit(f"没有这个视频：videos/{slug}（先用 new 创建）")

    script = (d / "script.txt").read_text(encoding="utf-8").strip()
    cfg = json.loads((d / "scenes.json").read_text(encoding="utf-8"))
    scenes = cfg["scenes"]
    voice = args.voice or cfg.get("voice", "zh-CN-XiaoxiaoNeural")
    rate = args.rate or cfg.get("rate", "+0%")

    engine = args.engine or cfg.get("engine", "edge")
    pack = args.voice_pack or cfg.get("voice_pack")
    audio = Path(args.audio) if args.audio else None

    if engine == "indextts" and not audio:
        if not pack:
            raise SystemExit(
                "IndexTTS2 需要指定音色：--voice-pack 名字\n"
                "  查看已有音色：python tools\\voice.py list"
            )
        audio = d / "audio" / f"vo_{pack}.wav"
    if audio is None:
        audio = d / "audio" / "vo.mp3"
    if not audio.is_absolute():
        audio = (d / audio) if not (ROOT / audio).exists() else ROOT / audio

    if not args.reuse_audio:
        if engine == "indextts":
            print(f"[1/4] 配音  IndexTTS2 · 音色「{pack}」（约 2 分钟）")
            conda = os.environ.get("CONDA_EXE") or shutil.which("conda") or "conda"
            subprocess.run([conda, "run", "--no-capture-output", "-n", "indextts",
                            "python", str(Path(__file__).parent / "say.py"), pack,
                            "--script", str(d / "script.txt"), "--out", str(audio)],
                           cwd=ROOT, check=True)
        else:
            print(f"[1/4] 配音  {voice} {rate}")
            asyncio.run(synth(script, voice, rate, audio))

    total = duration(audio)
    print(f"      时长 {total:.2f}s")

    print(f"[2/4] 时间轴")
    if args.transcribe:
        print("      转写中（FunASR，约 30 秒）…")
        conda = os.environ.get("CONDA_EXE") or shutil.which("conda") or "conda"
        subprocess.run([conda, "run", "--no-capture-output", "-n", "indextts",
                        "python", str(Path(__file__).parent / "transcribe.py"), slug,
                        "--audio", str(audio)], cwd=ROOT, check=True)
    transcript = load_transcript(d)
    bounds = pick_boundaries(detect_pauses(audio), scenes, total, transcript)
    if bounds:
        print("      分界 " + " | ".join(f"{b:.2f}s" for b in bounds))
    if transcript:
        print(f"      参考转写 {len(transcript.get('sentences', []))} 句")

    rel = quote(audio.relative_to(ROOT).as_posix())

    idx_path = d / "media" / "index.json"
    media = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}

    def media_url(key: str) -> str:
        if not key:
            raise SystemExit("image/video 镜头缺少 src")
        e = media.get(key)
        if not e:
            raise SystemExit(f"素材库里没有「{key}」，用 python tools/media.py list {slug} 查看")
        f = Path(e["file"])
        p = f if f.is_absolute() else (d / "media" / f)
        return quote(p.relative_to(ROOT).as_posix())

    cues = build_cues(script, transcript) if (args.subtitles and transcript) else None
    if cues and scenes:
        starts = [0.0] + bounds
        ends = bounds + [total]
        kept = []
        for c in cues:
            mid = (c["start"] + c["end"]) / 2
            if any(scenes[i].get("type") in ("quote", "ending") and starts[i] - 0.05 <= mid <= ends[i]
                   for i in range(len(scenes))):
                continue
            kept.append(c)
        cues = kept
    (ROOT / "index.html").write_text(
        build_html(scenes, bounds, rel, total, args.width, args.height, cues, media_url), encoding="utf-8")
    print(f"[3/4] index.html  {len(scenes)} 个镜头" + (f" + {len(cues)} 条字幕" if cues else ""))

    if args.render:
        npx = shutil.which("npx") or "npx.cmd"
        subprocess.run([npx, "--yes", "hyperframes@0.9.0", "check", "."], cwd=ROOT)
        out = d / "render.mp4"
        subprocess.run([npx, "--yes", "hyperframes@0.9.0", "render", ".",
                        "-o", str(out), "-q", "draft", "-w", "2"], cwd=ROOT)
        print(f"[4/4] 成片 -> videos/{slug}/render.mp4")
    else:
        print(f"[4/4] 跳过渲染（加 --render）")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="视频名，或 new <名字>")
    ap.add_argument("extra", nargs="?", help=argparse.SUPPRESS)
    ap.add_argument("--voice")
    ap.add_argument("--rate")
    ap.add_argument("--audio", help="指定现成音频（相对 videos/<slug>/ 或项目根）")
    ap.add_argument("--reuse-audio", action="store_true")
    ap.add_argument("--engine", choices=["edge", "indextts"],
                    help="配音引擎：edge（默认，2 秒）或 indextts（克隆音色，约 2 分钟）")
    ap.add_argument("--voice-pack", help="声音库里的音色名（IndexTTS2 用），见 tools/voice.py list")
    ap.add_argument("--transcribe", action="store_true",
                    help="先用 FunASR 转写，时间轴按句子边界对齐（需要 indextts 环境）")
    ap.add_argument("--subtitles", action="store_true",
                    help="用转写结果生成底部字幕轨（需要 transcript.json）")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()

    if args.slug == "new":
        if not args.extra:
            raise SystemExit("用法：python tools/make.py new 视频名")
        cmd_new(args.extra)
    else:
        cmd_build(args.slug, args)


if __name__ == "__main__":
    main()
