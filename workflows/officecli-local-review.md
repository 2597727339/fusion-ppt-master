---
description: Optional local-only post-export PPTX rendering and visual validation
---

# OfficeCLI Local Review Workflow

> Local-only post-export QA. This workflow reads a finished PPTX and produces PDF/PNG evidence. It never replaces Fusion planning, SVG generation, PPTX export, editability checks, or native PowerPoint validation.

## Positioning

Run this workflow only when the user explicitly asks for `officecli-local-review`, local visual review, or a post-export second opinion. It is off by default and runs after Phase 6 export, before handoff.

The implementation is bundled inside Fusion and uses local LibreOffice and Poppler executables. It has no account flow, remote provider, publishing path, or proprietary OfficeCLI executable dependency.

## Preconditions

- Phase 6 produced a non-empty `exports/*.pptx`.
- The PPTX already passed Fusion's structural and editability checks.
- Fusion bundles [`scripts/officecli_local_review.ps1`](../scripts/officecli_local_review.ps1).
- The adapter resolves the renderer in this order:
  1. `--local-renderer`
  2. `FUSION_LOCAL_REVIEWER`
  3. the bundled script beside the adapter
- The renderer discovers LibreOffice and Poppler from `PATH`, standard Windows install locations, and WinGet packages. Use `FUSION_SOFFICE` or `FUSION_PDFTOPPM` only when discovery needs an explicit executable path.

## Command

Use the isolated Fusion interpreter as `<python>`:

```bash
<python> scripts/officecli_local_review_adapter.py \
  --pptx <project_path>/exports/<deck>.pptx
```

The adapter is advisory by default. Add `--strict` only when the user explicitly requests this optional review to block handoff.

After `adapter_status=rendered_local`, read `.review/officecli-local/page-*.png` and inspect every page. `visual_evidence_ready=true` means the files exist; it does not mean an AI or human already inspected them.

## Output Contract

Default sidecar:

```text
<pptx_parent>/.review/officecli-local.json
```

The sidecar records:

- adapter status and strict policy;
- PPTX SHA-256 before and after review;
- OOXML slide count and optional `render-result.json` cross-check;
- bundled renderer and PowerShell paths;
- local PDF/PNG paths and page count;
- `used_visual=false` until an agent or human inspects every PNG;
- warnings and errors.

## Decision Rules

- Missing local tools or rendering failure remains advisory unless `--strict` was explicitly requested.
- `visual_evidence_ready=true` is evidence availability, not visual acceptance.
- Inspect every rendered page before making a visual-quality claim.
- Native PowerPoint open/save/render, editability, slide count, non-blank output, and source-owned quality gates remain authoritative.
- A LibreOffice render can differ from native PowerPoint and is a supporting gate, not a replacement.

## Fix Ownership

- Main SVG pipeline: fix `spec_lock.md` or `svg_output/`, then re-export and review again.
- Native template-fill workflow: fix the template-fill source contract, then regenerate.
- Never patch only the final PPTX behind Fusion's source artifacts.

## Stop Conditions

- The exported PPTX is missing or invalid.
- LibreOffice, Poppler, or PowerShell is unavailable.
- Page count, PNG validity, or source hash verification fails.
- A fix requires changing narrative, brand, layout structure, or another source outside the selected Fusion workflow.
