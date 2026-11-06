# AI-v 路 鐢ㄤ唬鐮佺敓鎴愮煭瑙嗛

涓€鍙ヨ瘽鏂囨锛屽叚姝ョ‘璁わ紝浜у嚭涓€鏉″甫閰嶉煶銆侀厤涔愩€佸瓧骞曠殑 MP4銆?鐢婚潰涓嶆槸妯℃澘锛屾槸姣忎竴甯х畻鍑烘潵鐨勩€?
```
鏂囨 鈫?閫愬彞閰嶉煶 鈫?鏃堕棿杞?鈫?render(t) 鐢婚潰 鈫?閫愬抚鎴浘 鈫?娣烽煶 鈫?MP4
```

鍏ㄧ▼鏈満杩愯锛屼笉璋冪敤浠讳綍鍦ㄧ嚎鐢熸垚 API銆?
## 鍏

```
brief 鈫?script 鈫?storyboard 鈫?voice 鈫?mix 鈫?render
绔嬮」     鏂囨      鍒嗛暅          閰嶉煶     娣烽煶    娓叉煋
```

姣忎竴姝ラ兘鐣欎笅鏂囦欢锛岄兘瑕佷綘鐐瑰ご鎵嶇户缁紱涓婃父鏀逛簡锛屼笅娓歌嚜鍔ㄦ爣璁拌繃鏈熴€?
| 姝?| 浜х墿 | 璋佹潵鍋?|
|---|---|---|
| 绔嬮」 | `project.json`銆乣source/brief.md` | 閫夐鏍笺€佹椂闀裤€佽瑷€ |
| 鏂囨 | `build/lines.json` | 鎸夊彞鎷嗗紑 |
| 鍒嗛暅 | `build/timeline.json` | 姣忓彞鐨勮捣姝㈡椂闂?|
| 閰嶉煶 | `film/audio/l1.wav鈥銆乣voice.wav` | IndexTTS2 鍏嬮殕闊宠壊 |
| 娣烽煶 | `music.wav`銆乣mix.wav` | 閰嶄箰 + 渚ч摼锛屸垝14 LUFS |
| 娓叉煋 | `output/render.mp4`銆乣qa/` | 閫愬抚鎴浘 + ffmpeg |

## 蹇€熷紑濮?
```powershell
python tools\pipeline.py start demo
python tools\pipeline.py brief demo --style swiss-motion --duration 48 --language zh --topic "涓婚"
python tools\pipeline.py script demo --file source\script.txt
python tools\pipeline.py storyboard demo
python tools\pipeline.py voice demo
python tools\pipeline.py mix demo
python tools\pipeline.py render demo
```

鐢婚潰鏂囦欢鍦?`videos/<鍚嶅瓧>/film/`锛氫竴涓?`index.html`銆佷竴涓?`main.js`锛屾毚闇诧細

```js
window.render = t => { ... };
window.DUR = 48;
window.READY = true;
```

## 绀轰緥

`videos/pipeline-showcase/`锛?8 绉掞紝鍏樁娈垫祦绋嬪浘锛屼腑鏂囨梺鐧?+ 绋嬪簭鍖栭厤涔愩€?
```powershell
start videos\pipeline-showcase\output\render.mp4
```

## 渚濊禆

| 鍔熻兘 | 渚濊禆 |
|---|---|
| 鐢婚潰娓叉煋 | Node 20+銆乣engine/` 閲岀殑 playwright-core + three銆丆hrome 鎴?Edge銆乫fmpeg |
| 閰嶉煶 | conda 鐜 `indextts`锛坱orch 2.8 + CUDA锛夈€乣vendor/index-tts/`銆乣voices/<闊宠壊>/sample.wav` |
| 閰嶄箰 / 娣烽煶 | Python `aivideo` 鐜锛坣umpy銆乻oundfile锛夈€乫fmpeg |
| 娴佹按绾?| Python 3.11锛堝彧鐢ㄦ爣鍑嗗簱锛?|
| 瀛楀箷 | 鐢诲湪 canvas 閲岋紝鏃犻澶栦緷璧?|

瀹屾暣瀹夎瑙?[INSTALL.md](INSTALL.md)銆傛祦绋嬬粏鑺傝 [PIPELINE.md](PIPELINE.md)銆?
## 鐩綍

```
engine/           娓叉煋鍣?+ 66 浠介鏍艰鑼冿紙vendored锛孧IT锛?tools/            pipeline.py / lemo.py / say_lines.py / music_bed.py
videos/<鐗囧瓙>/     source build film output qa
voices/           鍏嬮殕闊宠壊鏍锋湰
vendor/index-tts/ IndexTTS2 妯″瀷
env/              conda 鐜瀹氫箟
```

## 鐗堟湰

v3.0.0銆傛棫鐨勬ā鏉挎嫾瑁呴摼宸茬Щ闄わ紱闇€瑕佹椂浠?git 鍘嗗彶鍙栧洖銆?
