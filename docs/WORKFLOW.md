# AI 视频工作流 · 本机适配版

> 基于《AI 视频剪辑工作流｜从素材到成片》重写。
> 原文档假设：macOS + 有真人口播素材 + 有 ElevenLabs key + 全套 Skill。
> 本机实际：Windows 11 + 无素材 + 无 API key + HyperFrames/Remotion 已装 + edge-tts 云端配音。

---

## 环境（必读）

本项目的 Python 依赖**全部隔离在 conda 环境 `aivideo`**，base 里没有。

```powershell
conda activate aivideo
cd C:\Users\bb313\Desktop\AI-v
python tools\tts_edge.py
```

| 项 | 值 |
|---|---|
| 环境名 | `aivideo` |
| 解释器 | `C:\Users\bb313\anaconda3\envs\aivideo\python.exe` |
| Python | 3.13.18 |
| 占用 | 4.79 GB |
| 含 | torch 2.6.0+cu124（GPU 可用）、edge-tts、soundfile |
| VS Code | 已在 `.vscode/settings.json` 指定解释器，打开项目自动选中 |

没激活环境就运行 `python tools\tts_edge.py` 会报 `ModuleNotFoundError`，这是正常的，不是装坏了。

---

## 0. 先看结论

| 路线 | 前提 | 今天能不能跑 |
|---|---|---|
| **A · 全生成**（edge-tts 配音 + HyperFrames 画面） | 只要一段文案 | ✅ 现在就能出片 |
| **B · 真人素材剪辑**（原作者的流程） | 有 A-roll + ElevenLabs key | ⚠️ 缺 3 样，补齐约 1 小时 |
| **C · 云端渲染 / Lambda** | Docker | ❌ 本机无 Docker，跳过 |

**建议：先跑 A 把链路走通，再补 B。**

---

## 1. 本机 vs 原文差异表

| 环节 | 原文做法 | 本机实际 | 处理方式 |
|---|---|---|---|
| 系统 | macOS + brew | Windows 11 | 命令改成 PowerShell；不装 brew |
| FFmpeg | `brew install ffmpeg` | ✅ 已有 9.0.2（WinGet） | 直接用 |
| Whisper | `pip install openai-whisper`（要拖 2.5GB torch） | ❌ 未装 | 用 `hyperframes transcribe`，但 **Windows 无预编译自动安装**，运行时和模型都要手动放（见 B2） |
| 转写 key | ElevenLabs Scribe | ❌ 无 | video-use 的 `transcribe.py` **硬依赖** `ELEVENLABS_API_KEY`，无本地降级 |
| video-use 粗剪 | 主力工具 | ⚠️ 文件在，但转写不通 | 补 key 才能用；否则用默认剪辑 |
| Remotion | Agent Skills | ✅ 5 个 remotion skill 已装，但无工程 | 需要 `npx create-video` 建工程 |
| video-shotcraft | 动效库 + Motion Workbench | ❌ 未装 | `npx skills add Vincentwei1021/video-shotcraft` |
| 配音 | 真人录音 | ✅ Kokoro v1.1-zh 本地 | 无麦克风也能做「口播」 |
| 渲染 | 本地/云 | ✅ 本地 Chrome + FFmpeg | 无 Docker，只能本地 |
| 内存 | 未提 | 总 15.7GB，空闲实测 6.3GB（commit 17GB，走页面文件） | 默认 worker 2–4 即可，**不需要**强制 `--low-memory-mode` |
| 中文断句 | Whisper | ⚠️ whisper 中文一般 | 可选剪映导出 SRT 回灌 |

---

## 2. 能力盘点（实测）

### 已就绪

```
Node v22.14.0        npm 10.9.2        Python 3.13.5 (Anaconda)
FFmpeg / FFprobe 9.0.2                 Chrome（系统已装）
HyperFrames CLI 0.9.0                 工程：C:\Users\bb313\Desktop\AI-v
Kokoro 已移除（音质不达标）     edge-tts 7.3.1（微软晓晓等中文音色）
42 个 Agent Skill                 备选：IndexTTS2（vendor/index-tts，环境中 indextts）
```

### 缺失

