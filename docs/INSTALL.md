# 安装

目标：一台 Windows 机器，能跑 `tools/pipeline.py render`。

## 1. 系统工具

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | 3.13（aivideo）/ 3.11（indextts） | 流水线、配乐、混音、配音 |
| Node.js | 20+ | 逐帧渲染器 |
| ffmpeg | 7+ | 截图合成、混音、响度归一 |
| Chrome / Edge | 任意近期版本 | 无头截图 |
| NVIDIA 驱动 | CUDA 12.6 | IndexTTS2 |

检查：

```powershell
python --version
node --version
ffmpeg -version
```

## 2. Python 环境

```powershell
conda env create -f env\aivideo.yml
conda env create -f env\indextts.yml
```

- `aivideo`：Python 3.13，numpy、soundfile，跑流水线和配乐
- `indextts`：Python 3.11，torch 2.8 + cu126、IndexTTS2

`indextts` 建好后，还需要把 IndexTTS2 本体装进环境：

```powershell
conda activate indextts
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
cd vendor\index-tts
pip install -e .
```

## 3. 渲染器依赖

```powershell
cd engine
npm install --no-audit --no-fund
```

浏览器默认自动找 Chrome / Edge；也可以指定：

```powershell
$env:PLAYWRIGHT_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

## 4. IndexTTS2 模型

模型放在 `vendor/index-tts/checkpoints/`，至少包含：

```
config.yaml
gpt.pth
s2mel.pth
hf_cache/
```

音色样本放在 `voices/<名字>/sample.wav`，并在 `voices/<名字>/meta.json` 里写基本信息。

```powershell
python tools\voice.py list
```

## 5. 验证

```powershell
python tools\lemo.py doctor
python tools\pipeline.py status pipeline-showcase
```

正常输出应能看到 engine、node、ffmpeg、chrome 都 OK。

## 6. 出第一条

```powershell
python tools\pipeline.py render pipeline-showcase
start videos\pipeline-showcase\output\render.mp4
```

## 常见问题

**找不到 indextts 环境**
设置 `INDEXTTS_PYTHON` 指向它的 `python.exe`。

**Chrome 启动失败**
`PLAYWRIGHT_CHROME` 指向 `chrome.exe` 或 `msedge.exe`。

**渲染很慢**
`--workers 4`；1080p 48 秒约 1152 帧，视机器几十秒到几分钟。

**配音很慢**
IndexTTS2 约 8–18 倍实时。第一次全量，之后按句缓存，只补改动的句子。
