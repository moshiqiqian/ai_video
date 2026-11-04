---
name: video-brief
description: 视频流水线第 1 步「立项」。用户给出主题、或给了一份 md/txt 文稿要做视频时使用。负责导入并清洗文稿、体检字数与句长、给出压缩建议和候选标题/金句/分镜，建工程目录和参数。不写最终文案，也不做分镜。
---

# 第 1 步 · 立项

把「一句话主题」或「一篇文章」变成一份可执行的立项说明。

## 输入

| 来源 | 命令 |
|---|---|
| 只有主题 | `python tools\stage.py brief 视频名 --duration 45` |
| 有文稿 | `python tools\stage.py brief 视频名 --from D:\文章\降息.md --duration 45` |

常用参数：

```
--duration 45          目标时长（秒）
--theme news-red       配色（dark-teal / warm-paper / news-red / mono-ink）
--engine edge          配音引擎
--voice zh-CN-XiaoxiaoNeural
--voice-pack xiaoxiao  IndexTTS2 时用
--no-subtitles         不要字幕
```

## 产出

| 文件 | 内容 |
|---|---|
| `project.json` | 参数 + 六阶段状态机 |
| `brief.md` | 体检报告 + 候选清单 + 待定问题 |
| `source/原文.md` | 原始文稿（只读，便于回看） |
| `script.txt` | 清洗后的正文（下一阶段的起点） |
| `scenes.json` | 三屏骨架（标题/要点/结尾） |

## 执行后要做的

1. 读 `brief.md`，**用三句话转述给用户**：
   - 原文多少字、属于哪类（A 直接可用 / B 需压缩 / C 偏长 / D 密度过高）
   - 建议压缩到多少字
   - 有哪些候选（标题、金句、小标题）

2. 问用户三件事：
   - 全文压缩，还是只取其中几段？
   - 标题用原文的还是另起的？
   - 有没有必须保留的句子？

3. 用户回答后：

```powershell
python tools\stage.py confirm 视频名 brief
```

## 文稿类型判断

| 类型 | 特征 | 处理 |
|---|---|---|
| A | 已接近口播稿，字数合适 | 只需分句 |
| B | 文章/博客，2–3 倍字数 | 压缩 + 口语化 |
| C | 4–6 倍字数 | 只取核心段落 |
| D | 信息密度过高（论文、文档） | 重写而不是压缩 |

判断由 `brief.md` 的「体检」给出，不要自己猜。

## 注意

- **不要在这里改写文案**。压缩和口语化是 `video-script` 的事。
- 图片不会自动入库，只在 `brief.md` 里列出路径，由 `video-assets` 处理。
- 如果用户没有文稿，`script.txt` 是空的，直接进入 script 阶段手写。

## 常见错误

| 报错 | 原因 |
|---|---|
| `已存在：videos/xxx` | 同名视频已存在，换名字或加 `--force` |
| `找不到文稿` | 路径错，注意 Windows 反斜杠和空格 |
| `没有这个视频` | 还没立项，先跑 brief |

## 参考

- `references/import.md` — md 清洗规则、结构到分镜的映射
