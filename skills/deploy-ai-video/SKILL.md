---
name: deploy-ai-video
description: 在新机器上从零部署 AI-v 短视频生成工程（两个 conda 环境、IndexTTS2 模型、HyperFrames 渲染链），或在环境损坏后重建、诊断安装问题。当用户说「换电脑怎么装」「环境坏了」「重新部署这个项目」「安装 IndexTTS2 / FunASR」时使用。
---

# 部署 AI-v 视频工程

把 `AI-v` 项目从零装到「能出片」。全程 Windows，约 40 分钟，主要时间花在下载。

## 判断意图

| 用户说 | 做什么 |
|---|---|
| 换电脑 / 新机器部署 | 走「全新安装」 |
| 环境坏了、import 报错 | 先跑 `scripts/doctor.ps1`，再按 `references/troubleshooting.md` 修 |
| 只想配音不要视频 | 只装 `indextts` 环境 |
| 只想用微软音色出片 | 只装 `aivideo` 环境 |

## 全新安装（按顺序）

### 1. 检查基础软件

```powershell
node -v; npm -v; ffmpeg -version; conda --version
```

四条都要有输出。缺 Node / FFmpeg 先装：

```powershell
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
```

Chrome 必须存在（渲染引擎默认用系统 Chrome）。

### 2. 一键装环境

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\bootstrap.ps1
```

脚本会做：建两个 conda 环境 → 装 CUDA torch → 装 IndexTTS2 本体 → 装 FunASR → 修 protobuf → 下模型 → 体检。

**大约 30–60 分钟，中途不要 Ctrl+C。**

### 3. 手动补的三件事（脚本做不了）

见 `references/install.md` 的「手动步骤」一节：

1. VS Code 解释器指向 `aivideo`
2. 中文字体（仅 Linux）
3. 首次配音会额外下载 5 GB 辅助模型

### 4. 验证

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\doctor.ps1
```

全绿才算装好。

## 硬性规则（写错会静默失败）

1. **torch 必须带 `--index-url https://download.pytorch.org/whl/cu126`**，否则装成 CPU 版，`cuda.is_available()` 为 False。
2. **装完 funasr 必须立刻降 protobuf**：`pip install "protobuf==3.19.6"`，否则 IndexTTS2 报 `Descriptors cannot be created directly`。
3. **IndexTTS2 是本地包**，必须 `cd vendor\index-tts && pip install -e .`，YAML 里没有它。
4. **模型不放仓库**，占 10.6 GB，用脚本下载或从旧机器拷贝。
5. **conda 环境不能直接拷贝**，必须重建。

## 环境规格

| | aivideo | indextts |
|---|---|---|
| Python | 3.13 | 3.11 |
| 大小 | 0.31 GB | 7.97 GB |
| 关键包 | edge-tts | torch 2.8+cu126、torchaudio、IndexTTS2、funasr |
| 显卡 | 不需要 | 需要，6 GB 显存 |

## 参考文档

- `references/install.md` — 完整安装步骤、YAML 还原、镜像地址
- `references/troubleshooting.md` — 症状 → 原因 → 修复
- `assets/aivideo.yml` / `assets/indextts.yml` — 环境快照

## 完成后告诉用户什么

1. 两个环境是否都建好
2. `doctor.ps1` 是否全过
3. 第一条出片命令
4. 还缺什么（模型没下、字体没装、显卡不可用）
