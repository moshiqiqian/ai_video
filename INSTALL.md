# INSTALL · 交给 AI 的安装指令

> 用法：把这份文件和整个项目一起交给 AI，然后说一句
> **「按 INSTALL.md 安装这个项目」**。
> 下面的内容就是写给 AI 执行的全部信息。

---

## 给 AI 的目标

把本仓库安装到「能出片」状态。

**验收标准**：`doctor.ps1` 输出 `22/22 通过`，且能渲染出一个大于 1 MB 的 mp4。

---

## 执行步骤

### 0. 先注册 skill

本项目依赖八个 skill：

| Skill | 作用 |
|---|---|
| `video-pipeline` | 六阶段总控 |
| `video-brief` | 立项、导入文稿 |
| `video-script` | 文案 |
| `video-storyboard` | 分镜 |
| `video-assets` | 素材 |
| `video-voice` | 配音 |
| `video-render` | 渲染与质检 |
| `deploy-ai-video` | 部署与排错（本文件对应的技能） |

把仓库里的这些目录复制到当前 Agent 的 skills 目录：

```powershell
# OpenCode
$dst = "$env:USERPROFILE\.config\opencode\skills"
Copy-Item skills\* $dst -Recurse -Force
```

| Agent | skills 目录 |
|---|---|
| OpenCode | `~\.config\opencode\skills\` |
| Claude Code | `~\.claude\skills\` |
| 其他 | 见该 Agent 文档；不支持目录约定时，后续对话直接用路径引用 `skills/<名字>/SKILL.md` |

注册后确认每个目录里都有 `SKILL.md`：

```powershell
Get-ChildItem "$env:USERPROFILE\.config\opencode\skills\video-*" | Select-Object Name
```

### 0.5 读三份技能文档

```
skills/deploy-ai-video/SKILL.md
skills/deploy-ai-video/references/install.md
skills/deploy-ai-video/references/troubleshooting.md
```

没有 `skills/` 目录 → 仓库不完整，停止并告知用户。

### 1. 检查前置软件

```powershell
node -v; npm -v; ffmpeg -version; conda --version
```

- 全有输出 → 下一步
- 缺 Node.js → `winget install OpenJS.NodeJS.LTS`
- 缺 FFmpeg → `winget install Gyan.FFmpeg`
- 缺 conda → 让用户装 Miniconda，装完**重开终端**

装完系统级软件必须重开终端，否则 PATH 不生效。

### 2. 一键安装

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\bootstrap.ps1
```

- 30–60 分钟，主要花在下载：torch 2.5 GB、模型 5.5 GB
- 已有 `vendor\index-tts\checkpoints` 时可加 `-SkipModels`
- 中断可重跑，支持续传

### 3. 验收

```powershell
powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\doctor.ps1
```

- `22/22 通过` → 进入第 4 步
- 有失败项 → 按每项后面的 `->` 修复后重跑
- 同一项连续失败 2 次 → 查 `references/troubleshooting.md`，仍不行如实告知用户

### 4. 真实出片验证

```powershell
conda activate aivideo
python tools\make.py LangChain全家桶 --reuse-audio --subtitles --render
```

若 `videos/LangChain全家桶/audio/` 下没有配音，改用（约 10 分钟，含 AI 配音）：

```powershell
python tools\make.py LangChain全家桶 --engine indextts --voice-pack xiaoxiao --transcribe --subtitles --render
```

成功标志：`videos/LangChain全家桶/render.mp4` 存在且大于 1 MB。

---

## 六条硬规则（违反会静默失败）

1. **CUDA torch 必须带 `--index-url https://download.pytorch.org/whl/cu126`**
   否则装成 CPU 版，`torch.cuda.is_available()` 为 False，且装的时候不报错。

2. **装完 funasr 必须立刻 `pip install "protobuf==3.19.6"`**
   否则 IndexTTS2 启动报 `Descriptors cannot be created directly`。

3. **IndexTTS2 是本地包**：`cd vendor\index-tts; pip install -e .`
   YAML 里没有它，必须单独装。

4. **模型不进仓库**（10.6 GB），必须下载或从旧机器拷贝。

5. **conda 环境不能直接拷贝**，必须在目标机重建。

6. **`.ps1` 脚本必须是 UTF-8 with BOM**，否则 PowerShell 5.1 报语法错误。

---

## 环境规格（供判断是否装对）

| 项 | aivideo | indextts |
|---|---|---|
| Python | 3.13 | 3.11 |
| 大小 | 约 0.3 GB | 约 8 GB |
| 关键包 | edge-tts | torch 2.8+cu126、torchaudio、IndexTTS2、funasr |
| 需要显卡 | 否 | 是，6 GB 显存 |

---

## 装完必须回答用户这四件事

1. 八个 skill 是否注册（`video-pipeline` / `video-brief` / `video-script` / `video-storyboard` / `video-assets` / `video-voice` / `video-render` / `deploy-ai-video`）
2. 两个 conda 环境是否建好（`aivideo` / `indextts`）
3. `doctor.ps1` 结果：多少项通过、哪些失败
4. 验证视频是否渲染成功、路径在哪
5. 还缺什么（模型没下完、显卡不可用、字体缺失、磁盘不足）

---

## 常见失败与处理

| 现象 | 处理 |
|---|---|
| `torch.cuda.is_available()` 为 False | 重装 CUDA 版 torch（硬规则 1） |
| `Descriptors cannot be created directly` | 降 protobuf（硬规则 2） |
| `No module named 'indextts'` | 回 `vendor\index-tts` 执行 `pip install -e .` |
| `.ps1` 报语法错误 / 中文乱码 | 文件不是 UTF-8 BOM，重存 |
| 下载超时 | HuggingFace 换 `hf-mirror.com`，GitHub 换 `ghproxy.net` 前缀 |
| 渲染画面全黑 | GSAP 的 CDN 不通，改用本地 gsap.min.js |
| 中文变方块 | Windows 自带雅黑；Linux 装 `fonts-noto-cjk` |

更完整的排错见 `skills/deploy-ai-video/references/troubleshooting.md`。
