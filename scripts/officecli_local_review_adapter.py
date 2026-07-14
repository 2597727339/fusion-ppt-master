#!/usr/bin/env python3
"""Non-mutating local visual-evidence adapter for exported PPTX files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
SLIDE_PART_RE = re.compile(r"ppt/slides/slide\d+\.xml$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_slides(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return sum(1 for name in archive.namelist() if SLIDE_PART_RE.fullmatch(name))


def parse_json_output(text: str) -> Any:
    candidate = text.strip()
    if not candidate:
        raise ValueError("renderer returned no JSON output")
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("renderer output did not contain a JSON object") from None
        try:
            return json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"renderer returned invalid JSON: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
    ) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    temporary.replace(path)


def find_local_renderer(explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if os.environ.get("FUSION_LOCAL_REVIEWER"):
        candidates.append(Path(os.environ["FUSION_LOCAL_REVIEWER"]).expanduser())
    candidates.append(Path(__file__).resolve().with_name("officecli_local_review.ps1"))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def find_powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def run_process(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def compare_render_result(path: Path | None, slide_count: int) -> list[str]:
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"unable to read render result: {exc}"]
    value = data.get("slide_count") if isinstance(data, dict) else None
    if isinstance(value, (int, float)) and int(value) != slide_count:
        return [
            f"render-result slide_count {int(value)} does not match PPTX slide count {slide_count}"
        ]
    return []


def default_output_path(pptx: Path) -> Path:
    return pptx.parent / ".review" / "officecli-local.json"


def default_local_output_dir(pptx: Path) -> Path:
    return pptx.parent / ".review" / "officecli-local"


def is_png(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return False
    return (
        len(header) == 24
        and header[:8] == b"\x89PNG\r\n\x1a\n"
        and header[12:16] == b"IHDR"
    )


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def positive_timeout(value: str) -> int:
    try:
        timeout = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be an integer") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return timeout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render an exported PPTX locally without changing it. This adapter uses "
            "only the bundled PowerShell renderer, LibreOffice, and Poppler."
        )
    )
    parser.add_argument("--pptx", required=True, help="Final PPTX to inspect")
    parser.add_argument("--output", help="Review sidecar JSON path")
    parser.add_argument("--render-result", help="Optional render-result.json to cross-check")
    parser.add_argument(
        "--local-renderer",
        help="Override the bundled Unicode-safe local renderer PowerShell script",
    )
    parser.add_argument("--local-output-dir", help="Directory for local PDF/PNG evidence")
    parser.add_argument("--strict", action="store_true", help="Fail when rendering is unavailable")
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=180,
        help="Renderer timeout in seconds",
    )
    return parser


def execute(args: argparse.Namespace) -> int:
    pptx = Path(args.pptx).expanduser().resolve()
    requested_output = (
        Path(args.output).expanduser().resolve() if args.output else default_output_path(pptx)
    )
    output_conflicts_with_source = requested_output == pptx
    output = default_output_path(pptx) if output_conflicts_with_source else requested_output
    local_output = (
        Path(args.local_output_dir).expanduser().resolve()
        if args.local_output_dir
        else default_local_output_dir(pptx)
    )
    warnings: list[str] = []
    errors: list[str] = []
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "adapter_status": "initializing",
        "mode": "local",
        "strict": bool(args.strict),
        "source": str(pptx),
        "requested_output": str(requested_output),
        "sidecar_output": str(output),
        "source_sha256_before": None,
        "source_sha256_after": None,
        "source_unchanged": None,
        "slide_count": None,
        "local_renderer_path": None,
        "local_output_dir": str(local_output),
        "powershell_path": None,
        "renderer_exit_code": None,
        "used_visual": False,
        "visual_evidence_ready": False,
        "warnings": warnings,
        "errors": errors,
        "raw_result": None,
        "started_at_utc": utc_now(),
        "finished_at_utc": None,
    }

    exit_code = 0
    if not pptx.is_file() or pptx.suffix.lower() != ".pptx":
        payload["adapter_status"] = "invalid_input"
        errors.append("--pptx must point to an existing .pptx file")
        exit_code = 2
    else:
        try:
            payload["source_sha256_before"] = sha256_file(pptx)
            payload["slide_count"] = count_slides(pptx)
        except (OSError, zipfile.BadZipFile) as exc:
            payload["adapter_status"] = "invalid_input"
            errors.append(f"unable to inspect PPTX: {exc}")
            exit_code = 2

    if exit_code == 0 and output_conflicts_with_source:
        payload["adapter_status"] = "invalid_input"
        errors.append("--output must not overwrite the source PPTX")
        exit_code = 2

    if exit_code == 0 and (local_output == pptx or local_output.is_file()):
        payload["adapter_status"] = "invalid_input"
        errors.append("--local-output-dir must be a directory and not the source PPTX")
        exit_code = 2

    if exit_code == 0:
        render_result = Path(args.render_result).expanduser().resolve() if args.render_result else None
        warnings.extend(compare_render_result(render_result, int(payload["slide_count"])))
        renderer = find_local_renderer(args.local_renderer)
        powershell = find_powershell()
        if renderer is None or powershell is None:
            payload["adapter_status"] = "unavailable"
            errors.append("bundled local renderer or PowerShell is unavailable")
        else:
            payload["local_renderer_path"] = str(renderer)
            payload["powershell_path"] = powershell
            command = [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(renderer),
                "-InputFile",
                str(pptx),
                "-OutputDirectory",
                str(local_output),
            ]
            try:
                result = run_process(command, args.timeout)
                payload["renderer_exit_code"] = result.returncode
                raw = parse_json_output(result.stdout) if result.stdout.strip() else None
                payload["raw_result"] = raw
                pages = raw.get("pages", []) if isinstance(raw, dict) else []
                page_paths = [Path(str(page)).expanduser().resolve() for page in pages]
                declared_count = raw.get("page_count") if isinstance(raw, dict) else None
                slide_count = int(payload["slide_count"])
                page_count_matches = (
                    isinstance(declared_count, int)
                    and not isinstance(declared_count, bool)
                    and declared_count == slide_count
                    and len(page_paths) == slide_count
                    and len(set(page_paths)) == len(page_paths)
                )
                pages_within_output = bool(page_paths) and all(
                    is_within(page, local_output) for page in page_paths
                )
                pages_valid = bool(page_paths) and all(is_png(page) for page in page_paths)
                renderer_succeeded = (
                    isinstance(raw, dict) and str(raw.get("status", "")).lower() == "success"
                )
                if (
                    result.returncode == 0
                    and renderer_succeeded
                    and pages_within_output
                    and pages_valid
                    and page_count_matches
                ):
                    payload["adapter_status"] = "rendered_local"
                    payload["visual_evidence_ready"] = True
                    warnings.append(
                        "local PNGs are ready, but an AI or human must still inspect every page"
                    )
                else:
                    payload["adapter_status"] = "failed"
                    if not renderer_succeeded:
                        errors.append("local renderer did not report success")
                    elif page_paths and not pages_within_output:
                        errors.append("local renderer reported page images outside its output directory")
                    elif page_paths and not pages_valid:
                        errors.append("local renderer reported missing or invalid PNG page images")
                    elif page_paths and not page_count_matches:
                        errors.append("local renderer page count does not match the PPTX slide count")
                    else:
                        errors.append((result.stderr or "local renderer returned no page images")[:1000])
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                payload["adapter_status"] = "failed"
                errors.append(f"local renderer failed: {exc}")

        if args.strict and payload["adapter_status"] in {"unavailable", "failed"}:
            exit_code = 2

    if payload["source_sha256_before"] is not None and pptx.is_file():
        try:
            payload["source_sha256_after"] = sha256_file(pptx)
            payload["source_unchanged"] = (
                payload["source_sha256_before"] == payload["source_sha256_after"]
            )
            if payload["source_unchanged"] is False:
                errors.append("source PPTX changed during review")
                payload["adapter_status"] = "failed"
                payload["visual_evidence_ready"] = False
                exit_code = 2
        except OSError as exc:
            errors.append(f"unable to verify source after review: {exc}")
            payload["source_unchanged"] = False
            payload["adapter_status"] = "failed"
            payload["visual_evidence_ready"] = False
            exit_code = 2

    payload["finished_at_utc"] = utc_now()
    write_json(output, payload)
    print(
        json.dumps(
            {
                "adapter_status": payload["adapter_status"],
                "output": str(output),
                "used_visual": False,
                "visual_evidence_ready": payload["visual_evidence_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return exit_code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return execute(args)


if __name__ == "__main__":
    sys.exit(main())
