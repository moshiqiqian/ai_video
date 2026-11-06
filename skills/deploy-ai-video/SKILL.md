---
name: deploy-ai-video
description: 在新机器上安装 AI-v（Python 环境、IndexTTS2 模型、Node 渲染器、Chrome、ffmpeg），或环境损坏后重建、诊断。用户说「换电脑怎么装」「环境坏了」「重新部署」时使用。
---

# 部署 AI-v

完整步骤见仓库根目录的 [INSTALL.md](../../INSTALL.md)。这里只列执行顺序。

## 1. 系统工具

- Python 3.11
- Node.js 20+
- ffmpeg 7+
- Chrome 或 Edge
- NVIDIA 驱动（CUDA 12.6）

## 2. Python 环境

```powershell
conda env create -f env\aivideo.yml
conda env create -f env\indextts.yml
```

## 3. 渲染器

```powershell
cd engine
npm install --no-audit --no-fund
```

浏览器自动探测；也可以：

```powershell
$env:PLAYWRIGHT_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

## 4. 模型与音色

- `vendor/index-tts/checkpoints/` 放 IndexTTS2 权重
- `voices/<名字>/sample.wav` 放克隆音色

## 5. 验证

```powershell
python tools\lemo.py doctor
python tools\pipeline.py status pipeline-showcase
```

## 6. 第一条

```powershell
python tools\pipeline.py render pipeline-showcase
```

## 常见问题

- 找不到 indextts：设置 `INDEXTTS_PYTHON`
- 找不到浏览器：设置 `PLAYWRIGHT_CHROME`
- 渲染报 module not found：回 `engine/` 重新 `npm install`
- 配音极慢：IndexTTS2 约 18 倍实时，首次全量；之后按句缓存
