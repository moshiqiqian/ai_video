# AGENTS.md

## 这个仓库是什么

用代码生成短视频。一条片子 = 一个 `render(t)` 页面 + 逐句配音 + 程序化配乐。

旧链（`stage.py`、`make.py`、`templates/`、`library/`、HyperFrames）已移除，不要恢复。

## 六个阶段

```
brief → script → storyboard → voice → mix → render
```

每步必须停下来等用户确认。不要一次问多个问题，不要替用户选时长、风格、音色。

命令：

```powershell
python tools\pipeline.py start <slug>
python tools\pipeline.py brief <slug> --style <style> --duration <秒> --language zh
python tools\pipeline.py script <slug> --file source\script.txt
python tools\pipeline.py storyboard <slug>
python tools\pipeline.py voice <slug> [--voice-pack xiaoxiao]
python tools\pipeline.py mix <slug>
python tools\pipeline.py render <slug>
python tools\pipeline.py confirm <slug> <stage>
python tools\pipeline.py status <slug>
```

## 画面规则

- 文件：`videos/<slug>/film/index.html` + `main.js`
- 必须暴露 `window.render(t)`、`window.DUR`、`window.READY`
- 纯函数：不读上一帧，不用 `Date.now()`，随机必须固定种子
- 1920×1080，24fps，文字避开底部 90px 字幕区
- 先读 `engine/styles/<style>/STYLE.md`，再写画面

## 声音规则

- 配音：IndexTTS2，`vendor/index-tts/` + `voices/<pack>/sample.wav`
- 一句一个 WAV，文本不变就复用缓存
- 配乐：`tools/music_bed.py`
- 混音：旁白 + 配乐侧链，−14 LUFS / −1.5 dBTP

## 目录

```
engine/core/       渲染器（node）
engine/styles/     66 份风格规范
tools/pipeline.py  六阶段
tools/lemo.py      渲染封装
tools/say_lines.py IndexTTS2 批量配音
tools/music_bed.py 配乐
videos/<slug>/     source build film output qa
voices/            音色样本
vendor/index-tts/  模型
```

## 检查

- 渲染前抽帧看：`python tools\lemo.py still <slug> 2 8 12`
- 渲染后自动抽 3 帧到 `qa/`
- 字幕时间和 `build/lines.json` 同源
- 音轨响度用 ffmpeg `ebur128` 复核

## 禁止

- 不写模板拼装、section + GSAP 的分镜页
- 不把配音合成为一条再靠 ASR 猜时间
- 不在 `engine/`、`vendor/` 里改上游代码
