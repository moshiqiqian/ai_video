---
name: video-pipeline
description: 视频流水线总控。用户说「初始化 X」「做一条视频」「继续」「下一步」「进度到哪了」时使用。读取项目状态、判断当前该做哪一步、调度对应操作，并在每步结束时要求人工确认。
---

# 视频流水线总控

## 触发：`初始化 <名字>`

1. 执行 `python tools\pipeline.py start <名字>`
2. 一次只问一个问题，问完等回答

## 六个阶段

```
brief → script → storyboard → voice → mix → render
立项     文案      分镜          配音     混音    渲染
```

## 交互规则

1. 一次只问一个问题。
2. 不替用户决定：风格、时长、语言、音色。
3. 每阶段结束贴出产物，等用户说「可以」再 `confirm`。
4. 上游改了，下游自动 `stale`；不要跳过。

## 每一步

### brief

问：风格、时长、语言、主题。

```powershell
python tools\pipeline.py brief <名字> --style <slug> --duration <秒> --language zh --topic "<主题>"
```

风格从 `engine/styles/` 里选；不确定时列 2–3 个建议。

### script

用户给文稿，或直接写。写入 `source/script.txt` 后：

```powershell
python tools\pipeline.py script <名字> --file source\script.txt
```

停在 `build/lines.json`，让用户看逐句拆分。

### storyboard

```powershell
python tools\pipeline.py storyboard <名字>
```

产出 `build/timeline.json`。同时准备 `film/index.html`、`film/main.js`，先抽 2–3 帧给用户看。

### voice

```powershell
python tools\pipeline.py voice <名字> --voice-pack <音色>
```

IndexTTS2 逐句生成。停，让用户听。

### mix

```powershell
python tools\pipeline.py mix <名字> --bpm 96
```

配乐 + 旁白，−14 LUFS。停，让用户听。

### render

```powershell
python tools\pipeline.py render <名字>
```

输出 `output/render.mp4`，自动抽 3 帧到 `qa/`。停，等确认。

## 状态

```powershell
python tools\pipeline.py status <名字>
```

## 硬规则

- 画面必须是 `render(t)` 单页，不写分镜 section。
- 配音必须逐句，不合并成一条再猜时间。
- 不删除用户素材；不改 `engine/`、`vendor/`。
