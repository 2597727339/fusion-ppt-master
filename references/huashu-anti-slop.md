---
name: huashu-anti-slop
description: 反 AI slop 清单 — 禁止的模式及替代方案
metadata:
  type: reference
---

# Huashu Anti-Slop — 反 AI 默认模式清单

## 默认禁止的模式

这些规则约束的是没有品牌依据、没有设计理由时的 AI 默认输出。若用户明确选择的命名风格或真实品牌规范以渐变、圆角或其他相关元素为核心特征，可以例外使用，但必须在 `spec_lock.md visual_tone` 中记录选择依据和使用边界。Emoji 图标、SVG 人物剪影和全页密度雷同仍不得作为捷径。

| 模式 | 识别特征 | 为什么不好 | 替代方案 |
|------|---------|-----------|---------|
| 紫色渐变背景 | `linear-gradient(#635BFF, #00E5FF)` | AI 默认审美，千篇一律 | 实色背景 + 单一强调色 |
| Emoji 图标 | 😊🚀💡📊 等 Unicode emoji | 不专业、风格不统一 | SVG 图标库（chunk/tabler/phosphor） |
| 圆角卡片+左边框 | `border-radius: 12px; border-left: 4px solid #...` | 最典型的"AI 感" | 无边框分割 / 网格 / 非对称布局 |
| SVG 绘制的人物剪影 | 简单轮廓的人形 SVG | 廉价感、2010 年代过时 | 照片 / 矢量插画 / 抽象图形 |
| 每页密度一致 | 所有页面都是卡片网格 | 没有节奏感 | breathing/dense/anchor 交替 |
| GitHub-dark 偷懒解 | `#0D1117` 深蓝底 + 青/紫霓虹 glow | 只禁这一种组合 | 有意图的暗色（电影级光影、暖色赛博） |

## 每个 deck 的自定义 anti_slop 行

在 `spec_lock.md visual_tone` 中添加当前 deck 特有的禁止项；不要机械复制与已确认风格冲突的条目：

```
- anti_slop: no purple gradients, no emoji icons, no rounded cards with left accent border, no SVG-drawn people, no gradient text shadows
```

## 正面护栏：品位锚点

anti_slop 是"不要什么"，品位锚点是"要什么"。两者必须同时存在。

参见 [`huashu-taste-anchors.md`](huashu-taste-anchors.md)。
