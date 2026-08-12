# Fusion PPT Master v2.0.0 — Agent Audit Brief

## Objective

You are tasked with a **comprehensive audit** of `fusion-ppt-master` v2.0.0, a fused Claude Code skill that merges four existing skills into one cohesive pipeline. Your job is to find bugs, inconsistencies, missing pieces, and anything that would cause failures in real-world usage.

## What Is This Skill

`fusion-ppt-master` combines:
- **dashiai-ppt-structure** (narrative architecture, 7 story arcs)
- **huashu-design** (40 design styles, anti-slop, taste anchors)
- **guizang-ppt-skill** (page rhythm rules, layout templates)
- **ppt-master** (production engine, SVG standards, PPTX export)

The four roles are internal pipeline phases, not external skill wrappers. This is a genuine integration, not a fragile chain.

## Location

```
C:\Users\t2597\.claude\skills\fusion-ppt-master\
```

## Critical Files to Audit

### 1. SKILL.md (Entry Point)
- **Path**: `SKILL.md`
- **Check**: Version 2.0.0, 7-phase pipeline (Phase 0 through Phase 6), backward compatibility notes, execution commands, calling examples
- **Risk**: If SKILL.md references files or features that don't exist, the skill is broken from the start

### 2. Layout Index
- **Path**: `templates/layouts/layouts_index.json`
- **Check**: Both `magazine-style-a` (12 layouts) and `swiss-international` (22 layouts) sections present with correct metadata
- **Risk**: Executor queries this index to find templates — mismatched entries = missing layouts at runtime

### 3. Design Styles Index
- **Path**: `references/design-styles-index.json`
- **Check**: 20 PPT styles + 20 web styles, each with palette/typography/icon_style/rendering/palette_rec fields, anti_slop section present
- **Risk**: Strategist uses this for style recommendations — missing fields cause downstream drift

### 4. SVG Layout Templates (34 files)
- **Paths**: `templates/layouts/magazine-style-a/` (12 files), `templates/layouts/swiss-international/` (22 files)
- **Check each file for**:
  - `viewBox="0 0 1280 720"` present
  - NO `<style>` elements (comments are fine, but actual `<style>` tags are forbidden)
  - NO `class=` attributes
  - NO `<foreignObject>` elements
  - NO `<animate*>` elements
  - NO `<script>` or `<iframe>`
  - NO `<symbol>` + `<use>` pairs
  - All text as `<text>` elements
  - Sharp corners only (no border-radius)
  - Solid fills only (no rgba())
- **Risk**: Violations break ppt-master SVG standards and cause PPTX export failures

### 5. Strategist Reference
- **Path**: `references/strategist.md`
- **Check**: Eight Confirmations (a-h) present, narrative shape references, anti-slop enforcement mentions, design direction consultant mode workflow
- **Risk**: Missing confirmation steps = incomplete spec generation

### 6. Executor Reference
- **Path**: `references/executor-base.md`
- **Check**: §2.0 Expanded Layout Library documenting magazine-style-a and swiss-international families, §2.1 spec_lock re-read per page rule
- **Risk**: Executor won't know about new layouts without this documentation

### 7. Spec Lock Reference
- **Path**: `templates/spec_lock_reference.md`
- **Check**: New fields `visual_tone`, `narrative_shape`, `page_rhythm` present in YAML frontmatter section
- **Risk**: Executor reads this as the contract — missing fields cause context drift

### 8. Reference Docs (5 files)
- **Paths**:
  - `references/dashiai-narrative-shapes.md` — 7 narrative arcs + decision tree
  - `references/guizang-rhythm-guide.md` — anchor/dense/breathing rules, hero light/dark alternation
  - `references/huashu-anti-slop.md` — always-forbidden patterns table
  - `references/huashu-taste-anchors.md` — four anchor dimensions, seed combinations
  - `references/huashu-design-direction.md` — consultant mode workflow
- **Check**: All files exist, content is coherent and internally consistent with SKILL.md claims

### 9. Orchestrator Script
- **Path**: `scripts/fusion_orchestrator.py`
- **Check**: Compiles without syntax errors, implements `validate`, `migrate`, `check` subcommands, validates layouts_index.json fields, checks reference files exist
- **Risk**: Broken orchestrator = no migration path for old projects

### 10. Backward Compatibility
- **Check**: Old `deck-spec.json` deprecation noted, migration command documented, old 4 skills still referenced as available
- **Risk**: Breaking existing users

## Audit Methodology

### Phase 1: Structural Integrity
1. Verify all referenced files exist and are non-empty (> 0 bytes)
2. Parse all JSON files — confirm valid syntax
3. Compile all Python files — confirm no syntax errors
4. Run `python scripts/final_validation.py` — expect `RELEASE STATUS: PASS`
5. Run the isolated runtime form, `<skill>/.venv/Scripts/python.exe scripts/final_validation.py --runtime` on Windows (or `.venv/bin/python` on POSIX) — expect `RELEASE STATUS: PASS`

### Phase 2: Cross-Reference Consistency
1. Does SKILL.md file inventory match actual files on disk?
2. Does layouts_index.json list exactly the SVGs that exist?
3. Does design-styles-index.json have consistent field names across all 40 entries?
4. Do Strategist references to narrative shapes match dashiai-narrative-shapes.md content?
5. Do Executor layout references match what's documented in executor-base.md?

### Phase 3: SVG Standards Compliance
For all 34 new SVG templates:
1. Strip HTML comments, then scan for banned elements/attributes
2. Verify viewBox="0 0 1280 720" on every file
3. Verify all text uses `<text>` elements (no embedded HTML)
4. Check color values are solid fills (no rgba())
5. Check corners are sharp (no rx/ry on rects)

### Phase 4: Logical Consistency
1. Are the 7 pipeline phases (0 through 6) in correct serial order?
2. Does the spec_lock contract (Strategist output) match what Executor expects as input?
3. Are anti-slop rules enforced at the right pipeline stage (Strategist, not Executor)?
4. Does the design direction consultant mode have a clear entry condition (user has no style reference)?
5. Are the 7 narrative shapes mutually exclusive and collectively exhaustive for PPT use cases?

### Phase 5: Edge Cases & Failure Modes
1. What happens if a user has no source files (topic-only mode)? Is topic-research workflow accessible?
2. What happens if layouts_index.json references an SVG that doesn't exist?
3. What happens if design-styles-index.json has a style with missing palette_rec field?
4. What if spec_lock.md has visual_tone but no page_rhythm?
5. Is there any circular dependency between phases?

## Deliverable Format

Return a structured audit report:

```markdown
## Audit Summary
- Total files audited: N
- Critical issues: N
- Warnings: N
- Suggestions: N

## Critical Issues (block publication)
1. [file:line] description — impact — suggested fix

## Warnings (should fix before publication)
1. [file:line] description — impact — suggested fix

## Suggestions (nice-to-have improvements)
1. description

## Confidence Level
High / Medium / Low — reason
```

**Priority: Find real problems, not noise. A clean audit is better than a noisy one with false positives.**
