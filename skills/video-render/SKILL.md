---
name: video-render
description: 视频流水线第 6 步「渲染」。配音确认后使用，或用户说「出片」「渲染」「出个预览」「画质高一点」时使用。负责转写与字幕、构建 index.html、渲染 MP4、抽帧质检。不改文案和分镜。
---

# 第 6 步 · 渲染

把文案、分镜、素材、配音合成 MP4，并做一次质检。

## 输入

- `scenes.json`（分镜）
- `audio/vo.*`（配音）
- `media/`（素材，可能为空）
- `project.json`（主题、尺寸、字幕开关）

## 执行

```powershell
# 先看效果（快，draft 画质）
python tools\stage.py render 视频名 --quality draft

# 发布版
python tools\stage.py render 视频名 --quality delivery

# 需要字幕（会先转写，多 30 秒）
python tools\stage.py render 视频名 --transcribe
```

## 产出

| 文件 | 内容 |
|---|---|
| `index.html` | 画面（在项目根目录，每次重写） |
| `videos/<名字>/render.mp4` | 成片 |
| `videos/<名字>/qa/*.png` | 抽帧 |
| `videos/<名字>/render.json` | 画质、时长、文件大小 |
| `audio/transcript.json` | 转写（只在 `--transcribe` 时生成） |

## 内部做了什么

```
1. 有 --transcribe → 调 FunASR 出词级时间戳
2. 构建 index.html：套主题、算时间轴、生成字幕轨
3. 校验：hyperframes check
4. 渲染：Chrome 逐帧截图 → ffmpeg 合成
5. 抽 3 帧到 qa/
```

## 画质选择

| 参数 | CRF | 速度 | 用途 |
|---|---|---|---|
| `draft` | 高压缩 | 最快 | 改稿迭代 |
| `looks` | 中（默认） | 中 | 日常发布 |
| `delivery` | 低 | 慢 1.5 倍 | 正式交付 |

51 秒视频参考：draft 约 2 分钟，delivery 约 2.5 分钟。

## 执行后要做的

1. 报三个数：时长、文件大小、画质
2. 让用户看成片：

```
start videos/名字/render.mp4
```

3. 给抽帧路径，让用户看切换点：
   `videos/名字/qa/`
4. 等确认：

```powershell
python tools\stage.py confirm 视频名 render
```

## 质检清单

| 项 | 怎么查 |
|---|---|
| 有声音 | 播放 |
| 画面切换和语音对得上 | 看 2–3 个切换点 |
| 首帧有内容 | `qa/` 里第一张 |
| 结尾无黑屏 | 最后一帧 |
| 字幕不超框 | 抽帧看底部 |
| 中文字体正常 | 没有方块 |

发现问题：改对应阶段（文案/分镜/素材/配音）→ 系统会标 stale → 重跑下游。

## 常见错误

| 报错 | 原因 | 修法 |
|---|---|---|
| `还没有配音` | 没跑 voice | 先配音 |
| `上游「配音」还没确认` | 没 confirm | 先确认 |
| 画面全黑 | GSAP CDN 不通 | 本地化 gsap.min.js |
| 中文是方块 | 缺字体 | Windows 自带；Linux 装 noto-cjk |
| 渲染 OOM | 多 worker 抢内存 | 加 `-w 1` |
| 字幕压住图片说明 | 版面重叠 | 图片区已有 150px 留白，检查是否被改 |

## 重渲

只改画面或主题时，配音不用重做：

```powershell
python tools\stage.py render 视频名 --quality draft
```

命令内部会复用已有音频，不会重新配音。

## 参考

- `references/qa.md` — 质检清单与抽帧方法
