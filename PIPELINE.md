# 新流水线：六阶段 · render(t)

旧链（`scenes.json` + HyperFrames + 模板）保留在 `tools/stage.py`，只用于老项目。
新项目一律走这条。

## 六个阶段

```
brief → script → storyboard → voice → mix → render
立项     文案      分镜          配音     混音    渲染
```

每步独立执行、独立确认；上游改了，下游自动标记 `stale`。

| 阶段 | 产物 | 说明 |
|---|---|---|
| brief | `source/brief.md`、`project.json` | 风格、时长、语言、fps |
| script | `build/lines.json` | 按句拆分，一句一条 |
| storyboard | `build/timeline.json` | 每句的起点、终点、时长 |
| voice | `film/audio/*.mp3`、`voice.wav`、`film/lines.json` | 一句一个文件，按实际时长重排 |
| mix | `film/audio/music.wav`、`mix.wav` | 配乐 + 旁白，侧链压低，−14 LUFS |
| render | `output/render.mp4`、`qa/` | 逐帧截图 + ffmpeg 合成 |

## 命令

```powershell
python tools\pipeline.py start    <slug>
python tools\pipeline.py brief    <slug> --style swiss-motion --duration 48 --language zh --topic "主题"
python tools\pipeline.py script   <slug> --file source\script.txt
python tools\pipeline.py storyboard <slug>
python tools\pipeline.py voice    <slug>
python tools\pipeline.py mix      <slug> --bpm 96
python tools\pipeline.py render   <slug> --workers 4
python tools\pipeline.py confirm  <slug> <stage>
python tools\pipeline.py status   <slug>
```

## 画面

`film/index.html` 只有一个 `<canvas>`，动画全在 `film/main.js`：

```js
window.render = t => { ... };   // 给第 t 秒，画那一帧
window.DUR = 48;
window.READY = true;
```

不依赖上一帧，任意顺序都能渲染。

## 风格

`engine/styles/<slug>/STYLE.md`，来自 Lemo 的 66 份规范。写 `film/main.js` 前先读它。

## 检查

- 每步结束抽帧看一遍
- `render` 自动抽 3 帧到 `qa/`
- 混音目标 −14 LUFS / −1.5 dBTP
- 字幕与 `lines.json` 同源

## 示例

`videos/pipeline-showcase/`：48 秒，六阶段流程图，中文旁白 + 程序化配乐。

```powershell
start videos\pipeline-showcase\output\render.mp4
```