| 缺什么 | 影响 | 补法 |
|---|---|---|
| `video-shotcraft` | 没有动效库和 Motion Workbench | `npx skills add Vincentwei1021/video-shotcraft` |
| `ELEVENLABS_API_KEY` | video-use 无法转写 | 申请 key，写进 `video-use/.env` |
| Remotion 工程 | remotion skill 只能读不能跑 | `npx create-video@latest` |
| Docker | 云端渲染/确定性渲染不可用 | 非必需，跳过 |

---

## 3. 路线 A：全生成（今天可用）

**产物**：`out/final/final.mp4` + 可编辑 `index.html`
**耗时**：首条 30–40 分钟，之后 10 分钟

### A1 · 文案

`content\script.txt`（UTF-8，一行到底，用逗号句号控制停顿）

### A2 · 配音

```powershell
cd C:\Users\bb313\Desktop\AI-v
mkdir assets -Force
python tools\tts_edge.py
```

`tools\tts_edge.py`：

```python
import asyncio, subprocess
import edge_tts

VOICE = "zh-CN-XiaoxiaoNeural"   # 晓晓；男声用 zh-CN-YunyangNeural
RATE = "+0%"

async def main():
    text = open("script.txt", encoding="utf-8").read().strip()
    await edge_tts.Communicate(text, VOICE, rate=RATE).save("videos/<名字>/audio/vo.mp3")
    print(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0","videos/<名字>/audio/vo.mp3"], capture_output=True, text=True).stdout)

asyncio.run(main())
```

**产出**：`videos/<名字>/audio/vo.mp3` + 秒数（后面所有时间轴以它为准）

可用中文音色：

| 音色 ID | 性别 | 风格 |
|---|---|---|
| `zh-CN-XiaoxiaoNeural` | 女 | 温暖自然（默认） |
| `zh-CN-XiaoyiNeural` | 女 | 活泼 |
| `zh-CN-YunyangNeural` | 男 | 新闻播报 |
| `zh-CN-YunxiNeural` | 男 | 阳光 |
| `zh-CN-YunjianNeural` | 男 | 激情解说 |

### A2-b · 想要「自己的声音」→ IndexTTS2

edge-tts 只能选现成音色。要克隆某个人的声音（含你自己的），用 IndexTTS2。

```powershell
conda activate indextts
cd C:\Users\bb313\Desktop\AI-v
python tools\tts_indextts.py                                  # 默认参考 videos/<名字>/audio/ref.wav
python tools\tts_indextts.py --ref videos/<名字>/audio/my_voice.wav        # 换成你自己的录音
```

要求：参考音频 3–15 秒、单人、无背景音、不爆音。录完直接丢进 `videos\<名字>\audio\`。

| 项 | 数值 |
|---|---|
| 模型 | 5.49 GB（`vendor/index-tts/checkpoints`） |
| 显存 | 4–6 GB（本机 8GB 够） |
| 速度 | 14 秒音频约 2 分钟（RTF 9.2） |
| 首次加载 | 20–30 秒 |

时间轴注意：**IndexTTS2 每次生成的长度都不一样**，换音色后必须按新 wav 的实际时长重算 `data-start`。最稳的做法是一句一个 wav 再拼接（见 `tts_indextts.py` 可扩展）。

### A3 · 分镜表（跳过也行，但建议）

新建 `storyboard.md`，每 3–5 秒一个镜头：

```
0.0–4.0   标题「第一条视频」
4.0–9.0   说明文字
9.0–14.0  结尾金句
```

### A4 · 写画面

改 `index.html`：`#root` 的 `data-duration` 和 `<audio data-duration>` 必须等于 A2 秒数。

### A5 · 关键帧预览（原文档强调的一步，保留）

```powershell
npm run dev
```

浏览器里拖到 6 个时间点看：开场 / 口播段 / 重点文字 / 转场 / 结尾。**不好看就别急着渲染。**

### A6 · 检查

```powershell
npm run check
```

### A7 · 渲染

```powershell
npx hyperframes render . -o out/preview/preview.mp4 -q draft
npx hyperframes render . -o out/final/final.mp4
```

### A8 · QA

```powershell
mkdir qa -Force
ffmpeg -ss 2  -i out\final\final.mp4 -frames:v 1 qa\f01.png -y
ffmpeg -ss 6  -i out\final\final.mp4 -frames:v 1 qa\f02.png -y
ffmpeg -ss 12 -i out\final\final.mp4 -frames:v 1 qa\f03.png -y
```

