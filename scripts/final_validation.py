#!/usr/bin/env python3
"""Release validation for fusion-ppt-master v2.0.0."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import fusion_orchestrator as orchestrator  # noqa: E402
from fusion_orchestrator import (  # noqa: E402
    validate_design_styles_index,
    validate_layout_index,
    validate_skill_assets,
)


LAYOUT_FAMILIES = {
    "magazine-style-a": 12,
    "swiss-international": 22,
}
BANNED_ELEMENTS = {
    "style",
    "foreignObject",
    "script",
    "iframe",
    "set",
    "linearGradient",
    "radialGradient",
}
REQUIRED_SKILL_ROUTES = {
    "workflows/topic-research.md",
    "references/dashiai-narrative-shapes.md",
    "references/huashu-design-direction.md",
    "references/huashu-anti-slop.md",
    "references/guizang-rhythm-guide.md",
    "references/strategist.md",
    "references/executor-base.md",
    "references/shared-standards.md",
    "workflows/html-deck.md",
    "scripts/finalize_svg.py",
    "scripts/svg_to_pptx.py",
}
RUNTIME_IMPORTS = {
    "pptx": "python-pptx",
    "PIL": "Pillow",
    "fitz": "PyMuPDF",
    "mammoth": "mammoth",
    "markdownify": "markdownify",
    "ebooklib": "ebooklib",
    "nbconvert": "nbconvert",
    "openpyxl": "openpyxl",
    "requests": "requests",
    "bs4": "beautifulsoup4",
    "google.genai": "google-genai",
    "flask": "flask",
    "svglib": "svglib",
    "reportlab": "reportlab",
    "numpy": "numpy",
    "edge_tts": "edge-tts",
}
EXCLUDED_PARTS = {".venv", "venv", "node_modules", "__pycache__", ".git"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".html", ".js", ".mjs", ".cjs"}
SOURCE_SKILL_NAMES = {
    "huashu-design",
    "guizang-ppt-skill",
    "dashiai-ppt-structure",
    "ppt-master",
}
STALE_PATH_ALIASES = {
    "references/themes.md",
    "references/themes-swiss.md",
    "references/layouts-swiss.md",
    "references/swiss-layout-lock.md",
    "references/swiss-map-component.md",
    "references/screenshot-framing.md",
    "scripts/validate-swiss-deck.mjs",
    "assets/template.html",
    "assets/template-swiss.html",
}


class Validator:
    def __init__(self) -> None:
        self.passed = 0
        self.total = 0
        self.errors: list[str] = []

    def check(self, label: str, condition: bool, detail: str | None = None) -> None:
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  [PASS] {label}")
            return
        message = label if not detail else f"{label}: {detail}"
        self.errors.append(message)
        print(f"  [FAIL] {message}")

    def extend(self, category: str, errors: list[str]) -> None:
        self.check(category, not errors, "; ".join(errors) if errors else None)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _source_files(root: Path, pattern: str) -> list[Path]:
    return [
        path
        for path in root.rglob(pattern)
        if not EXCLUDED_PARTS.intersection(path.relative_to(SKILL_DIR).parts)
    ]


def _text_files() -> list[Path]:
    return [
        path
        for path in _source_files(SKILL_DIR, "*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    ]


def _audited_text_files() -> list[Path]:
    self_audit_files = {
        "scripts/audit_brief.md",
        "scripts/final_validation.py",
    }
    return [
        path
        for path in _text_files()
        if path.relative_to(SKILL_DIR).as_posix() not in self_audit_files
        and not path.name.startswith("AUDIT_REPORT")
    ]


def validate_json_and_python(validator: Validator) -> None:
    print("\n[1] JSON and Python integrity")
    json_files = sorted(_source_files(SKILL_DIR, "*.json"))
    json_errors: list[str] = []
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            json_errors.append(f"{path.relative_to(SKILL_DIR)} ({exc})")
    validator.check(
        f"All {len(json_files)} JSON files parse",
        not json_errors,
        "; ".join(json_errors),
    )

    python_files = sorted(_source_files(SCRIPT_DIR, "*.py"))
    compile_errors: list[str] = []
    for path in python_files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            compile_errors.append(f"{path.relative_to(SKILL_DIR)} ({exc})")
    validator.check(
        f"All {len(python_files)} Python files compile",
        not compile_errors,
        "; ".join(compile_errors),
    )


def validate_assets_and_indexes(validator: Validator) -> None:
    print("\n[2] Assets and indexes")
    errors, _warnings = validate_skill_assets()
    validator.extend("Required standalone assets are present", errors)
    errors, _warnings = validate_layout_index()
    validator.extend("Layout index matches layout files and metadata", errors)
    errors, _warnings = validate_design_styles_index()
    validator.extend("Design style index has 20+20 complete unique styles", errors)

    zero_files = [
        str(path.relative_to(SKILL_DIR))
        for path in _source_files(SKILL_DIR, "*")
        if path.is_file() and path.stat().st_size == 0
    ]
    validator.check("No zero-byte files", not zero_files, ", ".join(zero_files))

    showcases = sorted((SKILL_DIR / "assets" / "showcases").rglob("*"))
    showcase_files = [path for path in showcases if path.is_file()]
    validator.check(
        "Huashu visual direction showcase library has 49 local files",
        len(showcase_files) == 49,
        f"found {len(showcase_files)}",
    )

    layout_data = json.loads(
        (SKILL_DIR / "templates" / "layouts" / "layouts_index.json").read_text(
            encoding="utf-8"
        )
    )
    magazine_source = layout_data.get("magazine-style-a", {}).get("source", "")
    swiss_source = layout_data.get("swiss-international", {}).get("source", "")
    validator.check(
        "Fused layout metadata uses local sources and correct counts",
        "12 PPTX SVG layouts" in magazine_source
        and "22 PPTX SVG layouts" in swiss_source
        and not SOURCE_SKILL_NAMES.intersection(
            re.findall(r"[a-z0-9-]+", f"{magazine_source} {swiss_source}".lower())
        ),
        f"magazine={magazine_source!r}; swiss={swiss_source!r}",
    )


def validate_svg_templates(validator: Validator) -> None:
    print("\n[3] SVG template compliance")
    all_files: list[Path] = []
    for family, expected in LAYOUT_FAMILIES.items():
        files = sorted((SKILL_DIR / "templates" / "layouts" / family).glob("*.svg"))
        validator.check(f"{family} has {expected} SVG files", len(files) == expected)
        all_files.extend(files)

    issues: list[str] = []
    for path in all_files:
        relative = path.relative_to(SKILL_DIR)
        try:
            raw = path.read_text(encoding="utf-8")
            root = ET.fromstring(raw)
        except (OSError, ET.ParseError) as exc:
            issues.append(f"{relative}: XML parse error: {exc}")
            continue

        if root.attrib.get("viewBox") != "0 0 1280 720":
            issues.append(f"{relative}: viewBox must be 0 0 1280 720")
        if root.attrib.get("width") not in {None, "1280"}:
            issues.append(f"{relative}: width must be 1280")
        if root.attrib.get("height") not in {None, "720"}:
            issues.append(f"{relative}: height must be 720")

        comment_free = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
        has_symbol = False
        has_use = False
        for element in root.iter():
            name = _local_name(element.tag)
            if name == "symbol":
                has_symbol = True
            if name == "use":
                has_use = True
            if name in BANNED_ELEMENTS or name.startswith("animate"):
                issues.append(f"{relative}: banned element <{name}>")
            if name in {"html", "body", "div", "span"}:
                issues.append(f"{relative}: embedded HTML element <{name}>")
            if "class" in element.attrib:
                issues.append(f"{relative}: class attribute on <{name}>")
            if "style" in element.attrib:
                issues.append(f"{relative}: style attribute on <{name}>")
            if name == "rect":
                for attr in ("rx", "ry"):
                    value = element.attrib.get(attr)
                    if value not in {None, "", "0", "0.0"}:
                        issues.append(f"{relative}: rounded rect {attr}={value}")
            for attr, value in element.attrib.items():
                if re.search(r"rgba\s*\(", value, re.IGNORECASE):
                    issues.append(f"{relative}: rgba() in {attr}")
        if has_symbol and has_use:
            issues.append(f"{relative}: symbol+use pair")
        if re.search(r"rgba\s*\(", comment_free, re.IGNORECASE):
            issues.append(f"{relative}: rgba() in rendered content")

    validator.check(
        f"All {len(all_files)} fused SVG templates meet strict rules",
        not issues,
        "; ".join(sorted(set(issues))),
    )

    checker = SCRIPT_DIR / "svg_quality_checker.py"
    for family in LAYOUT_FAMILIES:
        result = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(SKILL_DIR / "templates" / "layouts" / family),
                "--template-mode",
            ],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = (result.stdout + result.stderr).strip()
        warning_counts = [
            int(value)
            for value in re.findall(
                r"(?:With warnings:\s*|Warnings \()(\d+)", combined
            )
        ]
        validator.check(
            f"Official template checker passes {family}",
            result.returncode == 0 and not any(warning_counts),
            combined[-1200:] if combined else f"exit {result.returncode}",
        )


def _markdown_links() -> list[tuple[Path, str]]:
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    broken: list[tuple[Path, str]] = []
    for path in _source_files(SKILL_DIR, "*.md"):
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target = match.group(1).strip().strip("<>")
            if re.match(r"^(?:https?://|mailto:|#|data:)", target):
                continue
            target = re.split(r'\s+"', target, maxsplit=1)[0]
            path_text = target.split("#", 1)[0]
            if not path_text:
                continue
            resolved = (path.parent / path_text).resolve()
            if not resolved.exists():
                broken.append((path, target))
    return broken


def validate_docs_and_independence(validator: Validator) -> None:
    print("\n[4] Documentation and independence")
    broken = _markdown_links()
    validator.check(
        "All local Markdown links resolve",
        not broken,
        "; ".join(f"{p.relative_to(SKILL_DIR)} -> {target}" for p, target in broken),
    )

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for route in sorted(REQUIRED_SKILL_ROUTES):
        validator.check(f"SKILL.md routes to {route}", route in skill_text)

    phases = sorted({int(value) for value in re.findall(r"Phase\s+([0-6])\s*:", skill_text)})
    validator.check("SKILL.md defines exactly Phase 0 through Phase 6", phases == list(range(7)))

    external_path_pattern = re.compile(
        r"(?:(?:\.codex|\.claude|\.agents)[\\/]+)?skills[\\/]+"
        r"(?:huashu-design|guizang-ppt-skill|dashiai-ppt-structure|ppt-master)"
        r"(?:[\\/]|\b)",
        re.IGNORECASE,
    )
    external_refs: list[str] = []
    for path in _audited_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if external_path_pattern.search(text):
            external_refs.append(str(path.relative_to(SKILL_DIR)))
    validator.check(
        "No runtime path references to the four source skills",
        not external_refs,
        ", ".join(external_refs),
    )

    hardcoded_user_paths: list[str] = []
    for path in _audited_text_files():
        relative = path.relative_to(SKILL_DIR)
        text = path.read_text(encoding="utf-8", errors="replace")
        windows_user = re.search(r"[A-Za-z]:\\Users\\[^<\s\\]+\\", text)
        unix_user = re.search(r"/Users/(?!me(?:/|\b))[^/\s]+/", text)
        if windows_user or unix_user:
            hardcoded_user_paths.append(str(relative))
    validator.check(
        "No machine-specific user paths in package text",
        not hardcoded_user_paths,
        ", ".join(hardcoded_user_paths),
    )

    stale_refs: list[str] = []
    for path in _audited_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for alias in STALE_PATH_ALIASES:
            if alias in text:
                stale_refs.append(f"{path.relative_to(SKILL_DIR)} -> {alias}")
    validator.check(
        "No stale pre-fusion path aliases",
        not stale_refs,
        "; ".join(sorted(stale_refs)),
    )

    literal_pattern = re.compile(
        r"(?<![A-Za-z0-9_.-])"
        r"((?:references|scripts|templates|workflows|assets)/"
        r"[A-Za-z0-9_.\-/]+\.(?:md|json|py|mjs|js|cjs|html|svg|webp))"
    )
    output_relative = {"assets/motion.min.js", "templates/design_spec.md"}
    broken_literals: list[str] = []
    for path in _audited_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in set(literal_pattern.findall(text)):
            if token in output_relative or "..." in token:
                continue
            if not (SKILL_DIR / Path(token)).exists():
                broken_literals.append(f"{path.relative_to(SKILL_DIR)} -> {token}")
    validator.check(
        "Operational path literals resolve inside the package",
        not broken_literals,
        "; ".join(sorted(broken_literals)),
    )

    html_namespace = "HTML Swiss 只能通过" in skill_text
    pptx_namespace = "PPTX 专用 basename" in skill_text
    validator.check(
        "Swiss HTML layout IDs and PPTX SVG basenames are separate contracts",
        html_namespace and pptx_namespace,
    )

    links = [path for path in _source_files(SKILL_DIR, "*") if path.is_symlink()]
    validator.check(
        "Skill package contains no symbolic-link dependencies",
        not links,
        ", ".join(str(path.relative_to(SKILL_DIR)) for path in links),
    )

    project_manager_text = (SCRIPT_DIR / "project_manager.py").read_text(encoding="utf-8")
    config_text = (SCRIPT_DIR / "config.py").read_text(encoding="utf-8")
    validator.check(
        "Project and config roots stay inside the standalone skill",
        "REPO_ROOT = SKILL_DIR" in project_manager_text
        and "REPO_ROOT = PROJECT_ROOT" in config_text
        and "REPO_ROOT = SKILL_DIR.parent.parent" not in project_manager_text
        and "REPO_ROOT = PROJECT_ROOT.parent.parent" not in config_text,
    )

    strategist_text = (SKILL_DIR / "references" / "strategist.md").read_text(
        encoding="utf-8"
    )
    confirmations = re.findall(
        r"^###\s+([a-h])\.\s+.+$",
        strategist_text,
        re.MULTILINE,
    )
    validator.check(
        "Strategist defines exactly confirmations a through h",
        confirmations == list("abcdefgh"),
        f"found {confirmations}",
    )
    validator.check(
        "Strategist icon options honor the anti-slop contract",
        "Built-in SVG icon library" in strategist_text
        and "Do not offer emoji" in strategist_text
        and not re.search(r"\|\s*\*\*[A-D]\*\*\s*\|\s*Emoji\s*\|", strategist_text),
    )

    spec_reference = (SKILL_DIR / "templates" / "spec_lock_reference.md").read_text(
        encoding="utf-8"
    )
    spec_headings = orchestrator._section_names(spec_reference)
    executor_text = (SKILL_DIR / "references" / "executor-base.md").read_text(
        encoding="utf-8"
    )
    narrative_text = (
        SKILL_DIR / "references" / "dashiai-narrative-shapes.md"
    ).read_text(encoding="utf-8")
    narrative_shapes = re.findall(
        r"^###\s+[1-7]\.\s+([a-z][a-z-]+)\s*$",
        narrative_text,
        re.MULTILINE,
    )
    validator.check(
        "Strategist and Executor share the complete spec_lock contract",
        orchestrator.SPEC_SECTIONS.issubset(spec_headings)
        and "before every SVG page" in spec_reference
        and "Before drawing each page" in executor_text,
        "missing sections: "
        + ", ".join(sorted(orchestrator.SPEC_SECTIONS - spec_headings)),
    )
    validator.check(
        "Narrative reference defines exactly seven primary shapes",
        len(narrative_shapes) == 7 and len(set(narrative_shapes)) == 7,
        f"found {narrative_shapes}",
    )


def validate_html_assets(validator: Validator) -> None:
    print("\n[5] HTML branch integrity")
    template = SKILL_DIR / "templates" / "html" / "guizang" / "template-swiss.html"
    motion = SKILL_DIR / "templates" / "html" / "guizang" / "assets" / "motion.min.js"
    html = template.read_text(encoding="utf-8") if template.is_file() else ""
    comment_free = re.sub(r"<!--[\s\S]*?-->", "", html)
    section_tags = re.findall(
        r'<section\b[^>]*class="[^"]*\bslide\b[^"]*"[^>]*>', comment_free
    )
    layouts = [
        match.group(1)
        for tag in section_tags
        if (match := re.search(r'\bdata-layout="([^"]+)"', tag))
    ]
    validator.check(
        "Swiss seed has registered cover and closing layout IDs",
        layouts == ["SWISS-COVER-ASCII", "SWISS-CLOSING-ASCII"],
        f"found {layouts}",
    )
    validator.check(
        "HTML seed local animation runtime is bundled",
        motion.is_file() and motion.stat().st_size > 0,
        str(motion.relative_to(SKILL_DIR)),
    )


def validate_failure_detection(validator: Validator) -> None:
    print("\n[6] Contract failure detection")
    original_root = orchestrator.SKILL_DIR
    original_layout_index = orchestrator.LAYOUT_INDEX
    original_style_index = orchestrator.DESIGN_STYLES_INDEX

    with tempfile.TemporaryDirectory(prefix="fusion-ppt-contract-") as temp_dir:
        fixture_root = Path(temp_dir)
        fixture_layouts = fixture_root / "templates" / "layouts"
        fixture_references = fixture_root / "references"
        shutil.copytree(SKILL_DIR / "templates" / "layouts", fixture_layouts)
        fixture_references.mkdir(parents=True)
        shutil.copy2(
            SKILL_DIR / "references" / "design-styles-index.json",
            fixture_references / "design-styles-index.json",
        )

        orchestrator.SKILL_DIR = fixture_root
        orchestrator.LAYOUT_INDEX = fixture_layouts / "layouts_index.json"
        orchestrator.DESIGN_STYLES_INDEX = fixture_references / "design-styles-index.json"
        try:
            (fixture_layouts / "magazine-style-a" / "01_cover.svg").unlink()
            layout_errors, _warnings = orchestrator.validate_layout_index()
            validator.check(
                "Layout validator rejects an indexed SVG missing on disk",
                any("Indexed layout missing on disk" in error for error in layout_errors),
                "; ".join(layout_errors),
            )

            style_data = json.loads(
                orchestrator.DESIGN_STYLES_INDEX.read_text(encoding="utf-8")
            )
            style_data["ppt_styles"][0].pop("palette_rec", None)
            orchestrator.DESIGN_STYLES_INDEX.write_text(
                json.dumps(style_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            style_errors, _warnings = orchestrator.validate_design_styles_index()
            validator.check(
                "Style validator rejects a missing palette_rec field",
                any("palette_rec" in error for error in style_errors),
                "; ".join(style_errors),
            )

            project = fixture_root / "project"
            project.mkdir()
            sections_without_rhythm = sorted(orchestrator.SPEC_SECTIONS - {"page_rhythm"})
            project.joinpath("spec_lock.md").write_text(
                "# Execution Lock\n\n"
                + "\n\n".join(f"## {section}\n- test: value" for section in sections_without_rhythm)
                + "\n",
                encoding="utf-8",
            )
            spec_errors, _warnings = orchestrator.validate_spec_lock(project)
            validator.check(
                "Spec validator rejects a missing page_rhythm section",
                any("page_rhythm" in error for error in spec_errors),
                "; ".join(spec_errors),
            )
        finally:
            orchestrator.SKILL_DIR = original_root
            orchestrator.LAYOUT_INDEX = original_layout_index
            orchestrator.DESIGN_STYLES_INDEX = original_style_index


def validate_runtime(validator: Validator) -> None:
    print("\n[7] Runtime dependencies")
    missing: list[str] = []
    for module, package in RUNTIME_IMPORTS.items():
        try:
            importlib.import_module(module)
        except Exception as exc:  # dependency imports can fail transitively
            missing.append(f"{package} ({exc})")
    validator.check("Core and optional production dependencies import", not missing, "; ".join(missing))

    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "svg_to_pptx.py"), "--help"],
        cwd=SKILL_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    validator.check(
        "PPTX exporter starts",
        result.returncode == 0,
        (result.stdout + result.stderr).strip()[-1200:],
    )

    project_help = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "project_manager.py"), "init", "--help"],
        cwd=SKILL_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    project_help_output = (project_help.stdout + project_help.stderr).strip()
    validator.check(
        "Project manager subcommand help has no creation side effect",
        project_help.returncode == 0 and "Project created:" not in project_help_output,
        project_help_output[-1200:],
    )

    optional_python_entrypoints = [
        "native_enhance_pptx.py",
        "beautify_inventory.py",
        "pptx_intake.py",
        "extract_svg_assets.py",
    ]
    entrypoint_errors: list[str] = []
    for filename in optional_python_entrypoints:
        check = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / filename), "--help"],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check.returncode != 0:
            entrypoint_errors.append(
                f"{filename}: {(check.stdout + check.stderr).strip()[-600:]}"
            )
    validator.check(
        "Bundled optional Python workflow entrypoints start",
        not entrypoint_errors,
        "; ".join(entrypoint_errors),
    )

    node = shutil.which("node")
    npm = shutil.which("npm")
    validator.check(
        "Node.js and npm are available for HTML/browser workflows",
        bool(node and npm),
        f"node={node!r}; npm={npm!r}",
    )
    node_scripts = [
        SCRIPT_DIR / "validate-guizang-swiss-deck.mjs",
        SCRIPT_DIR / "html2pptx.js",
        SCRIPT_DIR / "export_deck_pdf.mjs",
        SCRIPT_DIR / "export_deck_pptx.mjs",
        SCRIPT_DIR / "export_deck_stage_pdf.mjs",
        SCRIPT_DIR / "gen_deck_thumbs.mjs",
    ]
    node_errors: list[str] = []
    if node:
        for script in node_scripts:
            check = subprocess.run(
                [node, "--check", str(script)],
                cwd=SKILL_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if check.returncode != 0:
                node_errors.append(
                    f"{script.name}: {(check.stdout + check.stderr).strip()[-600:]}"
                )
    else:
        node_errors.append("node executable not found")
    validator.check(
        "All bundled Node workflow scripts parse",
        not node_errors,
        "; ".join(node_errors),
    )

    swiss_check = None
    if node:
        swiss_check = subprocess.run(
            [
                node,
                str(SCRIPT_DIR / "validate-guizang-swiss-deck.mjs"),
                str(SKILL_DIR / "templates" / "html" / "guizang" / "template-swiss.html"),
            ],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    validator.check(
        "Bundled Swiss HTML seed passes its production validator",
        swiss_check is not None and swiss_check.returncode == 0,
        "node unavailable"
        if swiss_check is None
        else (swiss_check.stdout + swiss_check.stderr).strip(),
    )

    node_modules = SKILL_DIR / "node_modules"
    npm_check = None
    if npm and node_modules.is_dir():
        npm_check = subprocess.run(
            [npm, "ls", "--depth=0"],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    validator.check(
        "Locked optional Node dependencies are installed and coherent",
        npm_check is not None and npm_check.returncode == 0,
        "run scripts/bootstrap_runtime.py --with-node"
        if npm_check is None
        else (npm_check.stdout + npm_check.stderr).strip()[-1200:],
    )

    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        cwd=SKILL_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    validator.check(
        "Python environment has no broken requirements",
        pip_check.returncode == 0,
        (pip_check.stdout + pip_check.stderr).strip(),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime",
        action="store_true",
        help="Also verify installed Python dependencies and exporter startup.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    os.chdir(SKILL_DIR)
    validator = Validator()

    print("=" * 68)
    print("FUSION-PPT-MASTER v2.0.0 RELEASE VALIDATION")
    print(f"Skill directory: {SKILL_DIR}")
    print("=" * 68)

    validate_json_and_python(validator)
    validate_assets_and_indexes(validator)
    validate_svg_templates(validator)
    validate_docs_and_independence(validator)
    validate_html_assets(validator)
    validate_failure_detection(validator)
    if args.runtime:
        validate_runtime(validator)

    print("\n" + "=" * 68)
    print(f"RESULT: {validator.passed}/{validator.total} checks passed")
    if validator.errors:
        print(f"ERRORS: {len(validator.errors)}")
        for error in validator.errors:
            print(f"  - {error}")
        print("RELEASE STATUS: BLOCKED")
        return 1
    print("RELEASE STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
