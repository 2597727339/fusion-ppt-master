---
kind: layout
name: magazine-style-a
source: references/guizang-layouts.md
summary: Editorial-style layout family with hero covers, big-number data pages, left-text-right-image layouts, image grids, pipeline/process slides, hero questions, big quotes, before/after comparisons, and lead-image side-text pages. Optimized for narrative decks that need breathing room between content pages.
placeholders:
  01_cover: []
  02_chapter: []
  03b_content_abstract: []
  03c_content_image_text: []
---

# Magazine Style A — Layout Family

## Design Intent

Editorial, magazine-inspired layouts that prioritize **narrative rhythm** over uniform grid density. Each page type serves a specific narrative function.

## Page Types (12 layouts)

| # | File | Page Type | Rhythm | Theme |
|---|------|-----------|--------|-------|
| 1 | `01_cover.svg` | Hero Cover | anchor | hero_dark |
| 2 | `02_chapter.svg` | Chapter Divider | anchor | hero_light |
| 3a | `03a_data_hero.svg` | Big Numbers Grid | dense | light |
| 3b | `03b_content_abstract.svg` | Abstract Content | dense | light |
| 3c | `03c_content_image_text.svg` | Left Text Right Image | dense | light |
| 4 | `04_quote_image.svg` | Quote + Image | breathing | light |
| 5 | `05_image_grid.svg` | Image Grid (3x2) | dense | light |
| 6 | `06_pipeline.svg` | Two-Column Pipeline | dense | light |
| 7 | `07_suspense.svg` | Hero Question | breathing | hero_dark |
| 8 | `08_big_quote.svg` | Big Quote | breathing | dark |
| 9 | `09_comparison.svg` | Before/After Comparison | dense | light |
| 10 | `10_lead_image_side_text.svg` | Lead Image + Side Text | dense | light |

## Theme Alternation Rules

- Layout 1 (cover) and Layout 2 (chapter) MUST alternate hero_dark / hero_light
- Content pages (3a-3c, 5-6, 9-10) default to light; alternate dark for visual relief
- Breathing pages (4, 7, 8) provide natural pauses between dense sequences
- Maximum 3 consecutive dense pages before a breathing or anchor page

## Conversion Notes

- Original source: HTML `<section class="slide">` with CSS classes
- Converted to: Standalone SVG with inline styles (no class/style elements)
- WebGL background effects from original template are NOT ported (SVG has no JS)
- Motion/animation effects from original are NOT ported (SVG is static)
- All typography uses PPT-safe font stacks (Microsoft YaHei, Georgia, etc.)
