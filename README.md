# AI-v · 短视频生成工程

**当前版本 v2.0.0**（六阶段流水线）：见 [CHANGELOG.md](CHANGELOG.md)

用**文字**生成短视频：写一段文案 + 几个画面描述，自动配音、自动排版、自动渲染成 MP4。
全程本机运行，不依赖任何付费 API。

```
文案 → 配音 → 时间轴 → 画面(HTML) → Chrome 逐帧截图 → MP4
```

---

# 新人上手：3 步（安装 + 出第一条片）

## 1. 下载项目

```powershell
git clone https://github.com/moshiqiqian/ai_video.git
cd ai_video
```

没有 Git 的话，直接在 GitHub 页面点 **Code → Download ZIP** 解压。

## 2. 用 OpenCode 打开这个文件夹，说一句话

```powershell
cd ai_video
opencode
```

然后输入：

```
读 README.md，按里面的步骤把项目装好，装完跑 doctor 验证。
```

**接下来的事它会自己做，你不用敲命令：**

```
读 README.md → 读 INSTALL.md
  → 把 skills/ 复制到 ~/.config/opencode/skills/（注册 8 个技能）
  → 检查 Node / FFmpeg / conda
  → 建两个 conda 环境、装 CUDA torch、装 IndexTTS2、装 FunASR
  → 下载模型（5.5 GB）
  → 跑 doctor 验收
  → 渲一条验证片
```

**预计 30–60 分钟**，主要花在下载。期间它可能会问你磁盘空间之类的问题。

安装脚本会做十步：检查基础软件（含 Chrome）→ 建两个 conda 环境 → 装 CUDA torch → 装 IndexTTS2 → 装 FunASR → 修 protobuf → 下模型 → 预热 HyperFrames（约 100 MB）→ 检查本地 GSAP → 体检。

安装完成后它会汇报：8 个 skill 是否注册、两个环境是否就绪、doctor 是否 22/22、验证片是否渲染成功。

> 不需要提前手动复制 skill。INSTALL.md 的第 0 步就是让 AI 完成注册。

## 3. 装完就直接说需求

在同一个 OpenCode 会话里直接说：

```
用这篇文章做一条 45 秒的视频：D:\文章\降息.md
```

或者没有文稿：

```
做一条 30 秒的视频，主题是「降息对普通人的影响」，用新闻红的配色。
```

它会按六个阶段推进，**每步停下来让你确认**：

```
① 立项   导入文稿、体检字数 → 问你压缩比例
② 文案   给出全文和字数 → 等你改
③ 分镜   给你表格 → 等你确认
④ 素材   问你有没有图（可跳过）
⑤ 配音   生成后让你听
⑥ 渲染   抽帧 + 出片
```

每一步你只需要回「可以」或「改一下 XX」。

## 如果 AI 没自动用 skill

skill 是按描述自动匹配的，偶尔会漏。直接点名：

```
用 video-pipeline 做一条视频，主题是……
```

或者更硬一点：

```
读 skills/video-pipeline/SKILL.md，按它的流程做一条视频。
```

---

# 为什么这样设计

| 文件 | 给谁看 | 作用 |
|---|---|---|
| `README.md` | 人 | 这是什么、怎么开始 |
| `INSTALL.md` | AI | 安装步骤、验收标准、硬规则 |
| `skills/*/SKILL.md` | AI | 每个阶段怎么做、产出什么、何时停 |

安装指令单独放在 **[INSTALL.md](INSTALL.md)**，不写进 README，避免说明越写越长把关键步骤淹没。

---

## skill 是什么

装好之后你会看到 8 个技能，它们决定了 AI 每一步该做什么：

| Skill | 作用 |
|---|---|
| `video-pipeline` | 总控：读状态、调度阶段、要求确认 |
| `video-brief` | 第 1 步 立项：导入文稿、定参数 |
| `video-script` | 第 2 步 文案 |
| `video-storyboard` | 第 3 步 分镜 |
| `video-assets` | 第 4 步 素材 |
| `video-voice` | 第 5 步 配音 |
| `video-render` | 第 6 步 渲染与质检 |
| `deploy-ai-video` | 部署 / 重建环境 / 排错 |

**这些都由 AI 在安装时自动注册，你不需要手动复制。**

如果某次 AI 没自动加载，直接点名就行：

```
用 video-pipeline 做一条视频，主题是……
```

---

# 手动安装（不走 AI 时）

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
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\doctor.ps1      # 验收，22/22 通过
```

| 脚本 | 作用 |
|---|---|
| `bootstrap.ps1` | 检查基础软件 → 建两个环境 → 装 CUDA torch → 装 IndexTTS2 → 装 FunASR → 修 protobuf → 下模型 → 自动体检 |
| `doctor.ps1` | 只读检查 22 项，逐项 PASS/FAIL，失败项附修复命令 |

环境快照在 `env\aivideo.yml`、`env\indextts.yml`。YAML 装不了 CUDA torch 和本地包，手动步骤见 `skills\deploy-ai-video\references\install.md`。

---

# 日常使用

## 让 AI 做

```
把 LangChain全家桶 的第 3 屏拆成两个镜头，每屏最多 2 行。
```

```
把 D:\图\架构图.png 加进 LangChain全家桶 的素材库，名字叫「架构图」。
```

```
把 D:\录音\我的声音.m4a 加进声音库，名字叫「我自己」，截 2-8 秒。
```

```
换成新闻红的配色。
```

## 自己做

```powershell
conda activate aivideo
cd AI-v

