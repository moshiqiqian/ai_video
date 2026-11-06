# AI-v · 用代码生成短视频

一句话文案，六步确认，产出一条带配音、配乐、字幕的 MP4。
画面不是模板，是每一帧算出来的。

```
文案 → 逐句配音 → 时间轴 → render(t) 画面 → 逐帧截图 → 混音 → MP4
```

全程本机运行，不调用任何在线生成 API。

## 六步

```
brief → script → storyboard → voice → mix → render
立项     文案      分镜          配音     混音    渲染
```

每一步都留下文件，都要你点头才继续；上游改了，下游自动标记过期。

| 步 | 产物 | 谁来做 |
|---|---|---|
| 立项 | `project.json`、`source/brief.md` | 选风格、时长、语言 |
| 文案 | `build/lines.json` | 按句拆开 |
| 分镜 | `build/timeline.json` | 每句的起止时间 |
| 配音 | `film/audio/l1.wav…`、`voice.wav` | IndexTTS2 克隆音色 |
| 混音 | `music.wav`、`mix.wav` | 配乐 + 侧链，−14 LUFS |
| 渲染 | `output/render.mp4`、`qa/` | 逐帧截图 + ffmpeg |

## 快速开始

```powershell
python tools\pipeline.py start demo
python tools\pipeline.py brief demo --style swiss-motion --duration 48 --language zh --topic "主题"
python tools\pipeline.py script demo --file source\script.txt
python tools\pipeline.py storyboard demo
python tools\pipeline.py voice demo
python tools\pipeline.py mix demo
python tools\pipeline.py render demo
```

画面文件在 `videos/<名字>/film/`：一个 `index.html`、一个 `main.js`，暴露：

```js
window.render = t => { ... };
window.DUR = 48;
window.READY = true;
```

## 示例

`videos/pipeline-showcase/`：48 秒，六阶段流程图，中文旁白 + 程序化配乐。

```powershell
start videos\pipeline-showcase\output\render.mp4
```

## 依赖

| 功能 | 依赖 |
|---|---|
| 画面渲染 | Node 20+、`engine/` 里的 playwright-core + three、Chrome 或 Edge、ffmpeg |
| 配音 | conda 环境 `indextts`（Python 3.11、torch 2.8 + CUDA）、`vendor/index-tts/`、`voices/<音色>/sample.wav` |
| 配乐 / 混音 | conda 环境 `aivideo`（Python 3.13、numpy、soundfile）、ffmpeg |
| 流水线 | conda 环境 `aivideo`（只用标准库） |
| 字幕 | 画在 canvas 里，无额外依赖 |

完整安装见 [docs/INSTALL.md](docs/INSTALL.md)。流程细节见 [docs/PIPELINE.md](docs/PIPELINE.md)。

## 目录

```
engine/           渲染器 + 66 份风格规范（vendored，MIT）
tools/            pipeline.py / lemo.py / say_lines.py / music_bed.py
videos/<片子>/     source build film output qa
voices/           克隆音色样本
vendor/index-tts/ IndexTTS2 模型
env/              conda 环境定义
docs/             安装与流程文档
```

## 版本

v3.0.0。旧的模板拼装链已移除；需要时从 git 历史取回。
