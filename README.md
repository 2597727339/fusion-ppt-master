# fusion-ppt-master

`fusion-ppt-master` is a self-contained Claude Code skill for narrative planning, visual direction, page rhythm, SVG production, and editable PPTX export.

It internalizes four capability areas without calling external skill directories at runtime:

| Capability | Internal responsibility |
|---|---|
| Narrative architecture | Audience, decision, thesis, evidence gaps, seven primary story shapes |
| Visual direction | Design context, 40-style catalog, brand assets, anti-slop guardrails, taste anchors |
| Page rhythm | Anchor/dense/breathing sequencing plus Magazine and Swiss layout families |
| Production | Source conversion, project management, SVG checks, post-processing, editable PPTX export |

## Default behavior

- Editable PPTX is the default deliverable.
- HTML is used only when explicitly requested and follows `workflows/html-deck.md`.
- `spec_lock.md` is the machine-readable contract between planning and execution.
- Full-slide screenshots and rasterized body text are not acceptable substitutes for editable output.

## Pipeline

```text
Phase 0  Source ingestion
Phase 1  Narrative architecture
Phase 2  Design direction and page rhythm
Phase 3  Strategist and eight user confirmations
Phase 4  Conditional image acquisition
Phase 5  Sequential SVG execution and quality gate
Phase 6  Post-processing and editable PPTX export
```

See `SKILL.md` for the mandatory reads, blocking confirmation point, artifacts, and commands for every phase.

## Installation

Place the directory at:

```text
~/.claude/skills/fusion-ppt-master/
```

Create its isolated Python runtime once:

```bash
python scripts/bootstrap_runtime.py
```

For explicit HTML/browser export utilities, install the optional locked Node runtime at the same time:

```bash
python scripts/bootstrap_runtime.py --with-node
```

The generated `.venv` is local installation state and is excluded from release packages by `.gitignore`.

## Validation

The full release gate expects both locked Python and Node dependencies. Run `python scripts/bootstrap_runtime.py --with-node` first.

Windows:

```powershell
.venv\Scripts\python.exe scripts\final_validation.py --runtime
```

macOS/Linux:

```bash
.venv/bin/python scripts/final_validation.py --runtime
```

The command exits nonzero on missing assets, broken links, invalid JSON/Python/Node scripts, index drift, noncompliant SVG templates, external source-skill paths, missing dependencies, HTML seed failure, or exporter startup failure.

## Layout resources

| Family | Count | Directory |
|---|---:|---|
| Base production layouts | existing library | `templates/layouts/` |
| Magazine Style A | 12 | `templates/layouts/magazine-style-a/` |
| Swiss International | 22 | `templates/layouts/swiss-international/` |

The 34 fused SVG layouts use a 1280 x 720 viewBox and are checked both by the release validator and the production SVG quality checker.

## Usage

```text
/fusion-ppt-master Create a fundraising deck and deliver an editable PPTX
/fusion-ppt-master Create an annual report in Swiss International style
/fusion-ppt-master I have no style reference; show three distinct directions
/fusion-ppt-master Convert this PDF into an editable PPTX
/fusion-ppt-master Explicitly deliver a single-file HTML presentation
```

## Migration

```bash
<python> scripts/fusion_orchestrator.py migrate --from <old_project_path>
<python> scripts/fusion_orchestrator.py validate <old_project_path>
```

Migration preserves `deck-spec.json`, creates `spec_lock.md`, and marks the mapped narrative as review-required.

## Independence boundary

The package includes its scripts, templates, references, HTML seeds, dependency manifest, and environment example. It must not rely on junctions, wrappers, or runtime reads from separate narrative, design, rhythm, or PPT production skill folders.

## License

MIT License. See `LICENSE`.