检查：有没有声音、结尾有没有黑屏、中文有没有方块、字号手机能不能看清。**发现问题改 → 重渲染 → 再查，最多 3 轮。**

---

## 4. 路线 B：真人素材（原作者流程）

### 目录

```
project/
├── script.md
├── A-roll/          ← 真人素材
├── B-roll/          ← 录屏/截图/产品
├── images/
├── assets/          ← 生成物：配音、gsap、字体
├── analysis/        ← transcript.md / storyboard.md
└── out/
    ├── preview/
    ├── final/
    └── qa/
```

### B0 · 补齐依赖（一次性）

```powershell
# 1. 动效库
npx skills add Vincentwei1021/video-shotcraft

# 2. video-use 的依赖
cd C:\Users\bb313\.config\opencode\skills\video-use
python -m pip install requests librosa matplotlib pillow numpy
# 3. 把 ELEVENLABS_API_KEY=xxx 写进 .env
```

### B1 · 分镜规划（保留原文提示词，效果不变）

> 请先不要开始剪辑。读取口播稿、A-roll、B-roll，先完成素材盘点和分镜规划……

产出 `analysis/storyboard.md`，列：口播内容 / 主画面 / B-roll / 字幕 / 动效。

### B2 · 转写（本机走 HyperFrames，不走 video-use）

**先说清楚：`hyperframes transcribe` 在 Windows 上不会自动装好。** 它的运行时获取逻辑是
`brew（仅 macOS）→ git clone + cmake 编译（需要 C 编译器）→ 报错`。本机 git 有、
cmake 和 MSVC 都没有，所以直接跑会失败。模型也不是从国内能连的地址下（走 huggingface.co）。

手动补两条：

```powershell
# 1. 运行时：gh-proxy 下预编译 whisper.cpp（v1.7.6，x64）
curl.exe -L -o "$env:TEMP\whisper.zip" `
  "https://gh-proxy.com/https://github.com/ggml-org/whisper.cpp/releases/download/v1.7.6/whisper-bin-x64.zip"
Expand-Archive "$env:TEMP\whisper.zip" -DestinationPath "$env:LOCALAPPDATA\whisper-cpp" -Force
# 找到 whisper-cli.exe 后写进环境变量
$env:HYPERFRAMES_WHISPER_PATH = "$env:LOCALAPPDATA\whisper-cpp\Release\whisper-cli.exe"

# 2. 模型：hf-mirror 下 ggml-medium.bin（1.53GB，只能靠文件大小校验）
$m = "$env:LOCALAPPDATA\hyperframes\cache\whisper\models"
mkdir $m -Force
curl.exe -L -o "$m\ggml-medium.bin" `
  "https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin"
```

放好后直接跑，不再需要联网：

```powershell
npx hyperframes transcribe A-roll\take01.mp4 -l zh -m medium --to analysis\transcript.srt
```

**为什么不推荐 `pip install openai-whisper`**：要拖 2.5GB torch，而且只解决转写、
不产出 HyperFrames 要的 word-level JSON 结构。

### B2-b · 用本地转写顶掉 ElevenLabs 的实际可行性

可行，但有前提：

| 项 | 结论 |
|---|---|
| 能否让 video-use 不报 401 | ✅ 可以。`transcribe.py` 只在 `<edit>/transcripts/<stem>.json` **不存在时**才调 API，放一份同结构的 JSON 进去就直接命中缓存 |
| 需要什么结构 | Scribe 的 `words: [{text, start, end, type: "word"\|"spacing"\|"audio_event", speaker_id}]` |
| 谁产这个结构 | `hyperframes transcribe` 的 JSON 是 word-level，但要写个十几行的转换脚本映射字段 |
| 质量损失 | 无说话人分离（`speaker_id` 全填 null）、无笑声/音效事件标记、中文分词粒度和 Scribe 不一致 |
| 是否违反 video-use 硬规则 | 不违反。硬规则第 8 条禁止的是 **SRT/短语级**，word-level JSON 正好满足 |
| 不用转换会怎样 | 只喂 SRT 的话，`takes_packed.md` 的静音间隙、重拍检测全部失真，粗剪会切错位置 |

### B3 · 粗剪（video-use）

原文的 8 条硬规则全部生效（**不要在一个词中间下刀**、30ms 淡入淡出、字幕最后加）。本机限制：

