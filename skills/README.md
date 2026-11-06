# Skills

给 AI Agent 看的操作技能，每个子文件夹一个。

## 现有技能

| 技能 | 角色 | 触发场景 |
|---|---|---|
| `video-pipeline` | 总控 | 「做一条视频」「继续」「下一步」「做到哪了」 |
| `deploy-ai-video` | 部署 | 「换电脑怎么装」「环境坏了」 |

## 流水线关系

```
video-pipeline（总控）
   ├── 1 立项      → source/brief.md
   ├── 2 文案      → build/lines.json
   ├── 3 分镜      → build/timeline.json + film/
   ├── 4 配音      → film/audio/*.wav
   ├── 5 混音      → film/audio/mix.wav
   └── 6 渲染      → output/render.mp4 + qa/
```

每个阶段：执行 → 给用户看产物 → `pipeline.py confirm` → 下一阶段。

## 目录规范

```
skills/<技能名>/
└── SKILL.md          入口：frontmatter + 判断 + 步骤
```
