# Skills

这里放给 AI Agent 看的**操作技能**，每个子文件夹是一个独立技能。

## 现有技能

| 技能 | 角色 | 触发场景 |
|---|---|---|
| `video-pipeline` | 总控 | 「做一条视频」「继续」「下一步」「做到哪了」 |
| `video-brief` | 第 1 步 | 「用这篇文章做个视频」「定主题」 |
| `video-script` | 第 2 步 | 「文案改一下」「太长了」 |
| `video-storyboard` | 第 3 步 | 「分镜怎么排」「拆一下」 |
| `video-assets` | 第 4 步 | 「加张图」「插个录屏」 |
| `video-voice` | 第 5 步 | 「换个声音」「用我的声音」 |
| `video-render` | 第 6 步 | 「出片」「渲染」「画质高一点」 |
| `deploy-ai-video` | 部署 | 「换电脑怎么装」「环境坏了」 |

## 流水线关系

```
video-pipeline（总控）
   ├── video-brief       立项 → brief.md
   ├── video-script      文案 → script.txt / script.json
   ├── video-storyboard  分镜 → scenes.json / storyboard.md
   ├── video-assets      素材 → media/index.json
   ├── video-voice       配音 → audio/vo.* / voice.json
   └── video-render      渲染 → render.mp4 / qa/
```

每个阶段：执行 → 给用户看产物 → `stage.py confirm` → 下一阶段。

## 目录规范

```
skills/<技能名>/
├── SKILL.md          入口：frontmatter + 判断 + 步骤
├── references/       长文档，按需加载
└── scripts/          可执行脚本（可选）
```

## 新增一个技能

1. 建目录
2. 写 `SKILL.md`，开头必须有：

```markdown
---
name: 技能名
description: 什么时候用 + 触发关键词
---
```

3. 长内容放 `references/`，可自动化放 `scripts/`

## 约定

- 每个技能自包含，不跨技能引用文件
- 脚本必须幂等
- 文档里的命令要能直接复制运行
- 必须写「怎么验证」，不能只说「做好了」
- 阶段技能不做别的阶段的事（文案不配音，配音不排版）
