# library · 可复用素材与组件

从 HyperFrames 官方 registry 下载的现成块和效果，**项目级共享**，不属于任何单支视频。

和每支视频自己的 `videos/<名字>/source/` 分开：

| 目录 | 内容 | 归属 |
|---|---|---|
| `library/` | 通用块、效果、背景 | 全项目复用 |
| `videos/<名字>/source/` | 这一支用到的文稿、图片、录屏 | 单支视频 |

## 现有内容

### blocks（整屏可复用段落）

| 名字 | 用途 |
|---|---|
| `data-chart` | 柱状 + 折线图，NYT 风格排版 |
| `bar-chart-race` | 条形图竞速（排名变化） |
| `code-typing` | 代码逐字打出 |
| `code-snippet-dark-2026` | VS Code 界面 + 打字动画 |
| `exploded-stack` | 分层结构爆炸图（架构图） |
| `camcorder-hud` | 摄像机 HUD 覆盖层 |
| `ai-answer-rank` | AI 回答排名卡片 |
| `editorial-flash-overlay` | 闪白转场 |
| `chromatic-radial-split` | 色差径向转场 |
| `flash-through-white` | 白闪转场 |
| `cinematic-zoom` | 电影感缩放转场 |

### components（叠加效果 / 小动画）

| 名字 | 用途 |
|---|---|
| `blur-in` | 文字从模糊到清晰 |
| `bottom-up-letters` | 逐字从下往上出现 |
| `caption-clip-wipe` | 字幕逐词擦除 |
| `caption-editorial-emphasis` | 重点词放大强调 |
| `aurora-drift` | 极光背景 |
| `beat-pulse-background` | 随节拍脉动的背景 |
| `camera-shake` | 手持抖动 |
| `agent-cursor` | AI 光标操作演示 |
| `badge-pop` | 徽章弹跳 |
| `beat-accent` | 节拍重音闪动 |
| `before-after-wipe` | 前后对比擦除 |
| `browser-device-stage` | 浏览器/手机外框 |
| `animated-bar-chart` | 紧凑数据卡片 |

## 怎么用

在 composition 里挂载：

```html
<template data-composition-src="library/blocks/data-chart.html"
          data-start="5" data-duration="8"></template>
```

或直接复制片段进自己的 `build/index.html` / 模板里改。

## 继续下载

```powershell
npx hyperframes@0.9.0 catalog                 # 列出全部（约 400 个）
npx hyperframes@0.9.0 catalog --tag chart     # 按标签筛
npx hyperframes@0.9.0 add <名字>               # 安装到 library/
```

`hyperframes.json` 已把安装路径指到 `library/blocks`、`library/components`，所以新装的也会落在这里。

## 注意

- 这些是**第三方组件**，来源 `heygen-com/hyperframes` registry，各自可能带独立许可，商用前确认
- 装进来是源码，可以改；但组件升级会覆盖（除非加 `--force`）
- 它们和 `templates/` 不冲突：`templates/` 是你的设计语言，`library/` 是现成效果库
