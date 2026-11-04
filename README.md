# AI-v · 短视频生成工程

用**文字**生成短视频：写一段文案 + 几个画面描述，自动配音、自动排版、自动渲染成 MP4。
全程本机运行，不依赖任何付费 API。

```
文案 → 配音 → 时间轴 → 画面(HTML) → Chrome 逐帧截图 → MP4
```

---

# 怎么用：把项目交给 AI

不需要自己敲命令。打开 Codex / OpenCode / Claude Code / Cursor，把下面这段复制给它：

```
请阅读当前项目根目录的 INSTALL.md，按里面的步骤在本机安装这个项目。
装完跑 doctor 验证，把结果告诉我。
```

AI 会自己读文档、装环境、下模型、验证。你只需要在它提问时回答（比如确认磁盘空间）。

安装指令单独放在 **[INSTALL.md](INSTALL.md)**，与这份 README 分开，避免说明越写越长、把安装步骤淹没。

---

# 安装

完整指令见 **[INSTALL.md](INSTALL.md)**。这里是摘要。

前置软件：

| 软件 | 用途 | 安装 |
|---|---|---|
| Miniconda | Python 环境 | 官网下载 |
| Node.js 18+ | HyperFrames 渲染 | `winget install OpenJS.NodeJS.LTS` |
| FFmpeg | 音频测量、封装 | `winget install Gyan.FFmpeg` |
| Chrome | 渲染引擎 | 系统自带或官网 |

两条命令：

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\bootstrap.ps1   # 装，30-60 分钟
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\doctor.ps1      # 验收，20/20 通过
```

| 脚本 | 作用 |
|---|---|
| `bootstrap.ps1` | 检查基础软件 → 建两个环境 → 装 CUDA torch → 装 IndexTTS2 → 装 FunASR → 修 protobuf → 下模型 → 自动体检 |
| `doctor.ps1` | 只读检查 20 项，逐项 PASS/FAIL，失败项附修复命令 |

环境快照在 `env\aivideo.yml`、`env\indextts.yml`。YAML 装不了 CUDA torch 和本地包，手动步骤见 `skills\deploy-ai-video\references\install.md`。

---

# 装完之后怎么出片

## 让 AI 做

```
做一条 60 秒的时评视频，主题是「AI 编程工具会不会取代初级程序员」，
用 xiaoxiao 音色，带字幕，横屏 1080p。
```

```
把 LangChain全家桶 的第 3 屏拆成两个镜头，每屏最多 2 行。
```

```
把 D:\图\架构图.png 加进 LangChain全家桶 的素材库，名字叫「架构图」。
```

```
把 D:\录音\我的声音.m4a 加进声音库，名字叫「我自己」，截 2-8 秒。
```

## 自己做

```powershell
conda activate aivideo
cd AI-v

python tools\make.py new 我的视频
# 改 videos\我的视频\script.txt 和 scenes.json
python tools\make.py 我的视频 --render
```

---

## 它能做什么

| 能力 | 说明 |
|---|---|
| 文字转语音 | 微软神经语音（8 种中文音色）或 IndexTTS2 克隆任意音色 |
| 自动时间轴 | 从音频里测出句子边界，画面按句子切 |
| 字幕 | 逐句字幕，时间来自 ASR 逐字对齐 |
| 画面 | 标题、清单、金句、图片、视频、结尾 |
| 渲染 | 浏览器逐帧截图，输出确定性视频 |

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
│   ├── video.py            工程管理：init / theme / check / preview / render
│   ├── make.py             底层的构建器（video.py 会调用它）
│   ├── tts_edge.py         微软音色配音
│   ├── say.py              用声音库音色配音
│   ├── voice.py            声音库管理
│   ├── media.py            素材库管理
│   └── transcribe.py       转写 + 词级时间戳
│
├── skills\                 给 Agent 的操作技能（可扩展）
│   ├── deploy-ai-video\    部署 / 重建环境
│   └── make-video\         做视频的七阶段流程
│       ├── SKILL.md        部署入口
│       ├── references\     install / troubleshooting
│       └── scripts\        bootstrap.ps1 / doctor.ps1
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

`start_at_sentence` 指「第几句开始时切过来」，句子编号来自 `transcript.json`。比手写秒数可靠：重新生成音频后句子编号不变。

## 常用命令

```powershell
# 工程化流程（推荐）
python tools\video.py init 视频名 --theme warm-paper --duration 45
python tools\video.py check 视频名
python tools\video.py preview 视频名 --at 3,12,25
python tools\video.py render 视频名 --quality delivery
python tools\video.py status 视频名
python tools\video.py list

# 底层命令（video.py 内部调用的就是这些）
python tools\make.py 视频名 --render
python tools\make.py 视频名 --reuse-audio --subtitles --render
python tools\media.py add 视频名 D:\图.png --name 架构图
python tools\voice.py add 我的声音 录音.m4a --start 2 --dur 8
```

主题预设：`dark-teal`（默认）/ `warm-paper` / `news-red` / `mono-ink`，用
`python tools\video.py theme 视频名 --set warm-paper` 切换。

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
- 无真人素材剪辑
- 中文字体依赖系统（Linux 需装 `fonts-noto-cjk`）

## 文档

- `INSTALL.md` — 交给 AI 的安装指令
- `skills\deploy-ai-video\SKILL.md` — 部署技能入口
- `skills\deploy-ai-video\references\install.md` — 手动安装详解
- `skills\deploy-ai-video\references\troubleshooting.md` — 排错
- `docs\RUNBOOK.md` — 日常操作手册
- `docs\WORKFLOW.md` — 工作流设计说明
