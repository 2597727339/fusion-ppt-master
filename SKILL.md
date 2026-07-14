---
name: fusion-ppt-master
description: 真正独立的融合型 PPT 技能。内置叙事架构、视觉设计、页面节奏、SVG 生产与可编辑 PPTX 导出能力，不调用 dashiai、huashu、guizang 或 ppt-master 的外部 skill 本体。当用户要求制作 PPT、演示文稿、融资路演、汇报、课件、提案、杂志风或瑞士风 deck 时使用。未明确要求 HTML 时，默认交付可编辑 PPTX。
---

# Fusion PPT Master

这是一个自包含的生产型 skill。叙事、设计、节奏和导出是同一条管线中的内部阶段；运行时不得读取或调用其他 PPT skill 的 `SKILL.md`、目录或中间产物。

## 输出契约

- 默认主交付物：可编辑 `.pptx`。
- 只有用户明确要求 HTML、browser slides 或网页演示时，才进入 [`workflows/html-deck.md`](workflows/html-deck.md)。
- `spec_lock.md` 是 Strategist 与 Executor 之间唯一的机器执行契约。
- `design_spec.md` 保存设计理由和逐页内容，不能代替 `spec_lock.md`。
- 禁止用整页截图、整页位图或栅格化正文冒充可编辑 PPTX。
- 完成前必须读取 `render/export` 结果，确认文件存在并验证可编辑对象。

## 运行时准备

所有脚本都以当前 skill 根目录为工作目录。不要依赖系统里碰巧安装的 Python 包。

```bash
# 仅使用默认 PPTX 管线时
python scripts/bootstrap_runtime.py

# 首次安装、发布审计或使用 HTML/browser 工具时
python scripts/bootstrap_runtime.py --with-node

# Windows 后续命令使用
.venv\Scripts\python.exe

# macOS/Linux 后续命令使用
.venv/bin/python
```

下文用 `<python>` 表示上述隔离解释器。完整发布级自检要求先执行 `--with-node`，然后运行：

```bash
<python> scripts/final_validation.py --runtime
```

## 全局执行纪律

1. Phase 0 到 Phase 6 必须串行执行；上游产物是下游输入。
2. Phase 3 的八项确认是硬停止点。用户确认前不得写最终 `design_spec.md`、`spec_lock.md` 或任何页面 SVG。
3. 不得在 Phase 1/2 提前生成 SVG，也不得在 Phase 5 反向重写已确认的叙事或视觉基准。
4. 每页 SVG 必须由当前主 agent 顺序生成。生成每一页前重新读取项目的 `spec_lock.md`。
5. 所有事实、数字、客户名称和结果必须来自用户材料或可追溯来源；未知项使用明确 placeholder。
6. 任一质量门返回非零退出码时必须修复并重跑，不得跳过。

## 七阶段统一管线

### Phase 0: Source Ingestion

目标：把用户材料变成可追溯的项目源文件。

1. 用户只有主题、没有实质材料时，先完整读取并执行 [`workflows/topic-research.md`](workflows/topic-research.md)。
2. 根据输入类型使用 `scripts/source_to_md/` 下对应转换器；Markdown 和对话正文可直接使用。
3. 初始化项目：

```bash
<python> scripts/project_manager.py init <project_name> --format ppt169 --dir <output_parent>
```

4. 有源文件时导入项目；只有在用户允许移动原文件时才使用 `--move`，否则使用 `--copy`：

```bash
<python> scripts/project_manager.py import-sources <project_path> <sources...> --copy
```

完成条件：项目目录存在，`sources/` 中有可读材料，来源与假设已区分。

### Phase 1: Narrative Architecture

必须读取 [`references/dashiai-narrative-shapes.md`](references/dashiai-narrative-shapes.md)。

输出 `<project_path>/narrative_plan.md`，至少包含：

- 决策目标和主要受众；
- 受众可能的反对意见；
- 一句话核心论点；
- 一个主叙事弧及选择理由；
- 逐页 job、takeaway、证据类型；
- 已验证事实、用户数据、假设和证据缺口。

七种叙事弧允许内容重叠，但必须根据“本次 deck 要支持的首要决策”选一个主弧；冲突时按 [`references/dashiai-narrative-shapes.md`](references/dashiai-narrative-shapes.md) 的 tie-breaker 处理。

### Phase 2: Design Direction and Page Rhythm

先读取与任务相关的本地设计资料：

- [`references/design-context.md`](references/design-context.md)
- [`references/design-styles-index.json`](references/design-styles-index.json)
- [`references/design-styles.md`](references/design-styles.md)
- [`references/huashu-design-direction.md`](references/huashu-design-direction.md)
- [`references/huashu-anti-slop.md`](references/huashu-anti-slop.md)
- [`references/huashu-taste-anchors.md`](references/huashu-taste-anchors.md)
- 涉及真实品牌时读取 [`references/brand-asset-protocol.md`](references/brand-asset-protocol.md)
- [`references/guizang-rhythm-guide.md`](references/guizang-rhythm-guide.md)

若用户没有品牌规范、参考图或明确风格，按设计方向顾问模式准备 3 个差异化方向；不要直接替用户拍板。每个方向必须给出内容适配理由、字体、色彩、版式节奏、图片策略和 anti-slop 边界。

输出 `<project_path>/design_direction_inputs.md`，供 Phase 3 八项确认使用。此阶段不写 SVG。

### Phase 3: Strategist and Eight Confirmations

必须完整读取：

- [`references/strategist.md`](references/strategist.md)
- [`templates/design_spec_reference.md`](templates/design_spec_reference.md)
- [`templates/spec_lock_reference.md`](templates/spec_lock_reference.md)
- [`templates/layouts/layouts_index.json`](templates/layouts/layouts_index.json)
- [`templates/charts/charts_index.json`](templates/charts/charts_index.json)

