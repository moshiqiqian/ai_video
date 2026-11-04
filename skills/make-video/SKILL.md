---
name: make-video
description: 引导完成一条视频的全流程：定主题、写文案、拆分镜、加素材、配音、校验、渲染、质检。当用户说「做一条视频」「生成视频」「做个时评」「帮我写个口播视频」「把这个内容做成视频」时使用。只负责流程与判断，具体命令由 tools/ 下的脚本执行。
---

# 制作视频

把一句需求变成一条能发布的 MP4。**七个阶段，每个阶段停下来确认。**

## 铁律

1. **不要一次性跑完**。每个阶段结束必须把结果给用户看，等确认再继续。
2. **先文字后画面**。分镜先用表格写，确认后再转 JSON。
3. **渲染前必须过 `check`**。有 error 不许渲染。
4. **时长先定，文案后写**。字数按住 4.5 字/秒 换算。
5. **一屏只放一个视觉重点**，清单最多 2 行。

## 环境确认（开工前）

```powershell
python tools\video.py list
```

- 能列出视频 → 环境正常，进入 P0
- 报 `ModuleNotFoundError` → 让用户先按 `INSTALL.md` 装环境，停止

---

## P0 · 定主题

问用户三件事，一次问完，不要挤牙膏：

1. **内容是什么**（一句话）——时评 / 科普 / 产品介绍 / 教程
2. **多长**——15s / 30s / 45s / 60s
3. **风格**——`dark-teal`（科技深色，默认）/ `warm-paper`（浅色纸质，知识类）/ `news-red`（新闻感）/ `mono-ink`（极简黑白）

然后建工程：

```powershell
python tools\video.py init 视频名 --theme dark-teal --duration 45
```

`视频名` 用中文短词，不要带空格和斜杠。

---

## P1 · 写文案

字数 = 目标秒数 × 4.5。

参考 `references/copywriting.md` 的结构：

```
钩子（1 句）→ 事实（2–3 句）→ 解读（2–3 句）→ 观点（1–2 句）
```

写进 `videos/<名字>/script.txt`，然后**把全文和字数给用户看，等他改**。

自查：

- 有没有超过 40 字的长句（TTS 会念不完）
- 数字用阿拉伯数字
- 至少 3 个句号，否则没有停顿可切

---

## P2 · 分镜草稿（先表格，不写 JSON）

按文案的句意切屏，先输出表格：

| 屏 | 从第几句 | 类型 | 内容 |
|---|---|---|---|
| 1 | 1 | title | 标题 + 副标题 |
| 2 | 4 | list | 两个要点 |
| 3 | 9 | quote | 一句金句 |
| 4 | 12 | ending | 结尾 |

规则见 `references/storyboard.md`。核心：

- 3–8 屏
- 每屏 2–6 秒
- 清单最多 2 行，每行 ≤ 12 字
- 标题 ≤ 16 字，金句 ≤ 24 字

**把表格给用户确认**，改了再往下。

确认后写成 `videos/<名字>/scenes.json`。

---

## P3 · 素材（可选）

问一句：「有图或录屏要放进去吗？」

有：

```powershell
python tools\media.py add 视频名 D:\图\xxx.png --name 架构图
python tools\media.py list 视频名
```

然后在 scenes.json 里用 `{"type":"image","src":"架构图"}`。

没有就跳过。

---

## P4 · 配音

默认微软音色（快）：

```powershell
python tools\video.py render 视频名 --quality draft --no-qa
```

只到出 HTML 和音频就够，或者在 P6 一起做。

用户要「自己的声音」→ 先加音色：

```powershell
python tools\voice.py add 我的声音 录音.m4a --start 2 --dur 8
python tools\video.py theme 视频名        # 确认当前设置
```

改 `project.json` 的 `engine` 为 `indextts`、`voice_pack` 为音色名，然后重新渲染。

**IndexTTS2 很慢**：45 秒文案约 7 分钟，提前告诉用户。

---

## P5 · 校验（强制关卡）

```powershell
python tools\video.py check 视频名
```

| 输出 | 处理 |
|---|---|
| 有 `[错误]` | 逐条修，修完重跑，**不许跳过** |
| 只有 `[提醒]` | 把提醒念给用户，问要不要改 |
| 全过 | 进入 P6 |

常见错误：标题超长、清单超 12 字、素材不存在、`start_at_sentence` 超出句数。

---

## P6 · 渲染

**先抽帧看排版**（30 秒，避免白等）：

```powershell
python tools\video.py preview 视频名 --at 3,12,25
```

看 `videos/<名字>/qa/` 里的图，检查：

- 文字有没有出框
- 有没有和字幕打架
- 深色/浅色主题对比度够不够

没问题再渲染：

```powershell
python tools\video.py render 视频名 --quality delivery --transcribe
```

- `--transcribe`：需要字幕时加（约 30 秒）
- `--quality`：`draft` 快速看效果、`looks` 默认、`delivery` 发布用

---

## P7 · 质检与交付

渲染完自动抽 3 帧到 `videos/<名字>/qa/`。检查：

| 项 | 标准 |
|---|---|
| 有声音 | 抽帧看不出，让用户播一下 |
| 首帧不空 | at-0s 有内容 |
| 结尾无黑屏 | 最后一帧有字 |
| 字幕同步 | 抽查 2–3 个切换点 |

交付时告诉用户：

1. 成片路径
2. 时长、分辨率
3. 改内容只需改哪个文件
4. 要不要再调整

---

## 常用修正指令（用户说这些时直接改）

| 用户说 | 做什么 |
|---|---|
| 太长了 | 砍文案，重新走 P1 |
| 画面太空 | 加 image 屏或拆 list |
| 节奏太慢 | 减少屏数，或缩短停顿 |
| 换个风格 | `video.py theme 名字 --set warm-paper` 后重渲染 |
| 字幕不好读 | 改 `project.json` 里 `subtitles: false` 或缩短句子 |
| 声音不好听 | 换 engine / voice |

---

## 参考文档

- `references/copywriting.md` — 文案结构与字数换算
- `references/storyboard.md` — 分屏规则、类型用法、常见错误
- `references/themes.md` — 四套主题的适用场景
