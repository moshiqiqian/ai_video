# AI-v · 短视频生成工程

用**文字**生成短视频：写一段文案 + 几个画面描述，自动配音、自动排版、自动渲染成 MP4。

全程本机运行，不依赖任何付费 API。

```
文案 → 配音 → 时间轴 → 画面(HTML) → Chrome 逐帧截图 → MP4
```

## 效果

一条 51 秒的技术科普视频，从文案到成片约 10 分钟（其中 7 分钟是本地 AI 配音）。

成片规格：1920×1080 / 30fps / H.264 + AAC，带底部字幕。

## 它能做什么

| 能力 | 说明 |
|---|---|
| 文字转语音 | 微软神经语音（8 种中文音色）或 IndexTTS2 克隆任意音色 |
| 自动时间轴 | 从音频里测出句子边界，画面按句子切 |
| 字幕 | 逐句字幕，时间来自 ASR 逐字对齐 |
| 画面 | 标题、清单、金句、结尾；可插图片和视频 |
| 渲染 | 浏览器逐帧截图，输出确定性视频 |

## 快速开始

已装好的机器上，三条命令：

```powershell
conda activate aivideo
cd AI-v
python tools\make.py new 我的视频
```

改 `videos\我的视频\script.txt`（文案）和 `scenes.json`（画面），然后：

```powershell
python tools\make.py 我的视频 --render
```

成片：`videos\我的视频\render.mp4`

## 部署到新机器

完整步骤、环境快照、排错手册都在 Skill 里：

```
skills\deploy-ai-video\
├── SKILL.md              部署流程（Agent 入口）
├── references\install.md 手动安装详解
├── references\troubleshooting.md
└── scripts\bootstrap.ps1 一键安装
```

一条命令安装（会建环境、装依赖、下模型、体检）：

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\bootstrap.ps1
```

### 前置软件

| 软件 | 版本 | 检查 |
|---|---|---|
| Miniconda | 任意较新版 | `conda --version` |
| Node.js | 18+ | `node -v` |
| FFmpeg | 任意新版 | `ffmpeg -version` |
| Chrome | 任意新版 | 渲染引擎 |

### 两个 Python 环境

| 环境 | Python | 大小 | 装什么 |
|---|---|---|---|
| `aivideo` | 3.13 | 0.31 GB | edge-tts（出片） |
| `indextts` | 3.11 | 7.97 GB | torch 2.8+cu126、IndexTTS2、FunASR |

环境快照在 `env\aivideo.yml` 和 `env\indextts.yml`。

### 模型权重

IndexTTS2 需要 10.6 GB 权重，**不在仓库里**。

`bootstrap.ps1` 会自动从 `hf-mirror.com` 下载；也可以从别的机器拷贝 `vendor\index-tts\checkpoints\`。

## 项目结构

```
AI-v\
├── videos\                 每支视频一个文件夹
│   └── LangChain全家桶\
│       ├── script.txt      旁白文案
│       ├── scenes.json     画面 + 音色设置
│       ├── media\          图片/视频素材
│       ├── audio\          配音 + 转写结果
│       └── render.mp4      成片
│
├── voices\                 声音库（可复用音色）
│   └── xiaoxiao\sample.wav
│
├── tools\
│   ├── make.py             出片主程序
│   ├── tts_edge.py         微软音色配音
│   ├── say.py              用声音库音色配音
│   ├── voice.py            声音库管理
│   ├── media.py            素材库管理
│   └── transcribe.py       转写 + 词级时间戳
│
├── skills\                 给 Agent 的操作技能（可扩展）
│   └── deploy-ai-video\
│
├── env\                    环境快照 YAML
├── docs\                   RUNBOOK / WORKFLOW
└── vendor\index-tts\       IndexTTS2 源码 + 模型（不进仓库）
```

## 核心概念

一支视频 = 一个文件夹，里面两个文本文件：

| 文件 | 作用 |
|---|---|
| `script.txt` | 念出来的话 |
| `scenes.json` | 屏幕上出现什么、什么时候出现 |

`make.py` 读这两个文件，产出 `audio\vo_*.wav`、`index.html`、`render.mp4`。

### 画面类型

```json
{ "type": "title",  "title": "标题", "sub": "副标题" }
{ "type": "list",   "rows": ["要点一", "要点二"], "mark": "number" }
{ "type": "quote",  "text": "一句金句" }
{ "type": "image",  "src": "素材名", "caption": "说明" }
{ "type": "video",  "src": "素材名" }
{ "type": "ending", "title": "结尾", "accent": "高亮词" }
```

### 时间对齐

```json
{ "type": "list", "start_at_sentence": 13, "rows": ["..."] }
```

`start_at_sentence` 指“第几句开始时切过来”，句子编号来自 `transcript.json`。

比手写秒数可靠：重新生成音频后句子编号不变。

## 常用命令

```powershell
# 新建视频
python tools\make.py new 视频名

# 出片（微软音色，约 90 秒）
python tools\make.py 视频名 --render

# 出片（克隆音色，约 10 分钟）
python tools\make.py 视频名 --engine indextts --voice-pack xiaoxiao --transcribe --subtitles --render

# 只改画面，不重新配音
python tools\make.py 视频名 --reuse-audio --subtitles --render

# 加素材
python tools\media.py add 视频名 D:\图.png --name 架构图
python tools\media.py list 视频名

# 加音色
python tools\voice.py add 我的声音 录音.m4a --start 2 --dur 8
python tools\voice.py list
```

## 技术栈

| 组件 | 作用 |
|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) | HTML/CSS/GSAP → 逐帧截图 → MP4 |
| [IndexTTS2](https://github.com/index-tts/index-tts) | 零样本音色克隆 TTS |
| [FunASR](https://github.com/modelscope/FunASR) | 中文语音识别 + 时间戳 |
| edge-tts | 微软神经语音（免费、快） |
| FFmpeg | 音频测量、封装 |

## 已知限制

- 渲染慢：51 秒视频约 2.5 分钟（逐帧截图）
- IndexTTS2 更慢：51 秒音频约 7 分钟
- 无 BGM / 音效生成能力
- 无真人素材剪辑（没有 video-use 依赖的 API key）
- 中文字体依赖系统（Linux 需装 `fonts-noto-cjk`）

## 文档

- `docs\RUNBOOK.md` — 日常操作手册
- `docs\WORKFLOW.md` — 工作流设计说明
- `skills\deploy-ai-video\` — 部署与排错
