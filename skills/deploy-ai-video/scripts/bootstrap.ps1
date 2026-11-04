<#
.SYNOPSIS
    一键部署 AI-v 视频工程（Windows）。

.DESCRIPTION
    检查基础软件 -> 建两个 conda 环境 -> 装 CUDA torch -> 装 IndexTTS2 本体
    -> 装 FunASR -> 修 protobuf -> 下模型 -> 体检。

    可重复执行：已完成的步骤会跳过。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\bootstrap.ps1
    powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -SkipModels
#>
param(
    [switch]$SkipModels,
    [switch]$SkipEnvs
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root      = Resolve-Path (Join-Path $scriptDir "..\..\..")
$envDir    = Join-Path $root "env"
$vendor    = Join-Path $root "vendor\index-tts"
$ckpt      = Join-Path $vendor "checkpoints"

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "  [XX] $msg" -ForegroundColor Red }

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Step "1/9 检查基础软件"
$missing = @()
if (-not (Have node))   { $missing += "Node.js   winget install OpenJS.NodeJS.LTS" }
if (-not (Have ffmpeg)) { $missing += "FFmpeg    winget install Gyan.FFmpeg" }
if (-not (Have conda))  { $missing += "Miniconda https://docs.conda.io/en/latest/miniconda.html" }
if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Fail $_ }
    Fail "缺基础软件，装完重开终端再跑本脚本"
    exit 1
}
Ok "node / ffmpeg / conda 都在"

Step "2/9 建 aivideo 环境"
$pyAivideo = "$env:USERPROFILE\anaconda3\envs\aivideo\python.exe"
if (Test-Path $pyAivideo) { Ok "已存在，跳过" }
elseif (-not $SkipEnvs) {
    conda create -n aivideo python=3.13 -y | Out-Null
    if (-not (Test-Path $pyAivideo)) { Fail "创建失败"; exit 1 }
    Ok "已创建"
}
& $pyAivideo -m pip install -q edge-tts
Ok "edge-tts 就绪"

Step "3/9 建 indextts 环境"
$pyIndextts = "$env:USERPROFILE\anaconda3\envs\indextts\python.exe"
if (Test-Path $pyIndextts) { Ok "已存在，跳过" }
elseif (-not $SkipEnvs) {
    conda create -n indextts python=3.11 -y | Out-Null
    if (-not (Test-Path $pyIndextts)) { Fail "创建失败"; exit 1 }
    Ok "已创建"
}

Step "4/9 安装 CUDA 版 torch"
$torchOk = & $pyIndextts -c "import torch; print(torch.cuda.is_available())" 2>$null
if ($torchOk -match "True") { Ok "torch 已就绪，GPU 可用" }
else {
    & $pyIndextts -m pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
    $torchOk = & $pyIndextts -c "import torch; print(torch.cuda.is_available())" 2>$null
    if ($torchOk -match "True") { Ok "安装完成，GPU 可用" } else { Warn "GPU 不可用，检查驱动或显卡" }
}

Step "5/9 安装 IndexTTS2 本体"
if (-not (Test-Path (Join-Path $vendor "pyproject.toml"))) {
    Warn "vendor\index-tts 不存在，从镜像下载源码"
    New-Item -ItemType Directory -Force (Split-Path $vendor -Parent) | Out-Null
    $tmp = Join-Path $env:TEMP "index-tts.zip"
    curl.exe -L --fail -o $tmp "https://ghproxy.net/https://github.com/index-tts/index-tts/archive/refs/heads/main.zip"
    if ($LASTEXITCODE -ne 0) { Fail "下载源码失败，检查网络或用 ghproxy 手动下载"; exit 1 }
    Expand-Archive $tmp -DestinationPath (Join-Path $env:TEMP "itt") -Force
    Move-Item (Join-Path $env:TEMP "itt\index-tts-main") $vendor
    Ok "源码就绪"
}
$hasTts = & $pyIndextts -c "import indextts; print('yes')" 2>$null
if ($hasTts -match "yes") { Ok "已安装，跳过" }
else {
    Push-Location $vendor
    & $pyIndextts -m pip install -e .
    Pop-Location
    Ok "安装完成"
}

Step "6/9 安装转写工具"
& $pyIndextts -m pip install -q funasr modelscope
Ok "funasr / modelscope 就绪"

Step "7/9 修 protobuf"
& $pyIndextts -m pip install -q "protobuf==3.19.6"
$pb = & $pyIndextts -c "import google.protobuf as p; print(p.__version__)" 2>$null
if ($pb.Trim() -eq "3.19.6") { Ok "protobuf = 3.19.6" } else { Warn "protobuf 版本异常：$pb" }

Step "8/9 检查模型"
$need = @("config.yaml","gpt.pth","s2mel.pth","bpe.model","wav2vec2bert_stats.pt")
$miss = @()
foreach ($f in $need) { if (-not (Test-Path (Join-Path $ckpt $f))) { $miss += $f } }
if ($miss.Count -eq 0) { Ok "模型文件齐全" }
elseif ($SkipModels) { Warn "缺 $($miss -join ', ')（已按参数跳过下载）" }
else {
    Warn "缺 $($miss -join ', ')，开始下载（约 5.5 GB，国内走 hf-mirror）"
    $base = "https://hf-mirror.com/IndexTeam/IndexTTS-2/resolve/main/"
    $files = @(
      "config.yaml","gpt.pth","s2mel.pth","bpe.model","wav2vec2bert_stats.pt","feat1.pt","feat2.pt",
      "qwen0.6bemo4-merge/config.json","qwen0.6bemo4-merge/model.safetensors",
      "qwen0.6bemo4-merge/tokenizer.json","qwen0.6bemo4-merge/merges.txt",
      "qwen0.6bemo4-merge/vocab.json","qwen0.6bemo4-merge/special_tokens_map.json",
      "qwen0.6bemo4-merge/tokenizer_config.json","qwen0.6bemo4-merge/added_tokens.json",
      "qwen0.6bemo4-merge/chat_template.jinja"
    )
    New-Item -ItemType Directory -Force $ckpt | Out-Null
    foreach ($f in $files) {
        $out = Join-Path $ckpt $f
        $dir = Split-Path $out -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
        if ((Test-Path $out) -and ((Get-Item $out).Length -gt 1024)) { continue }
        curl.exe -L --fail -C - -o $out ($base + $f)
        if ($LASTEXITCODE -ne 0) { Warn "下载失败：$f（可重跑本脚本续传）" }
    }
}

Step "9/9 体检"
& (Join-Path $scriptDir "doctor.ps1")

Write-Host "`n部署结束。下一步：" -ForegroundColor Cyan
Write-Host "  conda activate aivideo"
Write-Host "  python tools\make.py --help"
