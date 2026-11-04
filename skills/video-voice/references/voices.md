# 音色

## edge-tts（默认，免费，快）

| 音色 ID | 性别 | 风格 | 适合 |
|---|---|---|---|
| `zh-CN-XiaoxiaoNeural` | 女 | 温暖自然 | 通用（默认） |
| `zh-CN-XiaoyiNeural` | 女 | 活泼 | 生活、种草 |
| `zh-CN-YunyangNeural` | 男 | 新闻播报 | 时评、财经 |
| `zh-CN-YunxiNeural` | 男 | 阳光 | 科普、教程 |
| `zh-CN-YunjianNeural` | 男 | 激情解说 | 体育、燃向 |
| `zh-CN-liaoning-XiaobeiNeural` | 女 | 东北话 | 搞笑、接地气 |
| `zh-CN-shaanxi-XiaoniNeural` | 女 | 陕西话 | 地域内容 |

外语也支持（英语、日语、韩语、法语等 300+ 音色）。

## IndexTTS2（克隆任意音色）

```powershell
python tools\voice.py add 名字 录音.m4a --start 2 --dur 8 --label "本人"
python tools\stage.py voice 视频名 --engine indextts --voice-pack 名字
```

### 样本要求

| 项 | 建议 |
|---|---|
| 时长 | 5–10 秒（最少 3 秒） |
| 内容 | 一句完整的话，正常语速 |
| 环境 | 安静，无背景音乐、无回声 |
| 音量 | 不爆音、不过小 |
| 人数 | 单人 |

### 效果预期

- 音色相似度高，但语调和停顿仍带模型自己的习惯
- 中文四声偶有偏差，多音字可能读错
- 45 秒文案约 7 分钟，别用它做草稿迭代

## 什么时候选哪个

```
要快、要反复改文案      → edge-tts
要自己的声音 / 品牌音色  → IndexTTS2
要外语                  → edge-tts（IndexTTS2 中文为主）
没显卡                  → edge-tts
```

## 语速

`project.json` 里的 `rate`：

| 值 | 效果 |
|---|---|
| `-8%` | 沉稳，适合新闻 |
| `+0%` | 默认 |
| `+8%` | 轻快，适合抖音 |

中文 TTS 的 4.5 字/秒是按 `+0%` 算的，改语速后时长会变，要重新算。

## 音量

生成后可以用 ffmpeg 统一：

```powershell
ffmpeg -i vo.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11 vo_norm.mp3
```

## 常见问题

**一句话念不完**
→ 超过 40 字了，拆句。

**数字读错**
→ 改成阿拉伯数字；特别重要的数字单独成句。

**英文词读成拼音**
→ 换成中文谐音，或接受（字幕用原文）。

**声音忽大忽小**
→ 分句生成时每句单独归一化，或整体 loudnorm。
