# templates · 可复用版式

项目的视觉层都放这里，`tools/make.py` 只负责装配，不再内置样式。

```
templates/
├── base.css            全局样式（含 %(BG)s 等占位符）
├── themes.json         主题：配色、字幕底色
└── blocks/             版式片段
    ├── title.html
    ├── list.html
    ├── quote.html
    ├── image.html
    ├── video.html
    └── ending.html
```

## 工作原理

```
scenes.json 的 type  →  make.py 查 blocks/<type>.html
                     →  替换 {{占位符}}
                     →  拼进 build/index.html
```

占位符：

| 文件 | 占位符 |
|---|---|
| `title.html` | `{{i}}` `{{kicker}}` `{{title}}` `{{sub}}` |
| `list.html` | `{{items}}`（每行 HTML 由代码生成） |
| `quote.html` | `{{i}}` `{{text}}` |
| `image.html` | `{{i}}` `{{src}}` `{{caption}}` |
| `video.html` | `{{i}}` `{{src}}` `{{dur}}` |
| `ending.html` | `{{i}}` `{{title}}` `{{sub}}` |

## 加一种版式

1. 新建 `blocks/your-type.html`，用 `{{占位符}}`
2. 在 `scenes.json` 里用 `{"type": "your-type"}`
3. 在 `tools/make.py` 的 `build_html` 里加一个分支（渲染块 + 时间轴）

动画不写在模板里，因为时间点要按音频计算，统一在代码里生成。

## 加一套主题

在 `themes.json` 里加一项：

```json
"my-theme": {
  "label": "我的主题",
  "bg": "#101010", "ink": "#f5f5f5", "muted": "#888",
  "accent": "#ff6600", "sub_bg": "rgba(0,0,0,0.6)"
}
```

然后 `stage.py theme 视频名 --set my-theme`。

## 注意

- `base.css` 用 Python 的 `%` 格式化，颜色值写作 `%(BG)s`，百分号写作 `%%`
- 改模板后建议跑一次 `stage.py render --quality draft` 看效果
- 模板只负责结构和静态样式，动画在代码里
