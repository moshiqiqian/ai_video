# 更新日志

## v3.0.0 · 2026-11-06

换成 render(t) 流水线：一个函数画全片，逐帧截图，逐句配音，带配乐混音。

### 新增

- **engine/**：Lemo 渲染链（MIT），`core/` + 66 份 `STYLE.md`
- **tools/lemo.py**：doctor / still / render，自动找 Chrome
- **tools/pipeline.py**：六阶段新流水线
  - brief → script → storyboard → voice → mix → render
  - 逐句 TTS、按实际时长重排、侧链混音到 −14 LUFS
  - 上游改动自动标记下游 `stale`
- **tools/music_bed.py**：程序化配乐床
- **videos/pipeline-showcase**：48 秒流程图样片（1152 帧）

### 变更

- 新项目默认 `pipeline.py`；旧 `stage.py` 只服务老项目
- 画面从「分镜 section + GSAP」改为「单页 `render(t)`」

## v2.1.0 · 2026-11-06

把「权宜之计」拆成可复用的层。

### 新增

- **	emplates/**：版式与样式从代码里剥离
  - ase.css、	hemes.json、locks/*.html
  - make.py 变成装配器：读模板 → 填占位符 → 拼 HTML
- **library/**：通用块与效果库（项目级，独立于每支视频的 source/）
  - 11 个 block：data-chart / bar-chart-race / code-typing / exploded-stack / 转场等
  - 13 个 component：blur-in / bottom-up-letters / caption-clip-wipe / aurora-drift / camera-shake 等
  - hyperframes.json 安装路径改为 library/blocks、library/components
- 模板与库的说明文档：	emplates/README.md、library/README.md

### 变更

- 主题与 CSS 不再写死在 	ools/make.py
- hyperframes check 在画面文件位于 uild/ 时自动跳过（check 只认根目录 index.html）

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
