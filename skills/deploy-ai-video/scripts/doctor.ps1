<#
.SYNOPSIS
    体检：检查 AI-v 工程的运行条件。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File skills\deploy-ai-video\scripts\doctor.ps1
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root      = Resolve-Path (Join-Path $scriptDir "..\..\..")
$pyAivideo = "$env:USERPROFILE\anaconda3\envs\aivideo\python.exe"
$pyIndextts = "$env:USERPROFILE\anaconda3\envs\indextts\python.exe"
$pass = 0; $fail = 0

function Check($name, $ok, $hint = "") {
    if ($ok) { Write-Host ("  [OK] {0}" -f $name) -ForegroundColor Green; $script:pass++ }
    else {
        Write-Host ("  [XX] {0}{1}" -f $name, $(if ($hint) { "  -> $hint" } else { "" })) -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n=== 基础软件 ===" -ForegroundColor Cyan
Check "Node.js" ([bool](Get-Command node -ErrorAction SilentlyContinue)) "winget install OpenJS.NodeJS.LTS"
Check "FFmpeg"  ([bool](Get-Command ffmpeg -ErrorAction SilentlyContinue)) "winget install Gyan.FFmpeg"
Check "conda"   ([bool](Get-Command conda -ErrorAction SilentlyContinue)) "装 Miniconda"

Write-Host "`n=== aivideo 环境 ===" -ForegroundColor Cyan
if (Test-Path $pyAivideo) {
    Check "解释器存在" $true
    $e = & $pyAivideo -c "import edge_tts; print('ok')" 2>$null
    Check "edge-tts 可导入" ($e -match "ok") "pip install edge-tts"
} else { Check "aivideo 环境" $false "conda create -n aivideo python=3.13 -y" }

Write-Host "`n=== indextts 环境 ===" -ForegroundColor Cyan
if (Test-Path $pyIndextts) {
    Check "解释器存在" $true
    $t = & $pyIndextts -c "import torch; print(torch.__version__, torch.cuda.is_available())" 2>$null
    Check "torch 可导入" ($t -match "2\.") "重装 CUDA 版 torch"
    Check "GPU 可用" ($t -match "True") "装 cu126 版 torch"
    $f = & $pyIndextts -c "import funasr; print('ok')" 2>$null
    Check "funasr 可导入" ($f -match "ok") "pip install funasr modelscope"
    $i = & $pyIndextts -c "from indextts.infer_v2 import IndexTTS2; print('ok')" 2>$null
    Check "IndexTTS2 可导入" ($i -match "ok") "cd vendor\index-tts; pip install -e ."
    $p = & $pyIndextts -c "import google.protobuf as p; print(p.__version__)" 2>$null
    Check "protobuf = 3.19.6" ($p.Trim() -eq "3.19.6") "pip install `"protobuf==3.19.6`""
} else { Check "indextts 环境" $false "conda create -n indextts python=3.11 -y" }

Write-Host "`n=== 模型 ===" -ForegroundColor Cyan
$ckpt = Join-Path $root "vendor\index-tts\checkpoints"
foreach ($f in @("gpt.pth","s2mel.pth")) {
    $p = Join-Path $ckpt $f
    $ok = (Test-Path $p) -and ((Get-Item $p).Length -gt 100MB)
    Check $f $ok "用 bootstrap.ps1 下载"
}
$hf = Join-Path $ckpt "hf_cache"
Check "hf_cache（首次运行自动下）" (Test-Path $hf) "首次配音时会生成，可忽略"

Write-Host "`n=== 项目文件 ===" -ForegroundColor Cyan
foreach ($f in @("tools\make.py","tools\voice.py","tools\media.py","tools\transcribe.py","content")) {
    $exists = Test-Path (Join-Path $root $f)
    if ($f -eq "content") { continue }
    Check $f $exists ""
}

Write-Host "`n=== 渲染链 ===" -ForegroundColor Cyan
$npmOk = [bool](Get-Command npx -ErrorAction SilentlyContinue)
Check "npx 可用" $npmOk "装 Node.js"
$chromePaths = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
Check "Chrome 已安装" ([bool]($chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1)) "装 Chrome"

$total = $pass + $fail
Write-Host ("`n结果：{0}/{1} 通过" -f $pass, $total) -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
if ($fail -eq 0) { Write-Host "环境就绪，可以出片。" -ForegroundColor Green }
else { Write-Host "有 $fail 项未通过，按提示修复后重跑。" -ForegroundColor Yellow }
exit $fail
