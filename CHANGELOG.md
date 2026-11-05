# 更新日志

## v2.0.0 · 2026-11-05

六阶段流水线 + 每支视频独立工程。

### 新增

- **`tools/stage.py`**：阶段调度与状态机
  - `start / brief / script / storyboard / assets / voice / render`
  - `confirm / status / next / theme / migrate / list`
  - `project.json` 记录每个阶段的 `status / confirmed / input_hash`
  - 上游改动自动级联标记 `stale`，拒绝确认过期产物
- **七个技能**：`video-pipeline`（总控）+ `video-brief / script / storyboard / assets / voice / render`
- **文稿导入**：`brief` 自动扫描 `source/articles/`，清洗 frontmatter、代码块、图片、链接，体检字数/句长，提取标题、金句、小标题候选
- **时长自适应**：`--duration auto`，按文稿类型估算目标字数并吸附到 15/30/45/60… 档
- **主题系统**：`dark-teal / warm-paper / news-red / mono-ink`，支持单项颜色覆盖
- **本地 GSAP**：`assets/vendor/gsap.min.js`，不再依赖 CDN
- **目录分层**：`source/`（输入）`build/`（中间态）`audio/` `qa/` `output/`（成品）
- **每支视频独立画面文件**：`videos/<名字>/build/index.html`，渲染用 `-c` 指定
- **字幕全程覆盖**：`fill_cues()` 消除句间空档；开启字幕后缺转写会报错并自动转写
- **默认音色**：有音色库时默认 IndexTTS2 克隆（`xiaoxiao`），否则回退 edge-tts
- **一键安装**：`bootstrap.ps1` 新增 HyperFrames 预热、Chrome 检测、本地 GSAP 检查；`doctor.ps1` 检查项 20 → 22

### 变更

- 技能从 2 个（`deploy-ai-video`、`make-video`）拆为 8 个
- 渲染命令带 `-c`，不再使用根目录 `index.html`
- 中间产物全部收进 `build/`，成品进 `output/`
- 老视频可用 `stage.py migrate` 自动迁移目录与状态

### 移除

- `tools/video.py`（被 `stage.py` 取代）
- 根目录 `index.html`（改为每支视频一份）
- `skills/make-video`（拆分为阶段技能）

### 修复

- 字幕在 quote / ending 场景被过滤导致中断
- 句间停顿无字幕
- 开启字幕后缺转写仍静默出片
- 浅色主题字幕对比度不足
- `stage.py` 状态级联误判（递归串味）

## v1.0.0

初始版本：`make.py` 单脚本出片，edge-tts / IndexTTS2 配音，FunASR 时间戳，四种文字镜头。
