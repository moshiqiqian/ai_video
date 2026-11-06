# engine/ — Lemo 渲染链（vendored）

来源：https://github.com/lemomo-ai/lemo-opuscar （MIT，见 `LICENSE-lemo.txt`）

## 两条链

```
传统链   scenes.json → make.py → HyperFrames → render.mp4
新链     film/index.html (render(t)) → 逐帧截图 → ffmpeg → render.mp4
```

只要 `videos/<slug>/film/index.html` 存在，`stage.py render` 就走新链。

## 目录

```
engine/
  core/            渲染器、抽帧、事件、混音工具
  styles/<slug>/   66 份 STYLE.md 风格规范（只保留文档，不含 demo 代码）
  package.json     playwright-core + three
```

## 用法

```powershell
# 体检
python tools\lemo.py doctor

# 抽帧看效果
python tools\lemo.py still lemo-demo 2 8 13 19

# 出片
python tools\lemo.py render lemo-demo
```

首次运行会自动 `npm install`。需要本机 Chrome 或 Edge（自动探测），也可用 `PLAYWRIGHT_CHROME` 指定。

## 片子的结构

```
videos/<slug>/film/
  index.html       只有一个 canvas
  main.js          window.render(t) / window.DUR / window.READY
  lines.json       逐句文案与时间
  audio/mix.wav    旁白 + 配乐（可选）
  tools/           tts.py、music.py 等生成脚本
```

`render(t)` 是纯函数：给第 t 秒，画出那一帧。不依赖上一帧，可以任意顺序渲染。

## 没搬进来的

- 66 个风格的 demo 引擎代码（体积大、各片专用）。这里只保留 `STYLE.md`，需要时从上游取。
- 上游的 Python venv、Kokoro 模型、采样库。

## 下一步

1. 把 `stage.py` 的 brief/script/storyboard 产物改成 `lines.json` + `timeline.json`
2. 按风格补引擎（先做 ink-wash、swiss-motion、dataviz）
3. 接上配乐/音效/混音与 readcheck、cuecheck
