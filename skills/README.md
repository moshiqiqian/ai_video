# Skills

这里放的是给 AI Agent 看的**操作技能**，每个子文件夹是一个独立技能，互不依赖。

```
skills/
└── deploy-ai-video/        部署/重建环境
    ├── SKILL.md            入口，Agent 先读这个
    ├── references/         详细文档（按需加载）
    │   ├── install.md
    │   └── troubleshooting.md
    ├── scripts/            可直接运行的脚本
    │   ├── bootstrap.ps1
    │   └── doctor.ps1
    └── assets/             技能自带的数据文件
```

## 新增一个技能

1. 建目录 `skills/<技能名>/`
2. 写 `SKILL.md`，开头是元信息：

```markdown
---
name: 技能名
description: 一句话说明「什么时候用」，要写触发场景和关键词
---
```

3. 内容只写**判断逻辑和步骤**，长文档放 `references/`，能自动化的放 `scripts/`

## 现有技能

| 技能 | 触发场景 |
|---|---|
| `deploy-ai-video` | 换机器部署、环境损坏、安装报错 |
| `make-video` | 做一条新视频：定主题 → 写稿 → 分镜 → 素材 → 配音 → 校验 → 渲染 |

## 约定

- 每个技能自包含，不跨技能引用文件
- 脚本必须可重复执行（幂等）
- 文档里的命令要能直接复制运行
- 写「验证方法」，不能只说「装好了」
