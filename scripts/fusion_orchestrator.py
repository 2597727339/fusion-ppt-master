#!/usr/bin/env python3
"""Validate and migrate projects for the standalone fusion-ppt-master skill."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
LAYOUT_INDEX = SKILL_DIR / "templates" / "layouts" / "layouts_index.json"
DESIGN_STYLES_INDEX = SKILL_DIR / "references" / "design-styles-index.json"

LAYOUT_FAMILIES = {
    "magazine-style-a": 12,
    "swiss-international": 22,
}
LAYOUT_FIELDS = {"page_type", "rhythm", "theme", "summary"}
STYLE_FIELDS = {
    "id",
    "name",
    "temperature",
    "industry_fit",
    "palette",
    "typography",
    "icon_style",
    "rendering",
    "palette_rec",
}
SPEC_SECTIONS = {
    "canvas",
    "colors",
    "typography",
    "icons",
    "images",
    "page_rhythm",
    "page_layouts",
    "page_charts",
    "forbidden",
    "visual_tone",
    "narrative_shape",
}
VALID_RHYTHMS = {"anchor", "dense", "breathing"}
REQUIRED_ASSETS = {
    "requirements.txt",
    ".env.example",
    "references/dashiai-narrative-shapes.md",
    "references/design-styles-index.json",
    "references/design-styles.md",
    "references/brand-asset-protocol.md",
    "references/guizang-rhythm-guide.md",
    "references/guizang-layouts.md",
    "references/guizang-layouts-swiss.md",
    "references/guizang-swiss-layout-lock.md",
    "references/guizang-checklist.md",
    "references/guizang-themes.md",
    "references/guizang-themes-swiss.md",
    "references/huashu-anti-slop.md",
    "references/huashu-design-direction.md",
    "references/huashu-taste-anchors.md",
    "references/strategist.md",
    "references/executor-base.md",
    "references/shared-standards.md",
    "templates/spec_lock_reference.md",
    "templates/html/guizang/template.html",
    "templates/html/guizang/template-swiss.html",
    "templates/html/guizang/assets/motion.min.js",
    "workflows/html-deck.md",
    "scripts/project_manager.py",
    "scripts/svg_quality_checker.py",
    "scripts/svg_to_pptx.py",
    "scripts/validate-guizang-swiss-deck.mjs",
}


def _load_json(path: Path) -> tuple[Any | None, list[str]]:
    if not path.is_file():
        return None, [f"Missing JSON file: {path.relative_to(SKILL_DIR)}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"Cannot parse {path.relative_to(SKILL_DIR)}: {exc}"]


def validate_layout_index() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    data, load_errors = _load_json(LAYOUT_INDEX)
    errors.extend(load_errors)
    if not isinstance(data, dict):
        return errors or ["layouts_index.json must contain a JSON object"], warnings

    for family, expected_count in LAYOUT_FAMILIES.items():
        family_data = data.get(family)
        if not isinstance(family_data, dict):
            errors.append(f"Missing layout family: {family}")
            continue
        layouts = family_data.get("layouts")
        if not isinstance(layouts, dict):
            errors.append(f"Layout family '{family}' has no layouts object")
            continue
        if len(layouts) != expected_count:
            errors.append(
                f"Layout family '{family}' expected {expected_count} entries, found {len(layouts)}"
            )

        layout_dir = SKILL_DIR / "templates" / "layouts" / family
        disk_stems = {path.stem for path in layout_dir.glob("*.svg")} if layout_dir.is_dir() else set()
        index_stems = set(layouts)
        for stem in sorted(index_stems - disk_stems):
            errors.append(f"Indexed layout missing on disk: {family}/{stem}.svg")
        for stem in sorted(disk_stems - index_stems):
            errors.append(f"SVG missing from layout index: {family}/{stem}.svg")

        for stem, metadata in layouts.items():
            if not isinstance(metadata, dict):
                errors.append(f"Layout metadata must be an object: {family}/{stem}")
                continue
            missing = LAYOUT_FIELDS - set(metadata)
            if missing:
                errors.append(
                    f"Layout {family}/{stem} missing fields: {', '.join(sorted(missing))}"
                )
            if metadata.get("rhythm") not in VALID_RHYTHMS:
                errors.append(
                    f"Layout {family}/{stem} has invalid rhythm: {metadata.get('rhythm')!r}"
                )

    return errors, warnings


def validate_design_styles_index() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    data, load_errors = _load_json(DESIGN_STYLES_INDEX)
    errors.extend(load_errors)
    if not isinstance(data, dict):
        return errors or ["design-styles-index.json must contain a JSON object"], warnings

    required_top = {"version", "source", "ppt_styles", "web_styles", "anti_slop"}
    missing_top = required_top - set(data)
    if missing_top:
        errors.append(
            "design-styles-index.json missing top-level fields: "
            + ", ".join(sorted(missing_top))
        )

    seen_ids: set[str] = set()
    for group, expected_count in (("ppt_styles", 20), ("web_styles", 20)):
        styles = data.get(group)
        if not isinstance(styles, list):
            errors.append(f"{group} must be an array")
            continue
        if len(styles) != expected_count:
            errors.append(f"{group} expected {expected_count} entries, found {len(styles)}")
        for index, style in enumerate(styles):
            if not isinstance(style, dict):
                errors.append(f"{group}[{index}] must be an object")
                continue
            missing = STYLE_FIELDS - set(style)
            label = style.get("id", f"index {index}")
            if missing:
                errors.append(f"Style {label} missing fields: {', '.join(sorted(missing))}")
            style_id = style.get("id")
            if isinstance(style_id, str):
                if style_id in seen_ids:
                    errors.append(f"Duplicate style id: {style_id}")
                seen_ids.add(style_id)
            if not isinstance(style.get("palette"), dict) or not style.get("palette"):
                errors.append(f"Style {label} must define a non-empty palette object")
            if not isinstance(style.get("typography"), dict) or not style.get("typography"):
                errors.append(f"Style {label} must define a non-empty typography object")

    anti_slop = data.get("anti_slop")
    if not isinstance(anti_slop, list) or not anti_slop:
        errors.append("anti_slop must be a non-empty array")
    else:
        joined = " ".join(str(item).lower() for item in anti_slop)
        for pattern in ("purple gradients", "emoji icons", "rounded cards"):
            if pattern not in joined:
                errors.append(f"anti_slop missing expected guardrail: {pattern}")

    return errors, warnings


def validate_skill_assets() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_ASSETS):
        path = SKILL_DIR / relative
        if not path.is_file():
            errors.append(f"Missing required skill asset: {relative}")
        elif path.stat().st_size == 0:
            errors.append(f"Required skill asset is empty: {relative}")
    return errors, []


def _section_names(content: str) -> set[str]:
    return {
        match.group(1).strip().lower()
        for match in re.finditer(r"^##\s+([A-Za-z0-9_-]+)\s*$", content, re.MULTILINE)
    }


def validate_spec_lock(project_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    spec_lock = project_path / "spec_lock.md"
    if not spec_lock.is_file():
        return ["spec_lock.md not found"], warnings

    try:
        content = spec_lock.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Cannot read spec_lock.md: {exc}"], warnings

    missing_sections = SPEC_SECTIONS - _section_names(content)
    if missing_sections:
        errors.append(
            "spec_lock.md missing sections: " + ", ".join(sorted(missing_sections))
        )

    rhythm_match = re.search(
        r"^##\s+page_rhythm\s*$\n(.*?)(?=^##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    rhythms: dict[str, str] = {}
    if rhythm_match:
        for page, rhythm in re.findall(
            r"^\s*-\s*(P\d{2,3})\s*:\s*([A-Za-z_-]+)\s*$",
            rhythm_match.group(1),
            re.MULTILINE,
        ):
            rhythms[page.upper()] = rhythm.lower()
    if not rhythms:
        errors.append("spec_lock.md page_rhythm has no PNN entries")
    for page, rhythm in rhythms.items():
        if rhythm not in VALID_RHYTHMS:
            errors.append(f"spec_lock.md {page} has invalid rhythm: {rhythm}")

    return errors, warnings


def validate_project(project_path: Path) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not project_path.exists():
        return False, [f"Project path does not exist: {project_path}"], warnings
    if not project_path.is_dir():
        return False, [f"Project path is not a directory: {project_path}"], warnings

    for validator in (
        validate_skill_assets,
        validate_layout_index,
        validate_design_styles_index,
    ):
        current_errors, current_warnings = validator()
        errors.extend(current_errors)
        warnings.extend(current_warnings)

    current_errors, current_warnings = validate_spec_lock(project_path)
    errors.extend(current_errors)
    warnings.extend(current_warnings)
    return not errors, errors, warnings


def _font_stack(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if "," in text:
        return text
    return f'"{text}", "{fallback}"'


def _infer_rhythm(slide: dict[str, Any]) -> str:
    slide_type = str(slide.get("type", "")).lower()
    layout = slide.get("layout") if isinstance(slide.get("layout"), dict) else {}
    density = str(layout.get("density", "")).lower()
    if slide_type in {"cover", "chapter", "chapter_divider", "toc", "agenda", "end", "closing"}:
        return "anchor"
    if density in {"low", "breathing"} or slide_type in {
        "quote",
        "statement",
        "fullbleed_image",
        "hero_question",
    }:
        return "breathing"
    return "dense"


def _infer_narrative_shape(old_spec: dict[str, Any]) -> str:
    meta = old_spec.get("meta") if isinstance(old_spec.get("meta"), dict) else {}
    scenario = str(meta.get("scenario", "")).lower()
    mapping = {
        "training": "teaching-narrative",
        "lesson": "teaching-narrative",
        "fundraising": "investment-case",
        "pitch": "investment-case",
        "operating_review": "operating-review",
        "management_report": "strategic-recommendation",
        "proposal": "proposal",
        "launch": "launch-story",
    }
    return mapping.get(scenario, "problem-to-solution")


def migrate_old_project(
    old_path: Path,
    new_path: Path | None = None,
    *,
    force: bool = False,
) -> Path:
    if not old_path.is_dir():
        raise ValueError(f"Old project not found: {old_path}")

    destination = new_path or old_path
    if new_path is not None and new_path.resolve() != old_path.resolve():
        if new_path.exists():
            raise ValueError(f"Migration destination already exists: {new_path}")
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(old_path, new_path)

    deck_spec = destination / "deck-spec.json"
    spec_lock = destination / "spec_lock.md"
    if not deck_spec.is_file():
        raise ValueError(f"deck-spec.json not found: {deck_spec}")
    if spec_lock.exists() and not force:
        raise ValueError(f"spec_lock.md already exists: {spec_lock} (use --force to replace)")

    try:
        old_spec = json.loads(deck_spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot parse deck-spec.json: {exc}") from exc

    design = old_spec.get("design_system") if isinstance(old_spec.get("design_system"), dict) else {}
    colors = old_spec.get("colors") if isinstance(old_spec.get("colors"), dict) else {}
    colors = colors or (design.get("color_palette") if isinstance(design.get("color_palette"), dict) else {})
    typography = old_spec.get("typography") if isinstance(old_spec.get("typography"), dict) else {}
    typography = typography or (design.get("typography") if isinstance(design.get("typography"), dict) else {})
    intent = old_spec.get("intent") if isinstance(old_spec.get("intent"), dict) else {}
    slides = old_spec.get("slides") if isinstance(old_spec.get("slides"), list) else []

    rhythm_lines: list[str] = []
    for position, raw_slide in enumerate(slides, 1):
        slide = raw_slide if isinstance(raw_slide, dict) else {}
        raw_index = slide.get("index", position)
        try:
            page_number = int(raw_index)
        except (TypeError, ValueError):
            page_number = position
        rhythm_lines.append(f"- P{page_number:02d}: {_infer_rhythm(slide)}")
    if not rhythm_lines:
        rhythm_lines.append("- P01: anchor")

    narrative_shape = _infer_narrative_shape(old_spec)
    thesis = str(
        intent.get("primary_goal")
        or intent.get("desired_action")
        or "Review migrated content and confirm the primary decision."
    )

    lines = [
        "# Execution Lock",
        "",
        "## canvas",
        f'- viewBox: {old_spec.get("viewBox", "0 0 1280 720")}',
        f'- format: {old_spec.get("format", "PPT 16:9")}',
        "",
        "## colors",
        f'- bg: {colors.get("bg", colors.get("background", "#FFFFFF"))}',
        f'- primary: {colors.get("primary", colors.get("text_primary", "#0A0A0A"))}',
        f'- accent: {colors.get("accent", "#FF6B2C")}',
        f'- text: {colors.get("text", colors.get("text_primary", "#0A0A0A"))}',
        "",
        "## typography",
        f'- title_family: {_font_stack(typography.get("title_font") or typography.get("title"), "Arial")}',
        f'- body_family: {_font_stack(typography.get("body_font") or typography.get("body"), "Microsoft YaHei")}',
        f'- font_family: {_font_stack(typography.get("body_font") or typography.get("body"), "Microsoft YaHei")}',
        f'- body: {typography.get("body_size", 22)}',
        "",
        "## icons",
        "- library: tabler-outline",
        "- stroke_width: 2",
        "",
        "## images",
        "",
        "## page_rhythm",
        *rhythm_lines,
        "",
        "## page_layouts",
        "",
        "## page_charts",
        "",
        "## forbidden",
        "- rgba()",
        "- <style>, class, <foreignObject>, textPath, @font-face, <animate*>, <script>, <iframe>, <symbol>+<use>",
        "",
        "## visual_tone",
        f'- tone: {intent.get("tone", "professional, restrained, editable-first")}',
        "- anti_slop: no generic purple gradients, no emoji icons, no uniform card-grid density",
        "",
        "## narrative_shape",
        f"- shape: {narrative_shape}",
        f"- thesis: {thesis}",
        "- migration_status: review-required",
        "",
    ]
    spec_lock.write_text("\n".join(str(line) for line in lines), encoding="utf-8")
    return destination


def _print_report(errors: list[str], warnings: list[str]) -> None:
    if errors:
        print(f"\n[ERROR] ({len(errors)})")
        for item in errors:
            print(f"  - {item}")
    if warnings:
        print(f"\n[WARN] ({len(warnings)})")
        for item in warnings:
            print(f"  - {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("validate", "check"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("project_path", type=Path)

    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--from", dest="old_path", type=Path, required=True)
    migrate_parser.add_argument("--to", dest="new_path", type=Path)
    migrate_parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command in {"validate", "check"}:
        ok, errors, warnings = validate_project(args.project_path)
        heading = "Fusion Orchestrator Validation" if args.command == "validate" else "Fusion Orchestrator Check"
        print(f"\n{heading}\n{'=' * 50}")
        _print_report(errors, warnings)
        if ok:
            print("\n[PASS] Skill assets and project contract are valid.")
            return 0
        print("\n[FAIL] Fix the errors above before proceeding.")
        return 1

    try:
        destination = migrate_old_project(
            args.old_path,
            args.new_path,
            force=args.force,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] Migration complete: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
