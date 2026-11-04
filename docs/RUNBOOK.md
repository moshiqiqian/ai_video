# 自己做一条视频 · 全流程

> 适用：时评、观点、口播、产品介绍——凡是"一段话 + 几个画面"的短视频。
> 全程三条命令，改两个文本文件。

---

## 0. 每次开工前

```powershell
conda activate aivideo
cd C:\Users\bb313\Desktop\AI-v
```

只有第一次需要 `cd`，之后 VS Code 终端会自动进对目录。

---

## 0.5 新建一个视频（每个视频一个目录）

`powershell
python tools\make.py new 降息之后
`

会在 ideos\降息之后\ 下生成 script.txt 和 scenes.json，声音、成片之后都写进这个目录，**和其他视频完全隔离**。

之后所有命令都带上这个名字：

`powershell
python tools\make.py 降息之后 --render
`
## 1. 写文案：`videos\<名字>\script.txt`

一个纯文本文件，**一行写完**（或分几行也行，会被整段念）。

### 时评的标准结构

```
钩子（1 句）    把观众钉住：反常识、数字、或冲突
事实（2-3 句）  发生了什么，给关键数字
解读（2-3 句）  为什么会这样，谁受影响
观点（1-2 句）  你的判断，给一个明确立场
```

### 字数换算（重要）

中文 TTS 正常语速约 **4.5 字/秒**：

| 文案字数 | 视频时长 | 适合 |
|---|---|---|
| 60 字 | ~13 秒 | 抖音/视频号爆款长度 |
| 120 字 | ~27 秒 | 常规短时评 |
| 200 字 | ~45 秒 | 深度点评 |
| 400 字 | ~90 秒 | 公众号/长视频 |

**先定时长，再写字数**，不要写完再删。

### 写的时候注意

- 用句号、逗号控制停顿，TTS 靠标点断句
- 一句话别超过 40 字，否则一口气念不完
- 数字写阿拉伯数字（"3200 亿"比"三千二百亿"念得准）

---

## 2. 写画面：`videos\<名字>\scenes.json`

视频里出现的**每一屏**都写在这里。四种镜头：

### ① title — 开场标题

```json
{
  "type": "title",
  "kicker": "财经观察",
  "title": "降息之后",
  "sub": "三个被忽略的信号"
}
```

- `kicker`：上方小字（品牌/栏目名），可留空
- `title`：大字，建议 ≤ 10 字
- `sub`：下方说明，一行

### ② list — 要点清单

```json
{
  "type": "list",
  "mark": "✓",
  "rows": ["银行息差收窄", "存款利率跟降", "理财收益下行"]
}
```

- 每行 ≤ 12 字，最多 4 行
- `mark` 可换 `•`、`→`、数字 `1` 等

### ③ quote — 大字引述

```json
{
  "type": "quote",
  "text": "真正的风险不是降息，是降息之后没人借钱。"
}
```

适合金句、关键判断，一屏一句。

### ④ ending — 结尾

```json
{
  "type": "ending",
  "title": "关注我，看懂财经",
  "accent": "看懂财经",
  "sub": "每周三期 · 不吹不黑"
}
```

- `accent` 会在 `title` 里高亮成青色字，不写就不高亮

### 切换时机：三种写法（推荐第一种）

**① 按句子编号（推荐，最准）**

先转写一次：

```powershell
conda activate indextts
python tools\transcribe.py 视频名
```

它会打印 24 句和每句的起止时间，存到 `videos\<名字>\audio\transcript.json`。

然后写成：

```json
{ "type": "list", "start_at_sentence": 4, "rows": ["…"] }
```

表示「第 4 句开始时切过来」（编号从 1 开始，看 transcribe 打印的清单）。

**好处**：重新生成音频后，句子编号不变，永远不用改。

**② 按文字匹配**

```json
{ "type": "list", "at_text": "LangConnect 是插件商店", "rows": ["…"] }
```

程序在转写结果里找最接近的一句，取它的起点。适合懒得数编号。

**③ 手动秒数（旧方式，会过时）**

```json
{ "type": "list", "hint": 8.5, "rows": ["…"] }
```

换音频后失效，只在没有转写结果时用。

> 没有 `transcript.json` 时，程序退回「平均分配 + 找停顿」的自动策略。想启用句子对齐，出片时加 `--transcribe` 即可自动转写。

### ⑤ image — 图片

```json
{ "type": "image", "start_at_sentence": 4, "src": "架构图", "caption": "六个部件的位置" }
```

`src` 是素材库里的名字（见下），`caption` 可省略。

### ⑥ video — 视频片段

```json
{ "type": "video", "start_at_sentence": 9, "src": "演示" }
```

默认静音播放，用于 B-roll、录屏。

### 素材库

