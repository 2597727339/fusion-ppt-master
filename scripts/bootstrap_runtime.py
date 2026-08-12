#!/usr/bin/env python3
"""Create an isolated Python runtime and install fusion-ppt-master dependencies."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import venv
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = SKILL_DIR / "requirements.txt"


def venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=SKILL_DIR / ".venv",
        help="Virtual environment directory (default: <skill>/.venv).",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Clear and recreate the environment before installing.",
    )
    parser.add_argument(
        "--with-node",
        action="store_true",
        help="Also install optional browser/HTML dependencies from package-lock.json.",
    )
    args = parser.parse_args()

    if not REQUIREMENTS.is_file():
        print(f"[ERROR] Missing dependency manifest: {REQUIREMENTS}", file=sys.stderr)
        return 1

    environment = args.venv.resolve()
    python = venv_python(environment)
    if args.recreate or not python.is_file():
        print(f"Creating isolated runtime: {environment}")
        venv.EnvBuilder(with_pip=True, clear=args.recreate).create(environment)

    command = [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "-r",
        str(REQUIREMENTS),
    ]
    print("Installing dependencies from requirements.txt...")
    result = subprocess.run(command, cwd=SKILL_DIR)
    if result.returncode != 0:
        return result.returncode

    check = subprocess.run([str(python), "-m", "pip", "check"], cwd=SKILL_DIR)
    if check.returncode != 0:
        return check.returncode

    if args.with_node:
        package_lock = SKILL_DIR / "package-lock.json"
        npm = shutil.which("npm")
        if not package_lock.is_file():
            print(f"[ERROR] Missing Node dependency lock: {package_lock}", file=sys.stderr)
            return 1
        if not npm:
            print("[ERROR] Node.js/npm is required for --with-node.", file=sys.stderr)
            return 1
        print("Installing optional browser/HTML dependencies from package-lock.json...")
        node_result = subprocess.run(
            [npm, "ci", "--no-audit", "--no-fund"],
            cwd=SKILL_DIR,
        )
        if node_result.returncode != 0:
            return node_result.returncode

    print(f"[OK] Runtime ready: {python}")
    if args.with_node:
        print(f"[OK] Optional Node runtime ready: {SKILL_DIR / 'node_modules'}")
    print(f"Validate with: {python} scripts/final_validation.py --runtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
