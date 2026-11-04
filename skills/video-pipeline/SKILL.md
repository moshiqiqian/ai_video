---
name: video-pipeline
description: 视频流水线总控。用户说「做一条视频」「继续」「下一步」「这步重做」「进度到哪了」时使用。负责读取项目状态、判断当前该做哪一步、调度对应的阶段技能、并在每步结束时要求人工确认。不要在这里直接写文案或画面，交给阶段技能。
---

# 视频流水线总控

一条视频分六个阶段，每阶段独立执行、独立确认。

```
brief → script → storyboard → assets → voice → render
立项     文案      分镜         素材      配音      渲染
```

## 开工前：读状态

```powershell
python tools\stage.py list
python tools\stage.py status <视频名>
```

`status` 会打印六个阶段的状态：

| 状态 | 含义 | 该做什么 |
|---|---|---|
| 待做 | 还没开始 | 执行该阶段 |
| 完成 ✓ | 有产物且已确认 | 跳到下一阶段 |
| 完成（无 ✓） | 有产物，等你确认 | 给用户看产物 |
| 过期 | 上游改过，产物作废 | 重跑该阶段 |
| 跳过 | 本片不需要 | 忽略 |

## 主循环

```
1. status → 找到「下一步」
2. 告诉用户：现在第几阶段、上一步产出什么、这一步会产出什么
3. 确认需要的输入齐了（文案？素材？）
4. 加载对应的阶段技能，执行
5. 把产物给用户看，等回答
6. 用户认可 → confirm → 回到 1
   用户要改 → 重跑该阶段（或回到上游）
```

## 阶段与技能对照

| 阶段 | 技能 | 产物 | 确认物 |
|---|---|---|---|
| brief | `video-brief` | `brief.md`、`script.txt` 初稿、`scenes.json` 骨架 | 主题/时长/风格 |
| script | `video-script` | `script.txt`、`script.json` | 全文和字数 |
| storyboard | `video-storyboard` | `scenes.json`、`storyboard.md` | 分镜表格 |
| assets | `video-assets` | `media/index.json` | 素材清单 |
| voice | `video-voice` | `audio/vo.*`、`voice.json` | 让用户听 |
| render | `video-render` | `render.mp4`、`qa/*.png` | 预览帧 + 成片 |

## 命令

```powershell
python tools\stage.py brief      视频名 --from D:\文章.md --duration 45 --theme news-red
python tools\stage.py script     视频名
python tools\stage.py storyboard 视频名
python tools\stage.py assets     视频名
python tools\stage.py voice      视频名
python tools\stage.py render     视频名 --quality delivery

python tools\stage.py confirm 视频名 <阶段>   # 记录人工确认
python tools\stage.py status  视频名
python tools\stage.py next    视频名
```

## 硬规则

1. **没确认不许推进**。上游 `confirmed=false` 时，下一阶段会直接报错退出。
2. **过期必须重做**。`stale` 状态下 `confirm` 会被拒绝，先重跑该阶段。
3. **一次只做一个阶段**。不要连着跑 script 和 storyboard。
4. **改文案 = 重做分镜、配音、渲染**。系统会自动标 stale，照着提示走。
5. **用户说「直接出片」** 才允许 `--force`，并要说明跳过了哪些确认。

## 常见情况

**用户没有文稿，只有一句主题**
→ 走 `video-brief`，不带 `--from`，由 brief 写骨架，然后 script 阶段写稿。

**用户给了 md**
→ `video-brief` 负责导入、体检、给候选，不要自己读文件。

**用户改了文案**
→ 重跑 script → 确认 → storyboard（会提示过期）→ voice → render。

**用户只想换配色**
→ 不用走流水线，直接 `stage.py` 之外用 `make.py --theme`，或改 `project.json` 的 theme 后重渲染。

**用户问「做到哪了」**
→ 跑 `status`，把表格转述成一句话：「文案和分镜完成，配音待做」。

## 汇报格式

每次执行完一个阶段，用这个结构：

```
【第 2 步 · 文案】
产出：script.txt（186 字，预计 41 秒）
        script.json（逐句清单）
问题：2 句超过 40 字，TTS 会念得吃力
请确认：可以继续做分镜吗？
```
