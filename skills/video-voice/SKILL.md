---
name: video-voice
description: 视频流水线第 5 步「配音」。文案确认后使用，或用户说「换个声音」「用我自己的声音」「重新配音」时使用。负责用 edge-tts 或 IndexTTS2 生成音频、记录时长和参数。不做画面、不渲染。
---

# 第 5 步 · 配音

把 `script.txt` 变成一条音频，并让用户试听。

## 输入

- `script.txt`
- `project.json` 的 `engine` / `voice` / `voice_pack` / `rate`

## 执行

```powershell
python tools\stage.py voice 视频名
```

指定引擎或音色：

```powershell
python tools\stage.py voice 视频名 --engine edge --voice zh-CN-YunyangNeural
python tools\stage.py voice 视频名 --engine indextts --voice-pack xiaoxiao
```

## 两种引擎

| | edge-tts | IndexTTS2 |
|---|---|---|
| 耗时 | 约 2 秒 | 45 秒文案约 7 分钟 |
| 音色 | 8 种固定中文 | 任意克隆 |
| 需要显卡 | 否 | 是，6 GB |
| 稳定性 | 偶发返回空文件 | 本地，稳定 |

**默认用 edge-tts。** 用户明确要「自己的声音」才用 IndexTTS2。

## 产出

| 文件 | 内容 |
|---|---|
| `audio/vo.mp3` 或 `audio/vo_<音色>.wav` | 配音 |
| `build/voice.json` | 引擎、音色、时长、生成时间 |

## 执行后要做的

1. 报三个数：时长、引擎、文件路径
2. **让用户听一遍**：

```
start videos/名字/audio/vo.mp3
```

3. 等确认：

```powershell
python tools\stage.py confirm 视频名 voice
```

**这是唯一必须人工听的环节。** 字数对了不代表念得顺，多音字、断句问题只有听才知道。

## 换声音

| 用户说 | 做法 |
|---|---|
| 换个男声 | `--voice zh-CN-YunyangNeural` |
| 用我自己的声音 | 先加音色，再 `--engine indextts --voice-pack 名字` |
| 语速快一点 | 改 `project.json` 的 `rate` 为 `+8%` |
| 重配一遍 | 直接重跑本阶段（会覆盖） |

## 加自己的音色

```powershell
python tools\voice.py add 我的声音 D:\录音.m4a --start 2 --dur 8 --label "本人"
python tools\voice.py list
```

要求：3–15 秒、单人、无背景音、不爆音。

## 常见错误

| 报错 | 原因 |
|---|---|
| `上游「文案」还没确认` | 先 confirm script |
| `NoAudioReceived` | edge-tts 服务抖动，重跑一次 |
| `IndexTTS2 需要 voice_pack` | 加 `--voice-pack` |
| `声音库里没有「xx」` | `voice.py list` 看名字 |
| 音频 0 字节 | 网络或服务问题，重跑 |

## 参考

- `references/voices.md` — 音色清单、选择建议、克隆注意事项
