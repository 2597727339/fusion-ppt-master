---
kind: layout
name: swiss-international
source: internal-pptx-svg-adaptation
summary: PPTX-specific Swiss International SVG family with strict grids, hairline rules, high-contrast typography, and minimal decoration. Its Sxx basenames are not the HTML data-layout registry.
---

# Swiss International — Layout Family

## Design Intent

Strict grid-based layouts with typographic hierarchy as the primary visual device. No decoration, no gradients, no rounded corners. Color used sparingly as accent only.

> Namespace boundary: this file is authoritative for PPTX SVG basenames. `references/guizang-swiss-layout-lock.md` is authoritative only for HTML `<section data-layout="Sxx">` output. The two registries intentionally use separate semantics and must not be cross-resolved by number.

## Page Types (22 layouts)

| # | File | Page Type | Rhythm | Theme |
|---|------|-----------|--------|-------|
| S01 | `S01_index_cover.svg` | Swiss Cover | anchor | light |
| S02 | `S02_vertical_timeline.svg` | Vertical Timeline | dense | light |
| S03 | `S03_split_statement.svg` | Split Statement | breathing | light |
| S04 | `S04_asymmetric_grid.svg` | Asymmetric Grid | dense | light |
| S05 | `S05_data_table.svg` | Data Table | dense | light |
| S06 | `S06_quadrant.svg` | 2x2 Quadrant | dense | light |
| S07 | `S07_fullbleed_image.svg` | Full-Bleed Image | breathing | light |
| S08 | `S08_three_column.svg` | Three Column | dense | light |
| S09 | `S09_step_process.svg` | Step Process | dense | light |
| S10 | `S10_mixed_ratio.svg` | Mixed Ratio Grid | dense | light |
| S11 | `S11_chapter_divider.svg` | Chapter Divider | anchor | dark |
| S12 | `S12_infographic.svg` | Infographic | dense | light |
| S13 | `S13_callout.svg` | Callout Block | breathing | light |
| S14 | `S14_comparison_bar.svg` | Comparison Bars | dense | light |
| S15 | `S15_masonry.svg` | Masonry Grid | dense | light |
| S16 | `S16_metric_card.svg` | Metric Cards | dense | light |
| S17 | `S17_quote_dark.svg` | Dark Quote | breathing | hero_dark |
| S18 | `S18_team_roster.svg` | Team Roster | dense | light |
| S19 | `S19_agenda.svg` | Agenda/Timeline | dense | light |
| S20 | `S20_framed_photo.svg` | Framed Photo | breathing | light |
| S21 | `S21_end_slide.svg` | Ending | anchor | light |
| S22 | `S22_reference.svg` | References | dense | light |

## Design Rules

- **No rounded corners** anywhere — all rectangles have border-radius: 0
- **Hairline rules** (1px solid #E5E5E5 or #0A0A0A) for all separators
- **Strict grid** — 60px margins on all sides, content within 1160px width
- **Typography hierarchy** is the primary visual device — title > subtitle > body > annotation
- **Color** used only as accent (max 1 accent element per page)
- **No images** on most pages — photographs only on S07, S15, S18, S20
- **Tabular nums** for all numbers (font-variant-numeric: tabular-nums)

## Conversion Notes

- Original source: HTML-based Swiss layouts
- Converted to: Standalone SVG with inline styles
- All typography uses PPT-safe font stacks (Arial, Georgia, etc.)
- Strict adherence to Swiss International principles: grid, typography, minimalism
