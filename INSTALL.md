# 瀹夎

鐩爣锛氫竴鍙?Windows 鏈哄櫒锛岃兘璺?`tools/pipeline.py render`銆?
## 1. 绯荤粺宸ュ叿

| 宸ュ叿 | 鐗堟湰 | 鐢ㄩ€?|
|---|---|---|
| Python | 3.11 | 娴佹按绾裤€侀厤涔愩€佹贩闊?|
| Node.js | 20+ | 閫愬抚娓叉煋鍣?|
| ffmpeg | 7+ | 鎴浘鍚堟垚銆佹贩闊炽€佸搷搴﹀綊涓€ |
| Chrome / Edge | 浠绘剰杩戞湡鐗堟湰 | 鏃犲ご鎴浘 |
| NVIDIA 椹卞姩 | CUDA 12.6 | IndexTTS2 |

妫€鏌ワ細

```powershell
python --version
node --version
ffmpeg -version
```

## 2. Python 鐜

```powershell
conda env create -f env\aivideo.yml
conda env create -f env\indextts.yml
```

- `aivideo`锛歯umpy銆乻oundfile銆乪dge-tts锛堝鐢級锛岃窇娴佹按绾垮拰閰嶄箰
- `indextts`锛歵orch 2.8 + cu126銆両ndexTTS2銆丗unASR

## 3. 娓叉煋鍣ㄤ緷璧?
```powershell
cd engine
npm install --no-audit --no-fund
```

闇€瑕佹祻瑙堝櫒锛氶粯璁よ嚜鍔ㄦ壘 Chrome / Edge锛涗篃鍙互鎸囧畾

```powershell
$env:PLAYWRIGHT_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

## 4. IndexTTS2 妯″瀷

妯″瀷鏀惧湪 `vendor/index-tts/checkpoints/`锛岃嚦灏戝寘鍚細

```
config.yaml
gpt.pth
s2mel.pth
...
```

闊宠壊鏍锋湰鏀惧湪 `voices/<鍚嶅瓧>/sample.wav`锛屽苟鍦?`voices/<鍚嶅瓧>/meta.json` 閲屽啓鍩烘湰淇℃伅銆?
```powershell
python tools\voice.py list
```

## 5. 楠岃瘉

```powershell
python tools\lemo.py doctor
python tools\pipeline.py status pipeline-showcase
```

姝ｅ父杈撳嚭搴旇兘鐪嬪埌 engine銆乶ode銆乫fmpeg銆乧hrome 閮?OK銆?
## 6. 鍑虹涓€鏉?
```powershell
python tools\pipeline.py render pipeline-showcase
start videos\pipeline-showcase\output\render.mp4
```

## 甯歌闂

**鎵句笉鍒?indextts 鐜**
璁剧疆 `INDEXTTS_PYTHON` 鎸囧悜瀹冪殑 `python.exe`銆?
**Chrome 鍚姩澶辫触**
`PLAYWRIGHT_CHROME` 鎸囧悜 `chrome.exe` 鎴?`msedge.exe`銆?
**娓叉煋寰堟參**
`--workers 4`锛?080p 48 绉掔害 1152 甯э紝瑙嗘満鍣ㄥ嚑鍗佺鍒板嚑鍒嗛挓銆?
**閰嶉煶寰堟參**
IndexTTS2 绾?18 鍊嶅疄鏃躲€傜涓€娆″叏閲忥紝涔嬪悗鎸夊彞缂撳瓨锛屽彧琛ユ敼鍔ㄧ殑鍙ュ瓙銆?
