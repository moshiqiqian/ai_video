# 故障排查

按现象查。

## 环境 / 依赖

| 现象 | 原因 | 修复 |
|---|---|---|
| `ModuleNotFoundError: edge_tts` | 没激活 aivideo | `conda activate aivideo` |
| `ModuleNotFoundError: indextts` | 没装本体 | `cd vendor\index-tts && pip install -e .` |
| `torch.cuda.is_available()` 为 False | 装了 PyPI 的 CPU 版 | 重装：`pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu126` |
| `Descriptors cannot be created directly` | protobuf 被 funasr 升到 7.x | `pip install "protobuf==3.19.6"` |
| `funasr` 报 `tensorboardX requires protobuf>=3.20` | 只是警告 | 忽略，推理不用 tensorboardX |
| `CondaHTTPError` / 下载超时 | 网络 | 换清华 conda 源，或重试 |
| 建环境时 `PackagesNotFoundError` | YAML 里的 build 号已下架 | 用 `--no-builds` 版本或按 install.md 手动装 |

## 配音（IndexTTS2）

| 现象 | 原因 | 修复 |
|---|---|---|
| `CUDA out of memory` | 显存不足 | 关掉其他 GPU 程序；确认 `use_fp16=True` |
| 首次运行卡住不动 | 在下载 hf_cache（5 GB） | 等待，或看 `checkpoints\hf_cache` 是否在变大 |
| 生成的声音不像参考 | 参考样本太短/有噪音 | 换 5–10 秒干净录音 |
| 生成很慢 | 正常，RTF≈8–10 | 51 秒文案约 7 分钟 |
| 找不到音色 | voice_pack 名字错 | `python tools\voice.py list` |

## 转写（FunASR）

| 现象 | 原因 | 修复 |
|---|---|---|
| 英文词识别成别的（LangChain→launchen） | 中文模型对英文品牌弱 | 不影响时间戳；字幕用脚本原文 |
| 字幕条数为 0 | 时间戳与文本对不齐 | 更新 `transcribe.py`，或按句均分兜底 |
| 转写很慢 | CPU 模式 | `--device cuda` |

## 渲染（HyperFrames）

| 现象 | 原因 | 修复 |
|---|---|---|
| 画面全黑 | GSAP 的 CDN 被墙 | 把 gsap.min.js 下到本地并改引用 |
| 中文显示成方块 | 缺字体 | Windows 用微软雅黑；Linux 装 fonts-noto-cjk |
| 视频没声音 | `<audio>` 缺 id 或路径错 | 检查生成的 index.html |
| `npx: command not found` | Node 没装/没重启终端 | 重开终端 |
| 渲染 OOM | 多 worker 抢内存 | `-w 1` 或 `--low-memory-mode` |
| 首帧全黑 | 标题从 opacity 0 开始 | 让首帧就有内容 |
| `text_occluded` | 字幕盖住图片说明 | 给图片区留 `padding-bottom` |

## 出片流程

| 现象 | 原因 | 修复 |
|---|---|---|
| 画面比声音早/晚 | 分镜边界不准 | 用 `start_at_sentence` 代替 `hint` |
| 一屏多行逐步出现对不上 | 行是按平均时间排的 | 每屏只放 1–2 行，或拆成多个镜头 |
| 换了音频后时间全乱 | 时间轴没重算 | 去掉 `--reuse-audio` |
| `--voice-pack` 报错 | 声音库没有该音色 | `python tools\voice.py add 名字 录音.wav` |
