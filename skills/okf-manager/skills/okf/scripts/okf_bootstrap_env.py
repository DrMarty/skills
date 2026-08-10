#!/usr/bin/env python3
"""Create or repair the OKF Manager user-local worker environment."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

REQUIRED_IMPORTS = {
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "lxml": "lxml",
    "requests": "requests",
    "markdownify": "markdownify",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_data_root() -> Path:
    override = os.environ.get("OKF_MANAGER_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Codex" / "okf-manager"
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "codex" / "okf-manager"


def venv_python(env_dir: Path) -> Path:
    if os.name == "nt":
        return env_dir / "Scripts" / "python.exe"
    return env_dir / "bin" / "python"


def missing_imports(python: Path) -> list[str]:
    code = """
import importlib.util, json
mods = ['yaml', 'bs4', 'lxml', 'requests', 'markdownify']
print(json.dumps({m: importlib.util.find_spec(m) is not None for m in mods}))
"""
    result = subprocess.run([str(python), "-c", code], check=True, text=True, capture_output=True)
    found = json.loads(result.stdout)
    return [mod for mod, ok in found.items() if not ok]


def create_venv(env_dir: Path) -> None:
    env_dir.parent.mkdir(parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True, clear=False, symlinks=True).create(env_dir)


def install_requirements(python: Path, requirements: Path) -> None:
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)


def main(argv: list[str]) -> int:
    root = skill_root()
    parser = argparse.ArgumentParser(description="Bootstrap OKF Manager worker venv")
    parser.add_argument("--venv", default=str(default_data_root() / "venv"), help="Worker venv path; default: user-local OKF Manager cache")
    parser.add_argument("--requirements", default=str(root / "requirements-worker.txt"))
    parser.add_argument("--check-only", action="store_true", help="Only report status; do not create/install")
    parser.add_argument("--force-install", action="store_true", help="Run pip install even if imports are already present")
    args = parser.parse_args(argv[1:])

    env_dir = Path(args.venv).expanduser().resolve()
    requirements = Path(args.requirements).expanduser().resolve()
    py = venv_python(env_dir)
    created = False

    if not py.exists():
        if args.check_only:
            print(json.dumps({"ok": False, "venv": str(env_dir), "python": str(py), "missing": list(REQUIRED_IMPORTS), "action": "create-required"}, indent=2))
            return 1
        create_venv(env_dir)
        created = True

    missing = missing_imports(py)
    installed = False
    if missing or args.force_install:
        if args.check_only:
            print(json.dumps({"ok": False, "venv": str(env_dir), "python": str(py), "missing": missing, "action": "install-required"}, indent=2))
            return 1
        if not requirements.exists():
            raise FileNotFoundError(f"requirements file not found: {requirements}")
        install_requirements(py, requirements)
        installed = True
        missing = missing_imports(py)

    ok = not missing
    print(json.dumps({
        "ok": ok,
        "venv": str(env_dir),
        "python": str(py),
        "requirements": str(requirements),
        "created": created,
        "installed": installed,
        "missing": missing,
        "required_imports": REQUIRED_IMPORTS,
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
