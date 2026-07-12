---
name: fusion-html-deck
description: Explicit HTML/browser-slide output path for fusion-ppt-master.
---

# HTML Deck Workflow

Use this workflow only when the user explicitly requests HTML, browser slides, or a web presentation. The default fusion-ppt-master deliverable remains editable PPTX.

## Local Resources

- Style A seed: `templates/html/guizang/template.html`
- Swiss seed: `templates/html/guizang/template-swiss.html`
- Local HTML assets: `templates/html/guizang/assets/` (animation runtime and screenshot backgrounds)
- Style A layout guide: `references/guizang-layouts.md`
- Swiss layout lock: `references/guizang-swiss-layout-lock.md`
- Swiss layout guide: `references/guizang-layouts-swiss.md`
- Themes: `references/guizang-themes.md` and `references/guizang-themes-swiss.md`
- Final checklist: `references/guizang-checklist.md`

## Procedure

1. Complete narrative architecture and design-direction selection before writing HTML.
2. Choose Style A or Swiss International from content needs; do not mix both in one deck.
   For Swiss, `data-layout="S01"` through `S22` follow `references/guizang-swiss-layout-lock.md`; these IDs do not refer to the PPTX SVG files that happen to use `Sxx_*.svg` basenames.
3. Copy the corresponding local seed into the project as `index.html`, then copy `templates/html/guizang/assets/` to `<project_path>/assets/`. Keep all generated image paths project-relative.
4. Build one fixed 16:9 slide section per page. Preserve keyboard navigation and low-power behavior from the seed.
5. Apply the same thesis, page order, visual tone, and page rhythm recorded for the deck. HTML is a different renderer, not a different story.
6. Keep real text as HTML text. Do not replace complete slides with screenshots.
7. For Swiss output, run:

```bash
node scripts/validate-guizang-swiss-deck.mjs <project_path>/index.html
```

8. Read `references/guizang-checklist.md`, then open the HTML in a real browser and inspect every page at desktop and mobile viewport sizes before delivery.

Node.js is required for the Swiss validator. Run `node --version` before promising validated Swiss HTML. If the user explicitly requests one physical HTML file, keep CDN font/icon/runtime dependencies or inline them; state whether the result is network-dependent. An offline single-file claim is valid only after all external URLs and project-relative assets have been removed or embedded and the file has been tested with networking disabled.

The bundled HTML-to-PDF/PPTX and thumbnail utilities additionally require the locked packages in `package-lock.json`. Install them once with `python scripts/bootstrap_runtime.py --with-node`; do not read or reuse another skill's `node_modules` directory.

## Dual Delivery

When the user requests both PPTX and HTML, produce both from the same approved narrative and design decisions. PPTX follows the main production pipeline; HTML follows this workflow. Report the two outputs separately and do not claim pixel identity between the two renderers.
