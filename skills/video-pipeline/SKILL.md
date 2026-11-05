---
name: video-pipeline
description: 视频流水线总控。用户说「初始化 X」「做一条视频」「继续」「下一步」「这步重做」「进度到哪了」时使用。负责读取项目状态、判断当前该做哪一步、调度对应的阶段技能、并在每步结束时要求人工确认。不要在这里直接写文案或画面，交给阶段技能。
---

# 视频流水线总控

## 触发词：`初始化 <名字>`

用户说 **「初始化 玻尔兹曼机」** 这样一句话，就进入流程：

1. 立刻执行 `python tools\stage.py start <名字>`
2. **只问第一个问题**，等回答
3. 回答完问第二个……四个都拿到才 `brief`

不要一次列四个问题，不要替用户选默认值。

一条视频分六个阶段，每阶段独立执行、独立确认。

```
brief → script → storyboard → assets → voice → render
立项     文案      分镜         素材      配音      渲染
```

## 交互协议（最重要）

**这是对话，不是批处理。** 违反任何一条，用户会觉得「什么都没问我」。

1. **一次只问一个问题**，问完停下，等回答再问下一个。
2. **不替用户决定**：时长、风格、音色、保留哪几段，必须用户说。
3. **命令参数必须来自用户回答**：`brief` 缺 `--duration` 或 `--theme` 会直接报错退出，这是故意的。
4. **每阶段结束必须停**，贴出产物，说明「请确认」。
5. **确认才 `confirm`**：用户没说「可以 / 确认 / 继续」，不许执行。

### 提问格式（两种环境都要能跑）

有结构化提问工具的 Agent（如 OpenCode 的 `question`）优先用工具。

**纯文字环境（Codex CLI、终端）用编号列表**，并注明可以回数字或自由回答：

```
问：这条视频讲什么形态？
1. 科普
2. 时评
3. 产品介绍
4. 教程

回复数字，或直接说你的答案。
```

不要一次列四个问题，不要用「默认值」跳过。

## 开工：先建目录，再逐个问

```powershell
python tools\stage.py start 视频名
```
它会列出四个待问项：

```
Q1. 内容形态：科普 / 时评 / 产品介绍 / 教程
Q2. 多长：15 / 30 / 45 / 60 秒
Q3. 视觉风格：dark-teal / warm-paper / news-red / mono-ink
Q4. 有没有现成文稿：有给路径 / 没有由 AI 写
```

**先问 Q1，等回答；再问 Q2……** 四个都拿到后：

```powershell
python tools\stage.py brief 视频名 --duration 45 --theme dark-teal [--from 文稿路径]
```

## 开工前：读状态

```powershell
python tools\stage.py list
python tools\stage.py status <视频名>
python tools\stage.py ask <视频名>
```

`status` 会打印六个阶段的状态：

| 状态 | 含义 | 该做什么 |
|---|---|---|
| 待做 | 还没开始 | 执行该阶段 |
| 完成 ✓ | 有产物且已确认 | 跳到下一阶段 |
| 完成（无 ✓） | 有产物，等你确认 | 给用户看产物 |
| 过期 | 上游改过，产物作废 | 重跑该阶段 |
| 跳过 | 本片不需要 | 忽略 |

## 主循环

```
1. status → 找到「下一步」
2. 告诉用户：现在第几阶段、上一步产出什么、这一步会产出什么
3. 确认需要的输入齐了（文案？素材？）
4. 加载对应的阶段技能，执行
5. 把产物给用户看，等回答
6. 用户认可 → confirm → 回到 1
   用户要改 → 重跑该阶段（或回到上游）
```

## 每支视频的目录约定

```
videos/<名字>/
├── source/              你放素材的地方
│   ├── articles/        md / txt 文稿
│   ├── images/          图片
│   └── clips/           视频片段（B-roll、录屏）
├── script.txt           旁白（你改）
├── scenes.json          画面（你改）
├── project.json         状态机
├── build/               中间态，可删可重建
│   ├── brief.md
│   ├── script.json
│   ├── storyboard.md
│   ├── transcript.json
│   ├── voice.json
│   └── render.json
├── audio/               配音
├── qa/                  抽帧检查
└── output/render.mp4    成品
```

规则：

- 只碰 `source/`、`script.txt`、`scenes.json`
- `build/` 是程序产物，删了能重建
- 成品只在 `output/`

## 阶段与技能对照

| 阶段 | 技能 | 产物 | 确认物 |
|---|---|---|---|
| brief | `video-brief` | `build/brief.md`、`script.txt` 初稿、`scenes.json` 骨架 | 主题/时长/风格 |
| script | `video-script` | `script.txt`、`build/script.json` | 全文和字数 |
| storyboard | `video-storyboard` | `scenes.json`、`build/storyboard.md` | 分镜表格 |
| assets | `video-assets` | `media/index.json` | 素材清单 |
| voice | `video-voice` | `audio/vo.*`、`build/voice.json` | 让用户听 |
| render | `video-render` | `output/render.mp4`、`qa/*.png` | 预览帧 + 成片 |

## 命令

```powershell
python tools\stage.py brief      视频名 --from D:\文章.md --duration 45 --theme news-red
python tools\stage.py script     视频名
python tools\stage.py storyboard 视频名
python tools\stage.py assets     视频名
python tools\stage.py voice      视频名
python tools\stage.py render     视频名 --quality delivery

python tools\stage.py confirm 视频名 <阶段>   # 记录人工确认
python tools\stage.py status  视频名
python tools\stage.py next    视频名
```

## 硬规则

1. **没确认不许推进**。上游 `confirmed=false` 时，下一阶段会直接报错退出。
2. **过期必须重做**。`stale` 状态下 `confirm` 会被拒绝，先重跑该阶段。
3. **一次只做一个阶段**。不要连着跑 script 和 storyboard。
4. **改文案 = 重做分镜、配音、渲染**。系统会自动标 stale，照着提示走。
5. **用户说「直接出片」** 才允许 `--force`，并要说明跳过了哪些确认。

## 常见情况

**用户没有文稿，只有一句主题**
→ 走 `video-brief`，不带 `--from`，由 brief 写骨架，然后 script 阶段写稿。

**用户给了 md**
→ `video-brief` 负责导入、体检、给候选，不要自己读文件。

**用户改了文案**
→ 重跑 script → 确认 → storyboard（会提示过期）→ voice → render。

**用户只想换配色**
→ 不用走流水线，直接 `stage.py` 之外用 `make.py --theme`，或改 `project.json` 的 theme 后重渲染。

**用户问「做到哪了」**
→ 跑 `status`，把表格转述成一句话：「文案和分镜完成，配音待做」。

## 汇报格式

每次执行完一个阶段，用这个结构：

```
【第 2 步 · 文案】
产出：script.txt（186 字，预计 41 秒）
        build/script.json（逐句清单）
问题：2 句超过 40 字，TTS 会念得吃力
请确认：可以继续做分镜吗？
```
