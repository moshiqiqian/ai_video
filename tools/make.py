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

TPL = ROOT / "templates"
DEFAULT_THEME = "dark-teal"

# 主题与样式从 templates/ 读取，代码里不再硬编码
THEMES = json.loads((TPL / "themes.json").read_text(encoding="utf-8"))
CSS = ((TPL / "base.css").read_text(encoding="utf-8") + "\n"
       + (TPL / "ink.css").read_text(encoding="utf-8") + "\n"
       + (TPL / "code.css").read_text(encoding="utf-8") + "\n"
       + (TPL / "wave.css").read_text(encoding="utf-8"))


def render_ink(sc: dict, i: int) -> str:
    html = (TPL / "ink" / "mountains.html").read_text(encoding="utf-8")
    for k, v in (("id", f"ink{i}"), ("text", esc(sc.get("text", ""))),
                 ("sub", esc(sc.get("sub", ""))), ("seal", esc(sc.get("seal", ""))),
                 ("accent", "#a63a2e")):
        html = html.replace("{{" + k + "}}", str(v))
    return html


def render_chart(sc: dict, i: int) -> tuple[str, list]:
    data = sc.get("data") or []
    unit = sc.get("unit", "")
    vmax = max([float(d.get("v", 0)) for d in data] + [1])
    bars, anim = [], []
    for j, d in enumerate(data):
        h = int(420 * float(d.get("v", 0)) / vmax)
        bid = f"bar{i}_{j}"
        bars.append(
            f'          <div class="bar-wrap">'
            f'<div class="bar-val"><span id="{bid}-n">0</span>{esc(unit)}</div>'
            f'<div id="{bid}" class="bar" style="height:{h}px"></div>'
            f'<div class="bar-lbl">{esc(d.get("l", ""))}</div>'
            f'</div>')
        anim.append((bid, float(d.get("v", 0))))
    html = (
        f'        <div class="chart">\n'
        f'          <div class="chart-title">{esc(sc.get("title", ""))}</div>\n'
        f'          <div class="chart-axis"></div>\n'
        + "\n".join(bars) + "\n        </div>")
    return html, anim


def render_code(sc: dict, i: int) -> tuple[str, list]:
    tpl = (TPL / "code" / "terminal.html").read_text(encoding="utf-8")
    lines = []
    for j, ln in enumerate(sc.get("lines", [])):
        kind = ln.get("k", "out")
        cls = {"cmd": "term-cmd", "ok": "term-ok"}.get(kind, "term-out")
        prompt = '<span class="term-prompt">$</span>' if kind == "cmd" else ""
        lines.append(f'              <div id="code{i}_l{j}" class="term-line {cls}">{prompt}{esc(ln.get("t", ""))}</div>')
    html = (tpl.replace("{{id}}", f"code{i}")
                .replace("{{title}}", esc(sc.get("title", "terminal")))
                .replace("{{lines}}", "\n".join(lines)))
    return html, [f"code{i}_l{j}" for j in range(len(lines))]


def render_wave(sc: dict, i: int) -> tuple[str, list]:
    import math
    bars = []
    for j in range(44):
        h = 190 + int(300 * abs(math.sin(j * 0.7 + 1.2)) + 90 * abs(math.sin(j * 1.9)))
        bars.append(f'<div id="wv{i}_{j}" class="wbar" style="height:{h}px"></div>')
    html = (f'        <div class="wave">\n'
            f'          <div class="wave-title">{esc(sc.get("title", ""))}</div>\n'
            f'          <div class="wave-sub">{esc(sc.get("sub", ""))}</div>\n'
            + "\n".join(bars) + "\n        </div>")
    return html, [f"wv{i}_{j}" for j in range(44)]


def render_block(name: str, **kw) -> str:
    """从 templates/blocks/<name>.html 渲染一个版式片段。"""
    tpl = (TPL / "blocks" / f"{name}.html").read_text(encoding="utf-8")
    for k, v in kw.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


PPT = TPL / "ppt"


