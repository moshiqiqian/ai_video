# 主题

四条命令切换整套配色，不用改 CSS。

```powershell
python tools\video.py theme 视频名              # 看当前 + 全部预设
python tools\video.py theme 视频名 --set warm-paper
python tools\video.py theme 视频名 --color accent=#ff6600
```

## 四套预设

| 名称 | 背景 | 主色 | 适合 |
|---|---|---|---|
| `dark-teal` | `#0a0e13` 近黑 | `#5eead4` 青 | 科技、AI、编程（默认） |
| `warm-paper` | `#f6f1e7` 米白 | `#b4531f` 赭石 | 知识、财经、读书、文摘 |
| `news-red` | `#101114` 深灰 | `#e11d48` 玫红 | 新闻、时评、热点 |
| `mono-ink` | `#0e0e0e` 纯黑 | `#d4d4d4` 灰白 | 极简、严肃话题 |

## 怎么选

```
内容偏技术、要冷静       → dark-teal
内容偏知识、要亲和       → warm-paper
内容偏时事、要冲击       → news-red
内容偏观点、要克制       → mono-ink
```

拿不准就用默认 `dark-teal`，深色背景在手机上更耐看。

## 覆盖单项颜色

预设不满意可以只改一个色：

```powershell
python tools\video.py theme 降息之后 --color accent=#f59e0b
python tools\video.py theme 降息之后 --color bg=#111827
```

可覆盖项：`bg` `ink` `muted` `accent` `sub_bg`。

覆盖会写进 `project.json` 的 `theme_overrides`，换预设时保留。

## 主题会影响什么

| 元素 | 用的色 |
|---|---|
| 背景 | `bg` |
| 背景光晕 | `accent` 的 10% 透明度 |
| 正文、标题 | `ink` |
| 副标题、说明 | `muted` |
| kicker、序号、accent 高亮 | `accent` |
| 副标题背景条 | `sub_bg` |

## 换主题后必做

```powershell
python tools\video.py preview 视频名 --at 3,12,25
```

浅色主题最容易出问题：字幕背景条是白的、文字也是白的，会看不见。先抽帧确认。