# 第 1 步：立项（有文稿就带上）
python tools\stage.py brief 我的视频 --from D:\文章.md --duration 45 --theme news-red
# 看 build/brief.md 后确认
python tools\stage.py confirm 我的视频 brief

# 第 2 步：文案（改完 script.txt 再跑）
python tools\stage.py script 我的视频
python tools\stage.py confirm 我的视频 script

# 第 3–6 步
python tools\stage.py storyboard 我的视频
python tools\stage.py confirm 我的视频 storyboard
python tools\stage.py assets 我的视频          # 没素材会自动跳过
python tools\stage.py voice 我的视频
python tools\stage.py confirm 我的视频 voice
python tools\stage.py render 我的视频 --quality delivery

# 随时查看进度
python tools\stage.py status 我的视频
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
│   └── 玻尔兹曼机\
│       ├── source\         你放素材的地方
│       │   ├── articles\   文稿 md/txt
│       │   ├── images\     图片
│       │   └── clips\      视频片段
│       ├── script.txt      旁白
│       ├── scenes.json     画面
│       ├── build\          中间态（brief/script/storyboard/transcript/voice/render）
│       ├── audio\          配音
│       ├── qa\             抽帧
│       └── output\render.mp4
│
├── voices\                 声音库（可复用音色）
│   └── xiaoxiao\sample.wav
│
├── assets\vendor\          gsap.min.js（本地，不依赖 CDN）
│
├── tools\
│   ├── stage.py            阶段调度：brief/script/storyboard/assets/voice/render
│   ├── make.py             底层构建器（stage.py 会调用它）
│   ├── tts_edge.py         微软音色配音
│   ├── say.py              用声音库音色配音
│   ├── voice.py            声音库管理
│   ├── media.py            素材库管理
│   └── transcribe.py       转写 + 词级时间戳
│
├── skills\                 给 Agent 的操作技能（可扩展）
│   ├── video-pipeline\     总控：状态判断与调度
│   ├── video-brief\        第 1 步 立项（支持导入 md）
│   ├── video-script\       第 2 步 文案
│   ├── video-storyboard\   第 3 步 分镜
│   ├── video-assets\       第 4 步 素材
│   ├── video-voice\        第 5 步 配音
│   ├── video-render\       第 6 步 渲染与质检
│   └── deploy-ai-video\    部署 / 重建环境
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

`make.py` 读这两个文件，产出 `audio\vo_*.wav`、`build/index.html`、`output/render.mp4`。

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

`start_at_sentence` 指「第几句开始时切过来」，句子编号来自 `tranbuild/script.json`。比手写秒数可靠：重新生成音频后句子编号不变。

## 常用命令

```powershell
# 六阶段流水线（推荐）
python tools\stage.py brief      视频名 --from D:\文章.md --duration 45 --theme news-red
python tools\stage.py script     视频名
python tools\stage.py storyboard 视频名
python tools\stage.py assets     视频名
python tools\stage.py voice      视频名
python tools\stage.py render     视频名 --quality delivery

python tools\stage.py confirm 视频名 <阶段>   # 记录人工确认
python tools\stage.py status  视频名          # 看进度
python tools\stage.py next    视频名          # 下一步做什么

# 素材与音色
python tools\media.py add 视频名 D:\图.png --name 架构图
python tools\voice.py add 我的声音 录音.m4a --start 2 --dur 8

# 预览某一支（画面文件在 build/index.html）
npx hyperframes@0.9.0 preview . -c videos/视频名/build/index.html

# 单文件直出（跳过阶段，适合快速改画面）
python tools\make.py 视频名 --reuse-audio --subtitles --render
```

主题预设：`dark-teal`（默认）/ `warm-paper` / `news-red` / `mono-ink`。

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

- `CHANGELOG.md` — 版本变更
- `INSTALL.md` — 交给 AI 的安装指令
- `skills\video-pipeline\SKILL.md` — 六阶段总控
- `skills\video-brief\references\import.md` — 文稿导入规则
- `skills\video-script\references\copywriting.md` — 文案结构
- `skills\video-storyboard\references\build/storyboard.md` — 分镜规则
- `skills\video-voice\references\voices.md` — 音色选择
- `skills\video-render\references\qa.md` — 质检清单
- `skills\deploy-ai-video\references\install.md` — 手动安装
- `docs\RUNBOOK.md` — 日常操作
- `docs\WORKFLOW.md` — 设计说明