def render_ppt(blocks: list, idx: int):
    """渲染 PPT 风格的多块版式，返回 (html, [(block_id, order)])。"""
    parts, anim, counters = [], [], []
    for j, b in enumerate(blocks):
        name = b.get("block")
        bid = f"ppt{idx}_{j}"
        path = PPT / f"{name}.html"
        if not path.exists():
            raise SystemExit(f"未知的 ppt 块：{name}（templates/ppt/ 下没有）")
        html = path.read_text(encoding="utf-8")

        if name == "masthead":
            html = (html.replace("{{brand}}", esc(b.get("brand", "")))
                        .replace("{{sub}}", esc(b.get("sub", "")))
                        .replace("{{issue}}", esc(b.get("issue", ""))))
        elif name == "headline":
            html = (html.replace("{{text}}", esc(b.get("text", "")))
                        .replace("{{deck}}", esc(b.get("deck", ""))))
        elif name == "cards":
            cards = "".join(
                f'<div class="ppt-card"><h3>{esc(c.get("t", ""))}</h3>'
                f'<p>{esc(c.get("d", ""))}</p></div>'
                for c in b.get("items", []))
            html = html.replace("{{cards}}", cards)
        elif name == "stats":
            segs = []
            for k, it in enumerate(b.get("items", [])):
                segs.append(f'<div class="ppt-stat"><b id="{bid}-n{k}">0</b>'
                            f'<span>{esc(it.get("l", ""))}</span></div>')
                try:
                    v = float(str(it.get("n", "0")).replace("%", "").replace("+", ""))
                except ValueError:
                    v = 0.0
                counters.append((f"{bid}-n{k}", v))
            html = html.replace("{{items}}", "".join(segs))
        elif name == "pipeline":
            segs = []
            for k, s in enumerate(b.get("steps", [])):
                if k:
                    segs.append('<span class="ppt-arrow">→</span>')
                segs.append(f'<div class="ppt-step"><i>{k + 1:02d}</i>'
                            f'<strong>{esc(s)}</strong></div>')
            html = html.replace("{{items}}", "".join(segs))
        elif name == "band":
            html = html.replace("{{text}}", esc(b.get("text", "")))

        parts.append(html.replace("{{id}}", bid))
        anim.append((bid, j))
    return "\n".join(parts), anim, counters


def resolve_theme(name: str = None, overrides: dict = None) -> dict:
    """返回主题字典，支持覆盖单项颜色。"""
    preset = THEMES.get(name or DEFAULT_THEME, THEMES[DEFAULT_THEME])
    t = dict(preset)
    for k, v in (overrides or {}).items():
        if k in ("bg", "ink", "muted", "accent", "sub_bg"):
            t[k] = v
    return t


def _rgba(hex_color: str, alpha: float) -> str:
    """#rrggbb -> rgba(...)，用于背景光晕。"""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return f"rgba(94,234,212,{alpha})"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

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
    for rel in ("build/transcript.json", "audio/transcript.json"):
        p = d / rel
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



def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fill_cues(cues, total: float):
    """保证字幕全程连续：从 0 开始，到 total 结束，中间不留空档。"""
    if not cues:
        return cues
    cues = sorted(cues, key=lambda c: c["start"])
    cues[0]["start"] = 0.0
    for i in range(len(cues) - 1):
        # 不重叠
        if cues[i]["end"] > cues[i + 1]["start"]:
            cues[i]["end"] = cues[i + 1]["start"]
        # 不留空：本条的结束直接接到下一条开始
        else:
            cues[i]["end"] = cues[i + 1]["start"]
        if cues[i]["end"] <= cues[i]["start"]:
            cues[i]["end"] = cues[i]["start"] + 0.2
    cues[-1]["end"] = max(cues[-1]["end"], total)
    return cues


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