- ✅ ffmpeg 可用 → 切片、拼接、调色、字幕都能做
- ❌ 转写依赖 ElevenLabs → 没有 key 就先用 B2 的 SRT 顶替

### B4 · 重新对齐时间轴（关键，别跳）

粗剪后所有 `data-start` 全部重算，旧时间点作废。

### B5 · 关键帧预览

`npm run dev` 或 `npx hyperframes snapshot`，6 个点位。

### B6 · 字幕 + 动效

- 字幕：`embedded-captions` skill（中文逐字高亮用它）
- 动效：`hyperframes-registry` 找现成的，别手搓
- 真人画面包装：`talking-head-recut` skill

```powershell
npx hyperframes transcribe analysis\transcript.srt --to vtt
npx hyperframes check
```

### B7 · 声音

优先级固定：**人声 > 音效 > BGM**。
本机无 MusicGen、无 ElevenLabs，只能接现成音频文件。
想要 BGM：`pip install transformers torch soundfile numpy` 太重（又 2.5GB），建议直接找免费素材。

### B8 · 渲染 + QA + 交付

```powershell
npx hyperframes render . -o out\preview\preview.mp4 -q draft
npx hyperframes render . -o out\final\final.mp4 -w 2
```

交付清单：
- `out/final/final.mp4`
- `index.html`（可编辑工程）
- `analysis/transcript.srt`、`analysis/storyboard.md`
- `qa/*.png`
- 一句话说明：QA 通过 / 还有什么需人工确认

---

## 5. 本机一键提示词

给 Agent 用（替换原文第 8 节）：

```
# AI 视频工作流（本机版）

环境：Windows 11，无 Docker，无任何 API key。
已装：HyperFrames 0.9.0、FFmpeg 9.0.2、Chrome、edge-tts（微软中文语音）。
未装：video-shotcraft、openai-whisper、Remotion 工程。
备选：IndexTTS2 在 vendor/index-tts + conda 环境 indextts（需要克隆音色时用）。

开始前先逐项实测下面这些能力，把「可用 / 不可用 / 需安装」列给我，
不要假设、不要假装调用成功：
1. npx hyperframes --version
2. ffmpeg -version
3. python -c "import edge_tts, soundfile"
4. npx hyperframes transcribe --help
5. video-use 的 transcribe.py（无 ELEVENLABS_API_KEY 应判定为不可用）

规则：
- 没有 key 的云端能力一律跳过，不要问我要。
- 内存总 15.7GB、空闲约 6GB，worker 默认 2–4 即可；只有同时开一堆 Chrome 才需要降。
- 中文配音用 edge-tts（默认 zh-CN-XiaoxiaoNeural）；要克隆音色时用 IndexTTS2；转写优先 hyperframes transcribe -l zh -m medium。
- 动效优先查 hyperframes-registry / video-shotcraft 现成效果，不要从零设计。
- 时长、字幕、音轨一律以实际音频秒数为准，不要用估算值。

按以下顺序执行，每步停下来给我产物，等我确认再继续：
1. 分镜表 → analysis/storyboard.md
2. 配音 → videos/<名字>/audio/vo.mp3（edge-tts）+ 实测时长
3. 关键帧预览 → 截图 6 张
4. 完整合成 → index.html
5. Preview 渲染 → out/preview/
6. QA 抽帧 → qa/，最多 3 轮
7. 最终渲染 → out/final/final.mp4

交付时告诉我：成片路径、工程路径、QA 结论、仍需人工确认的问题。
```

---

## 6. 常见失败对照

| 现象 | 原因 | 修法 |
|---|---|---|
| 渲染无声 | `<audio>` 缺 `id` | 补 `id="vo"` |
| 画面全黑 | GSAP CDN 被墙 | 下载到 `assets/gsap.min.js` 改本地引用 |
| 中文方块 | 字体缺失 | 用 `Microsoft YaHei` |
| 结尾黑屏 | `data-duration` 超音频 | 对齐秒数 |
| 渲染 OOM / Chrome 崩 | 多 worker 抢内存 | `-w 1` 或 `--low-memory-mode` |
| video-use 报 401 | 无 ElevenLabs key | 换 `hyperframes transcribe` |
| 字体下载失败 | 无网 | 只用系统字体，不要 Google Fonts |