每个视频独立一个 `media\`，只写名字：

```powershell
python tools\media.py add 视频名 D:\图\架构.png --name 架构图
python tools\media.py list 视频名
python tools\media.py remove 视频名 架构图
```

大文件不想复制，加 `--link` 只登记原路径。

### 完整示例

```json
{
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "scenes": [
    { "type": "title", "kicker": "财经观察", "title": "降息之后", "sub": "三个被忽略的信号" },
    { "type": "list", "mark": "1", "rows": ["银行息差收窄", "存款利率跟降"] },
    { "type": "quote", "text": "真正的风险，是没人借钱。" },
    { "type": "ending", "title": "关注我，看懂财经", "accent": "看懂财经", "sub": "每周三期" }
  ]
}
```

镜头数量 = 你要的画面段数，1–6 个都行。

---

## 3. 出片：一条命令

```powershell
python tools\make.py 视频名 --render
```

它自动做四件事：

```
配音 → 检测停顿算时间轴 → 生成 index.html → 检查 + 渲染
```

输出在 `renders\20261103_151033.mp4` 这种带时间戳的文件里。

### 常用变体

```powershell
python tools\make.py 视频名                          # 只生成，不渲染（先看看时间轴对不对）
python tools\make.py 视频名 --reuse-audio            # 改画面不重新配音
python tools\make.py 视频名 --voice zh-CN-YunyangNeural   # 换男声
python tools\make.py 视频名 --rate +5%               # 语速快 5%
```

### 第二次改画面时

改 `videos\<名字>\scenes.json` → `python tools\make.py 视频名 --reuse-audio --render`

音色、语速不动的话，音频不会重跑，节省时间。

---

## 4. 验收（别跳过）

```powershell
start videos\你的文件.mp4
```

检查四件事：

| 查什么 | 怎么看 |
|---|---|
| 字幕/文字有没有错别字 | 看画面 |
| 画面切换和说话对得上吗 | 听第 3 秒、第 8 秒的切换点 |
| 有没有声音 | 开头就该有声音，没有就是音频路径错 |
| 结尾有没有多余黑屏 | 最后一帧应该有字 |

抽帧看细节：

```powershell
ffmpeg -ss 6 -i videos\名字\render.mp4 -frames:v 1 videos\名字\check.png -y
start videos\名字\check.png
```

---

## 5. 想改风格

全部在 `tools\make.py` 顶部的 `CSS` 里：

| 想要 | 改哪里 |
|---|---|
| 换主色（现在是青色 `#5eead4`） | 搜索 `#5eead4`，全部换成你的色值 |
| 背景从深色改浅色 | `#0a0e13` 换成 `#ffffff`，文字色 `#f4f7fb` 换成 `#111` |
| 字号太大/太小 | `h1` 的 `font-size: 120px` |
| 竖屏抖音 | `python tools\make.py 视频名 --width 1080 --height 1920`，字号要相应调小 |

改完跑 `python tools\make.py 视频名 --reuse-audio --render` 验证。

---

## 6. 想用你自己的声音（声音库）

音色统一存在 `voices\` 里，一次录入，所有视频复用。

### 录入一个音色

录 5–10 秒（安静环境、单人、正常语速），然后：

```powershell
python tools\voice.py add 我的声音 我的录音.m4a --start 2 --dur 8 --label "本人"
```

| 参数 | 说明 |
|---|---|
| `--start` | 从第几秒开始截（去掉开头杂音） |
| `--dur` | 截多长，建议 6–10 秒 |
| `--label` | 备注，方便识别 |

会自动转成 24kHz 单声道，存到 `voices\我的声音\sample.wav`。

### 管理

```powershell
python tools\voice.py list          # 看所有音色
python tools\voice.py show 我的声音   # 看详情
python tools\voice.py remove 我的声音 # 删除
```

### 用这个音色出片

```powershell
python tools\make.py 降息之后 --engine indextts --voice-pack 我的声音 --render
```

或者写进 `scenes.json` 固定下来：

```json
{ "engine": "indextts", "voice_pack": "我的声音", "scenes": [ ... ] }
```

### 只生成一段语音（不出视频）

```powershell
conda activate indextts
python tools\say.py 我的声音 --text "你好，这是测试" --out test.wav
```

注意：IndexTTS2 一条 15 秒文案约 2 分钟。

---

## 7. 目录说明

```
AI-v\
├── videos\               ← 所有视频，一支一个文件夹
│   └── 降息之后\
│       ├── script.txt    旁白文案
│       ├── scenes.json   画面 + 音色
│       ├── audio\        配音（vo.mp3 / ref.wav）
│       └── render.mp4    成片
├── voices\               声音库（可复用音色）
│   └── xiaoxiao\sample.wav
├── tools\                出片脚本
│   ├── make.py
│   ├── transcribe.py      FunASR 转写，出时间戳
│   ├── voice.py           声音库管理
│   ├── say.py             用指定音色生成语音
│   └── tts_edge.py
├── docs\                 本手册 + 工作流说明
├── index.html            当前构建的画面文件（自动生成，别手改）
└── vendor\index-tts\     IndexTTS2 模型
```

---

## 8. 常见错误

| 报错 | 原因 | 解法 |
|---|---|---|
| `ModuleNotFoundError: edge_tts` | 没激活环境 | `conda activate aivideo` |
| `NoAudioReceived` | 网络断了或音色名写错 | 重跑；音色名见下表 |
| 画面文字是方块 | 字体没加载 | 别用非系统字体，微软雅黑最稳 |
| 视频没声音 | `<audio>` 路径错 | 检查 `videos/<名字>/audio/vo.mp3` 是否存在 |
| 时长对不上 | 改了音频没重算 | 去掉 `--reuse-audio` 重跑 |
| 渲染很慢 | 同时开了浏览器/飞书 | 关掉，或 `-w 1` |
| 首帧全黑 | 标题动画从 0 开始 | 已经是默认安全写法，别改 GSAP 开头 |

### 中文音色名单

```
zh-CN-XiaoxiaoNeural   女 温暖（默认）
zh-CN-XiaoyiNeural     女 活泼
zh-CN-YunyangNeural    男 新闻播报
zh-CN-YunxiNeural      男 阳光
zh-CN-YunjianNeural    男 激情解说
```

---

## 9. 从零到成片的完整示例

```powershell
conda activate aivideo
cd C:\Users\bb313\Desktop\AI-v

# 1. 写 script.txt（时评 120 字左右）
# 2. 写 scenes.json（4 个镜头）

# 3. 出片
python tools\make.py 视频名 --render

# 4. 看
start videos\
```

就这样。改文案 → 改画面 → 一条命令，循环。