def build_html(scenes, bounds, audio_rel, total, width, height, cues=None, media_url=None, theme=None, gsap_src="assets/vendor/gsap.min.js"):
    theme = theme or resolve_theme()
    starts = [0.0] + bounds
    ends = bounds + [total]
    sections, tl = [], []

    for i, sc in enumerate(scenes):
        s, e = starts[i], ends[i]
        sid = f"s{i+1}"
        kind = sc.get("type", "title")

        if kind == "title":
            body = render_block("title", i=i,
                                kicker=esc(sc.get("kicker", "")),
                                title=esc(sc.get("title", "")),
                                sub=esc(sc.get("sub", "")))
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
            body = render_block("list", items=items)
            gap = max(e - s - 1.0, 0.6) / max(len(rows), 1)
            for j in range(len(rows)):
                tl.append(f'      tl.from("#r{i}_{j}", {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, {s + 0.2 + j * gap:.2f})')
            tl.append(f'        .to("#s{i+1} .rows", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.45):.2f});')

        elif kind == "quote":
            body = render_block("quote", i=i, text=esc(sc.get("text", "")))
            tl.append(f'      tl.from("#q{i}", {{ opacity: 0, y: 30, duration: 0.6, ease: "power2.out" }}, {s+0.2:.2f})')
            tl.append(f'        .to("#q{i}", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.45):.2f});')

        elif kind == "image":
            if not media_url:
                raise SystemExit(f"第 {i+1} 个镜头用了 image，但没有素材库")
            url = media_url(sc.get("src", ""))
            cap = esc(sc.get("caption", ""))
            caption_block = (f'          <div id="cap{i}" class="figcap">{cap}</div>'
                             if cap else "")
            body = render_block("image", i=i, src=url, caption=caption_block)
            tl.append(f'      tl.fromTo("#fig{i}", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }}, {s+0.15:.2f})')
            if cap:
                tl.append(f'        .from("#cap{i}", {{ opacity: 0, duration: 0.45, ease: "power2.out" }}, {s+0.55:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {max(s+0.3, e-0.4):.2f});')

        elif kind == "editorial":
            body, anim, counters = render_ppt(sc.get("blocks", []), i)
            body = f'        <div class="ppt">\n{body}\n        </div>'
            for bid, j in anim:
                tl.append(f'      tl.from("#{bid}", {{ opacity: 0, y: 26, duration: 0.5, ease: "power2.out" }}, {s + 0.2 + j * 0.35:.2f})')
            for cid, val in counters:
                tl.append(f'        .to("#{cid}", {{ innerText: {val:g}, snap: {{ innerText: 1 }}, duration: 0.9, ease: "power2.out" }}, {s + 0.6:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {max(s + 0.4, e - 0.45):.2f});')

        elif kind == "ink":
            body = render_ink(sc, i)
            acc = "#a63a2e"
            tl.append(f'      tl.from("#ink{i}-m2", {{ opacity: 0, y: 30, duration: 0.9, ease: "power2.out" }}, {s+0.1:.2f})')
            tl.append(f'        .from("#ink{i}-m1", {{ opacity: 0, y: 40, duration: 1.0, ease: "power2.out" }}, {s+0.25:.2f})')
            tl.append(f'        .from("#ink{i}-m3", {{ opacity: 0, y: 24, duration: 0.9, ease: "power2.out" }}, {s+0.45:.2f})')
            tl.append(f'        .from("#ink{i}-mist1", {{ opacity: 0, scale: 0.9, duration: 1.0, ease: "sine.out" }}, {s+0.6:.2f})')
            tl.append(f'        .from("#ink{i}-mist2", {{ opacity: 0, scale: 0.9, duration: 1.0, ease: "sine.out" }}, {s+0.7:.2f})')
            tl.append(f'        .from("#ink{i}-sun", {{ opacity: 0, scale: 0.6, transformOrigin: "center", duration: 0.8, ease: "power2.out" }}, {s+0.5:.2f})')
            tl.append(f'        .from("#ink{i}-text", {{ opacity: 0, y: 26, duration: 0.8, ease: "power2.out" }}, {s+0.9:.2f})')
            tl.append(f'        .from("#ink{i}-seal", {{ opacity: 0, scale: 1.8, rotate: -18, duration: 0.35, ease: "back.out(2)" }}, {s+1.4:.2f})')
            tl.append(f'        .fromTo("#ink{i} svg", {{ scale: 1 }}, {{ scale: 1.05, duration: {max(e-s,1.0):.2f}, ease: "none" }}, {s:.2f})')
            tl.append(f'        .fromTo("#ink{i}-mist1", {{ x: -30 }}, {{ x: 30, duration: {max(e-s,1.0):.2f}, ease: "sine.inOut" }}, {s:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.5, ease: "power2.in" }}, {max(s+0.6, e-0.6):.2f});')

        elif kind == "chart":
            body, bars = render_chart(sc, i)
            for j, (bid, val) in enumerate(bars):
                t0 = s + 0.35 + j * 0.28
                tl.append(f'      tl.fromTo("#{bid}", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.55, ease: "power3.out" }}, {t0:.2f})')
                tl.append(f'        .to("#{bid}-n", {{ innerText: {val:g}, snap: {{ innerText: 1 }}, duration: 0.7, ease: "power2.out" }}, {t0+0.15:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {max(s+0.5, e-0.5):.2f});')

        elif kind == "code":
            body, lines = render_code(sc, i)
            tl.append(f'      tl.from("#code{i}-win", {{ opacity: 0, scale: 0.96, duration: 0.5, ease: "power2.out" }}, {s+0.15:.2f})')
            for j, lid in enumerate(lines):
                tl.append(f'        .from("#{lid}", {{ opacity: 0, x: -14, duration: 0.22, ease: "power2.out" }}, {s+0.55+j*0.22:.2f})')
            tl.append(f'        .to("#code{i}-caret", {{ opacity: 0, duration: 0.32, repeat: 8, yoyo: true, ease: "none" }}, {s+0.8:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {max(s+0.5, e-0.5):.2f});')

        elif kind == "wave":
            body, bars = render_wave(sc, i)
            tl.append(f'      tl.from(".wave-title", {{ opacity: 0, y: 20, duration: 0.5, ease: "power2.out" }}, {s+0.15:.2f})')
            tl.append(f'        .from(".wave-sub", {{ opacity: 0, duration: 0.5 }}, {s+0.3:.2f})')
            for j, bid in enumerate(bars):
                amp = 0.55 + 0.45 * ((j * 37 % 11) / 10)
                tl.append(f'        .fromTo("#{bid}", {{ scaleY: 0.45 }}, {{ scaleY: {amp:.2f}, duration: 0.26, repeat: 18, yoyo: true, ease: "sine.inOut" }}, {s+0.25+j*0.012:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {max(s+0.5, e-0.5):.2f});')

        elif kind == "block":
            src = sc.get("src", "")
            if not (ROOT / src).exists():
                raise SystemExit(f"组件不存在：{src}")
            body = (f'        <template data-composition-src="{src}"\n'
                    f'                  data-start="0" data-duration="{e - s:.2f}"></template>')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {max(s+0.4, e-0.4):.2f});')

        elif kind == "video":
            if not media_url:
                raise SystemExit(f"第 {i+1} 个镜头用了 video，但没有素材库")
            url = media_url(sc.get("src", ""))
            dur = e - s
            body = render_block("video", i=i, src=url, dur=f"{dur:.2f}")
            tl.append(f'      tl.fromTo("#vid{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, {s+0.1:.2f})')
            tl.append(f'        .to("#s{i+1}", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {max(s+0.3, e-0.35):.2f});')

        else:
            title = sc.get("title", "")
            accent = sc.get("accent", "")
            if accent and accent in title:
                title = title.replace(accent, f'<span class="accent">{esc(accent)}</span>', 1)
            else:
                title = esc(title)
            body = render_block("ending", i=i, title=title, sub=esc(sc.get("sub", "")))
            tl.append(f'      tl.fromTo("#t{i}", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.65, ease: "power3.out" }}, {s+0.2:.2f})')
            tl.append(f'        .from("#sub{i}", {{ opacity: 0, duration: 0.5, ease: "power2.out" }}, {s+0.7:.2f})')
            tl.append(f'        .to("#t{i}", {{ scale: 1.03, duration: {max(e - s - 1.0, 0.6):.2f}, ease: "none" }}, {s+1.0:.2f});')

        sections.append(
            f'      <section id="{sid}" class="clip" data-start="{s:.2f}" data-duration="{e-s:.2f}">\n'
            f'{body}\n      </section>')

    css = CSS % {
        "W": width, "H": height, "FONT": DEFAULT_FONT,
        "BG": theme["bg"], "INK": theme["ink"], "MUTED": theme["muted"],
        "ACCENT": theme["accent"], "SUB_BG": theme["sub_bg"],
        "GLOW": _rgba(theme["accent"], 0.10),
    }
    sub_layer = subs_html(cues, total) if cues else ""
    sub_js = "\n".join(subs_timeline(cues)) if cues else ""
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <script src="{gsap_src}"></script>
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

    # project.json 提供默认值，命令行参数优先
    proj = {}
    pj = d / "project.json"
    if pj.exists():
        try:
            proj = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            proj = {}

    def pick(*vals, default=None):
        for v in vals:
            if v not in (None, "", []):
                return v
        return default

    voice = pick(args.voice, cfg.get("voice"), proj.get("voice"), default="zh-CN-XiaoxiaoNeural")
    rate = pick(args.rate, cfg.get("rate"), proj.get("rate"), default="+0%")
    engine = pick(args.engine, cfg.get("engine"), proj.get("engine"), default="edge")
    pack = pick(args.voice_pack, cfg.get("voice_pack"), proj.get("voice_pack"))
    theme_name = pick(args.theme, cfg.get("theme"), proj.get("theme"), default=DEFAULT_THEME)
    theme = resolve_theme(theme_name, proj.get("theme_overrides"))
    width = args.width or proj.get("width") or 1920
    height = args.height or proj.get("height") or 1080

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

    html_path = d / "build" / "index.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    base = html_path.parent

    def rel_url(p: Path) -> str:
        return quote(os.path.relpath(p, base).replace("\\", "/"))

    rel = rel_url(audio)

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
        return rel_url(p)

    gsap_src = rel_url(ROOT / "assets" / "vendor" / "gsap.min.js")

    if args.subtitles and not transcript:
        raise SystemExit(
            "开了字幕但没有转写文件 build/transcript.json。\n"
            "  先跑：python tools\\transcribe.py " + slug + "\n"
            "  或渲染时加 --transcribe 自动转写"
        )

    cues = build_cues(script, transcript) if (args.subtitles and transcript) else None
    if cues:
        cues = fill_cues(cues, total)

    html_path.write_text(
        build_html(scenes, bounds, rel, total, width, height, cues, media_url, theme, gsap_src),
        encoding="utf-8")
    print(f"[3/4] build/index.html  {len(scenes)} 个镜头"
          + (f" + {len(cues)} 条字幕（全程覆盖）" if cues else "")
          + f"  主题 {theme_name}")

    if args.render:
        npx = shutil.which("npx") or "npx.cmd"
        # hyperframes check 只认项目根目录的 index.html；画面文件在 build/ 时跳过
        if (ROOT / "index.html").exists():
            subprocess.run([npx, "--yes", "hyperframes@0.9.0", "check", "."], cwd=ROOT)
        else:
            print("      （跳过 hyperframes check：画面文件在 build/，check 只支持根目录）")
        out = d / "output" / "render.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        comp = html_path.relative_to(ROOT).as_posix()
        subprocess.run([npx, "--yes", "hyperframes@0.9.0", "render", ".",
                        "-c", comp, "-o", str(out), "-q", args.quality, "-w", "2"], cwd=ROOT)
        print(f"[4/4] 成片 -> videos/{slug}/output/render.mp4")
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
    ap.add_argument("--theme", help="主题预设：dark-teal / warm-paper / news-red / mono-ink")
    ap.add_argument("--transcribe", action="store_true",
                    help="先用 FunASR 转写，时间轴按句子边界对齐（需要 indextts 环境）")
    ap.add_argument("--subtitles", action="store_true",
                    help="用转写结果生成底部字幕轨（需要 transcript.json）")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--quality", choices=["draft", "looks", "delivery"], default="draft",
                    help="渲染画质：draft 快 / looks 默认 / delivery 最好")
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
