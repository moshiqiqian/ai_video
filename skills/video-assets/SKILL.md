---
name: video-assets
description: 视频流水线第 4 步「素材」。分镜确认后使用，或用户说「加张图」「插个录屏」时使用。负责检查 scenes.json 里引用的素材是否齐全、把用户提供的文件登记进 media 库、缺件时给出具体命令。不做分镜改写、不配音。
---

# 第 4 步 · 素材

保证 `scenes.json` 里每个 `src` 都能找到文件。

## 输入

- `scenes.json` 里所有 `type` 为 `image` / `video` 的 `src`

## 执行

```powershell
python tools\stage.py assets 视频名
```

三种结果：

| 结果 | 含义 | 下一步 |
|---|---|---|
| 素材齐全 | 全部命中 | 确认后做配音 |
| 缺少素材 | 列出缺哪些 | 让用户提供文件 |
| 没有素材需求 | 自动标记 skipped | 直接进入配音 |

## 添加素材

```powershell
python tools\media.py add 视频名 D:\图\架构.png --name 架构图
python tools\media.py list 视频名
```

- `--name` 就是 `scenes.json` 里 `src` 写的名字
- 文件会复制到 `videos/<名字>/media/`
- 大文件不想复制：加 `--link` 只登记路径（原文件不能移动）

## 支持格式

| 类型 | 后缀 |
|---|---|
| 图片 | png / jpg / jpeg / webp / gif / svg / avif |
| 视频 | mp4 / mov / webm / m4v |
| 音频 | mp3 / wav / m4a / aac / flac |

## 缺件时怎么问用户

要具体，不要笼统：

```
第 3 屏需要「架构图」，还没有。
请提供一张架构截图，或者告诉我换一屏不用图的。

如果你有文件：
  python tools\media.py add 降息之后 D:\图\xxx.png --name 架构图
```

## 图片的排版约束

| 项 | 规则 |
|---|---|
| 最大尺寸 | 1420 × 680（超出等比缩小） |
| 位置 | 居中，底部自动留 150px 给字幕 |
| 说明文字 | 可省略，≤ 24 字 |
| 视频 | 静音播放，最长 = 该屏时长 |

图片太宽或竖图会被缩得很小，建议提前裁成 16:9。

## 执行后要做的

1. 列出素材清单（名字 + 类型 + 尺寸）
2. 缺件就停下等用户
3. 齐了之后：

```powershell
python tools\stage.py confirm 视频名 assets
```

## 常见错误

| 报错 | 原因 |
|---|---|
| `缺少素材：架构图` | scenes.json 写了但没 add |
| `没有这个视频` | 名字错 |
| `素材名已存在` | 换 `--name` 或先 remove |
| `不支持的格式` | 转成 png/jpg 再加 |

## 注意

- 不要用外链图片（`https://...`），断网渲染会黑屏
- 素材换了要重跑本阶段，否则下游仍是旧的
- `--link` 的文件被移动或删除后，渲染会失败
