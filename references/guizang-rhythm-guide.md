---
name: guizang-rhythm-guide
description: Guizang 页面节奏规则 — hero light/dark 交替、连续同主题限制、breathing 页判定
metadata:
  type: reference
---

# Guizang Rhythm Guide — 页面节奏规则

## 三种节奏标签

| 标签 | 含义 | 布局纪律 |
|------|------|---------|
| `anchor` | 结构性页面（封面/章节页/目录/结尾） | 跟随模板，不做改动 |
| `dense` | 信息密集型（数据/KPI/对比/多要点列表） | 允许卡片网格、多列、表格、图表 |
| `breathing` | 低密度页面（单一概念、英雄引语、大图+说明、章节过渡） | **禁止**多卡片网格布局 |

## Breathing 页的 4 种合法形式

1. **裸文本** — 一句话+大留白，无容器
2. **分割线** — 章节过渡，用 1px 线或色块差
3. **全幅图片** — 图片是主要声音，文字只是说明
4. **单一强调元素** — 一个大数字/引语/指标，不封装在卡片中

## Hero Light/Dark 交替规则

**核心原则**：相邻页面不应同为 light（浅色底）或 dark（深色底）。

| 页面类型 | 默认底色 | 例外 |
|---------|---------|------|
| anchor | 跟随模板 | 章节页可 dark |
| dense | light | 数据密集时可 dark 提高可读性 |
| breathing | 交替于前一页 | 如果前一页 dark → 此页 light |

**连续同主题限制**：同一主题的 dense 页面最多连续 3 页，第 4 页必须是 breathing 或 anchor。

## 节奏分配策略

### 策略 A：叙事驱动（推荐）

breathing 页出现在：
- 章节转换处
- SCQA 的 "Complication" 之前（制造张力）
- 大数字/关键指标之后（让用户消化）
- 结论页之前（聚焦注意力）

### 策略 B：密度均匀

适用于数据简报类 deck——几乎全部 dense，仅在封面/结尾/章节页使用 anchor。

**禁止**：为了凑节奏而发明无内容的 breathing 页（如空白分隔页）。每个 breathing 页必须回答"这一页独立在说什么？"

## 对 Executor 的影响

Executor 在生成 SVG 时根据 `page_rhythm` 应用不同纪律：

| 标签 | Executor 行为 |
|------|--------------|
| `anchor` | 使用 `page_layouts` 指定的模板 SVG |
| `dense` | 允许卡片网格、多列、紧凑间距 |
| `breathing` | 禁止多卡片网格；使用裸文本/全幅图/单元素布局 |

## 节奏验证

Strategist 在输出 `spec_lock.md` 后自检：
1. 是否有连续的 breathing 页？→ 最多 1 个连续 breathing
2. 是否有超过 3 个连续的 dense 页且同一主题？→ 必须插入 breathing
3. 每个 breathing 页是否有独立内容价值？→ 否 → 改为 dense 或 anchor
