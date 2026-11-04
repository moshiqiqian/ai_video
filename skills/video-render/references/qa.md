# 质检

## 抽帧

渲染阶段自动抽 3 帧：

```
videos/<名字>/qa/at-2.5s.png
videos/<名字>/qa/at-14.7s.png
videos/<名字>/qa/at-27.9s.png
```

手动抽指定时间：

```powershell
npx hyperframes@0.9.0 snapshot . --at 3,12,25 -o videos\名字\qa --keep
```

或直接从成片取帧：

```powershell
ffmpeg -ss 8 -i videos\名字\render.mp4 -frames:v 1 videos\名字\qa\check.png -y
```

## 清单

### 技术项

| 项 | 标准 | 怎么查 |
|---|---|---|
| 时长 | 和配音一致（±0.3 秒） | `ffprobe` |
| 分辨率 | 1920×1080 或设定值 | `ffprobe` |
| 帧率 | 30 | `ffprobe` |
| 音轨 | 有 AAC，不是静音 | `ffmpeg -af volumedetect` |
| 文件大小 | draft 几分钟片约 1–2 MB | 目测 |

一条命令看全：

```powershell
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,duration -of default=nw=1 videos\名字\render.mp4
```

音量：

```powershell
ffmpeg -hide_banner -i videos\名字\render.mp4 -af volumedetect -f null NUL 2>&1 | findstr volume
```

正常范围：mean −22 ~ −16 dB，max −4 ~ −1 dB。

### 内容项

| 项 | 常见问题 |
|---|---|
| 首帧 | 全黑、只有背景 |
| 切换点 | 画面比语音早/晚 0.5 秒以上 |
| 文字 | 出框、换行难看、字号过小 |
| 字幕 | 压住别的文字、超长单行 |
| 图片 | 变形、过小、被字幕遮挡 |
| 结尾 | 黑屏拖尾、字突然消失 |
| 主题 | 浅色主题下字幕看不清 |

## 常见问题与修法

| 现象 | 原因 | 修 |
|---|---|---|
| 首帧全黑 | 标题从 opacity 0 开始 | 让首帧就有内容 |
| 结尾黑屏 2 秒 | `data-duration` 比音频长 | 由 make.py 自动计算，一般是音频过长 |
| 画面早于语音 | 分镜边界按均分猜 | 补 `start_at_sentence` |
| 字幕和语音错开 | 转写对齐漂移 | 缩短字幕条（12 字以内） |
| 字太小 | 手机看不清 | 标题 ≥ 100px，正文 ≥ 40px |
| 浅色主题发白 | 字幕背景条也是浅色 | 换 `sub_bg` 或改回深色主题 |

## 交付前最后三件

1. 用手机看一遍（竖屏/横屏都看）
2. 音量对一下（和别的视频比，别突然变小声）
3. 文件名改成人能读的（`降息之后_v1.mp4`），别用时间戳

## 留档

`render.json` 记录了画质、时长、大小、渲染时间。改稿重渲后对比一下，能看出是哪一版。
