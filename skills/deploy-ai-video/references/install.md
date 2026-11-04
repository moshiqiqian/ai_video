# 完整安装步骤

适用于 Windows 10/11。macOS / Linux 见文末。

## 0. 前置软件

| 软件 | 检查命令 | 安装 |
|---|---|---|
| Miniconda | `conda --version` | https://docs.conda.io/en/latest/miniconda.html |
| Node.js 18+ | `node -v` | `winget install OpenJS.NodeJS.LTS` |
| FFmpeg | `ffmpeg -version` | `winget install Gyan.FFmpeg` |
| Chrome | 打开浏览器 | https://www.google.com/chrome/ |
| Git（可选） | `git --version` | `winget install Git.Git` |

装完**重开终端**，PATH 才会生效。

---

## 1. 建 `aivideo` 环境（出片）

```powershell
conda create -n aivideo python=3.13 -y
conda activate aivideo
pip install edge-tts
python -c "import edge_tts; print('ok')"
```

只有 edge-tts。**不要装 torch**——这个环境不做 GPU 推理。

---

## 2. 建 `indextts` 环境（配音 + 转写）

### 2.1 建环境

```powershell
conda create -n indextts python=3.11 -y
conda activate indextts
```

### 2.2 CUDA 版 torch

```powershell
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
```

验证：

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

期望 `True NVIDIA GeForce RTX 4060 Laptop GPU`（型号随机器）。

### 2.3 IndexTTS2 本体

```powershell
cd 项目路径\vendor\index-tts
pip install -e .
cd ..\..
```

耗时 5–10 分钟，会拉 transformers、librosa、numba 等三十多个包。

### 2.4 转写工具

```powershell
pip install funasr modelscope
```

### 2.5 修 protobuf（必做）

```powershell
pip install "protobuf==3.19.6"
```

不做这一步，IndexTTS2 启动时报：

```
TypeError: Descriptors cannot be created directly.
```

### 2.6 验证

```powershell
python -c "import torch, funasr; from indextts.infer_v2 import IndexTTS2; print('ok')"
```

---

## 3. 模型权重

检查：

```powershell
dir vendor\index-tts\checkpoints
```

应存在：`gpt.pth`(3.3 GB)、`s2mel.pth`(1.1 GB)、`qwen0.6bemo4-merge\`(1.1 GB)。

缺失则下载（国内用 hf-mirror）：

```powershell
$base = "https://hf-mirror.com/IndexTeam/IndexTTS-2/resolve/main/"
$files = @(
  "config.yaml","gpt.pth","s2mel.pth","bpe.model","wav2vec2bert_stats.pt","feat1.pt","feat2.pt",
  "qwen0.6bemo4-merge/config.json","qwen0.6bemo4-merge/model.safetensors",
  "qwen0.6bemo4-merge/tokenizer.json","qwen0.6bemo4-merge/merges.txt",
  "qwen0.6bemo4-merge/vocab.json","qwen0.6bemo4-merge/special_tokens_map.json",
  "qwen0.6bemo4-merge/tokenizer_config.json","qwen0.6bemo4-merge/added_tokens.json"
)
New-Item -ItemType Directory -Force vendor\index-tts\checkpoints | Out-Null
foreach ($f in $files) {
  curl.exe -L --fail -C - -o "vendor\index-tts\checkpoints\$f" ($base + $f)
}
```

首次运行 IndexTTS2 还会下载约 5 GB 辅助模型到 `checkpoints\hf_cache\`（w2v-bert、bigvgan、semantic_codec）。这一步没有进度条，看起来像卡住，耐心等。

---

## 4. 用 YAML 还原（可选）

仓库 `env/` 下有环境快照：

```powershell
conda env create -f env/aivideo.yml
conda env create -f env/indextts.yml
conda activate indextts
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
cd vendor\index-tts; pip install -e .; cd ..\..
pip install "protobuf==3.19.6"
```

YAML 里没有本地包和 CUDA torch，最后几行必须补。

---

## 5. VS Code

`.vscode/settings.json`：

```json
{ "python.defaultInterpreterPath": "C:\\Users\\<用户名>\\anaconda3\\envs\\aivideo\\python.exe" }
```

打开项目后右下角显示 `aivideo`。

---

## 6. 验证

```powershell
conda activate aivideo
python tools\make.py --help
npx hyperframes@0.9.0 --version
ffmpeg -version
```

---

## 其他系统

### macOS

- 字体用系统自带的 PingFang SC（代码已包含）
- torch 换成 `--index-url https://download.pytorch.org/whl/cpu`（无 CUDA），IndexTTS2 会走 MPS，速度慢 3–5 倍
- FFmpeg：`brew install ffmpeg`

### Linux

- 字体必须装：`sudo apt install fonts-noto-cjk`，否则中文全是方块
- CUDA 版 torch 同上（cu126）
- HyperFrames 需要 Chromium：`sudo apt install chromium-browser` 或用 Playwright 下载

### 镜像替换

| 原地址 | 国内替代 |
|---|---|
| `huggingface.co` | `hf-mirror.com` |
| `github.com`（下载 zip） | `ghproxy.net/https://github.com/...` |
| `download.pytorch.org` | 直连较慢，可等待或换时段 |