一次性向用户提交带推荐值的八项确认，并停止等待：

1. 画布格式；
2. 页数；
3. 关键信息、主叙事弧和证据缺口；
4. 视觉风格；
5. 配色；
6. 图标；
7. 字体与字号；
8. 图片获取和处理策略。

用户确认后，生成：

- `<project_path>/design_spec.md`
- `<project_path>/spec_lock.md`

`spec_lock.md` 必须包含 `canvas`、`colors`、`typography`、`icons`、`images`、`page_rhythm`、`page_layouts`、`page_charts`、`forbidden`、`visual_tone` 和 `narrative_shape`。每个页面必须有 `anchor`、`dense` 或 `breathing` 节奏标签。

运行契约门：

```bash
<python> scripts/fusion_orchestrator.py validate <project_path>
```

### Phase 4: Image Acquisition

仅当图片清单要求 AI 生成或网络搜索时执行。先读取 [`references/image-base.md`](references/image-base.md)，然后只加载实际需要的路径：

- AI 图片：[`references/image-generator.md`](references/image-generator.md)
- 网络图片：[`references/image-searcher.md`](references/image-searcher.md)

图片必须写入项目 `images/`，并更新清单状态和来源。失败项标记为 `Needs-Manual`，不得伪造已生成状态。若没有图片需求，明确记录跳过并进入 Phase 5。

### Phase 5: Executor

必须读取：

- [`references/executor-base.md`](references/executor-base.md)
- [`references/shared-standards.md`](references/shared-standards.md)
- 已确认的一个执行风格文件：`executor-general.md`、`executor-consultant.md` 或 `executor-consultant-top.md`

若使用融合布局，还需按所选系列读取：

- Magazine Style A：[`references/guizang-layouts.md`](references/guizang-layouts.md) 和 [`templates/layouts/magazine-style-a/design_spec.md`](templates/layouts/magazine-style-a/design_spec.md)
- Swiss International PPTX：[`templates/layouts/swiss-international/design_spec.md`](templates/layouts/swiss-international/design_spec.md)。其中 `Sxx_*.svg` 是 PPTX 专用 basename，不等同于 HTML 的 `data-layout="Sxx"`。HTML Swiss 只能通过 [`workflows/html-deck.md`](workflows/html-deck.md) 读取其 layout lock。

执行顺序：

1. 预读 `spec_lock.md` 引用的所有布局和图表模板。
2. 启动 [`workflows/live-preview.md`](workflows/live-preview.md) 中的本地预览服务。
3. 每页生成前重新读取 `spec_lock.md`，然后逐页写入 `svg_output/`。
4. 生成 `notes/total.md`。
5. 运行质量门：

```bash
<python> scripts/svg_quality_checker.py <project_path>
```

存在图表时再执行 [`workflows/verify-charts.md`](workflows/verify-charts.md)。任何 error 必须修复到 0。

### Phase 6: Post-processing and Export

三个命令必须按顺序分别成功，不得合并或跳步：

```bash
<python> scripts/total_md_split.py <project_path>
<python> scripts/finalize_svg.py <project_path>
<python> scripts/svg_to_pptx.py <project_path>
```

导出后必须：

1. 确认 `exports/*.pptx` 存在且大小大于 0；
2. 用 `python-pptx` 重新打开；
3. 报告页数、总 shape 数、文本 shape 数、图表和表格数量；
4. 确认正文不是整页位图；
5. 读取质量检查和导出日志后再宣布完成。

用户明确要求导出后视觉复核、`officecli-local-review` 或第二意见时，才进入 [`workflows/officecli-local-review.md`](workflows/officecli-local-review.md)。该流程只使用 Fusion 内置的本地渲染器，默认关闭，只读取最终 PPTX 并写独立审查证据，不得替代 Fusion 生成、可编辑性检查或 PowerPoint 实机门。

## 布局与风格资源

- Magazine Style A：`templates/layouts/magazine-style-a/`，12 个 SVG。
- Swiss International：`templates/layouts/swiss-international/`，22 个 SVG。
- 40 个设计方向：`references/design-styles-index.json`，完整说明在 `references/design-styles.md`。
- HTML 种子与离线动画资源：`templates/html/guizang/`。

## 迁移旧项目

旧 `deck-spec.json` 项目使用：

```bash
<python> scripts/fusion_orchestrator.py migrate --from <old_project_path>
```

迁移结果必须再次运行 `validate`。迁移会保留旧文件并创建 `spec_lock.md`；`migration_status: review-required` 表示仍需人工确认叙事和设计映射。

## 向后兼容与独立性

- 原四个 skill 可以在系统中单独存在，但不是本 skill 的运行依赖。
- 不得通过目录联接、包装器或外部 skill 路径补齐缺失文件。
- 所需脚本、模板、参考文档、HTML 资源和依赖清单必须位于本目录。
- 内置 `officecli-local-review` 只调用本地 PowerShell、LibreOffice 和 Poppler，不读取独立 OfficeCLI skill，也不依赖专有 OfficeCLI 二进制或任何远程服务。
- 将本目录复制到另一位置后，结构校验和 PPTX 导出仍应可运行。

## 调用示例

- `/fusion-ppt-master 创建一个 AI 客服融资演示，输出可编辑 PPTX`
- `/fusion-ppt-master 用瑞士国际主义风格制作年度数据汇报`
- `/fusion-ppt-master 我没有风格方向，请给我三个真实可比较的方向`
- `/fusion-ppt-master 把这份 PDF 转成可编辑 PPTX`
- `/fusion-ppt-master 明确输出单文件 HTML 网页演示`
