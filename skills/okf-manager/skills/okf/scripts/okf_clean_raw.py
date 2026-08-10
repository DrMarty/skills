#!/usr/bin/env python3
"""Remove generated/internal artifacts from retained OKF raw evidence.

This script is intentionally code-driven and should be run from the plugin install
path, never from inside okf/raw/**. Raw evidence is audit input, not an execution
location.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

INTERNAL_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".npm", ".venv", "venv", "dist", "build"}
INTERNAL_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".swp"}
INTERNAL_FILENAMES = {".DS_Store"}


def is_internal_path(path: Path) -> bool:
    return (
        any(part in INTERNAL_DIRS or part.startswith(".") for part in path.parts)
        or path.suffix in INTERNAL_SUFFIXES
        or path.name in INTERNAL_FILENAMES
    )


def clean(raw_root: Path, dry_run: bool = False) -> dict:
    raw_root = raw_root.resolve()
    removed = []
    kept = 0
    if not raw_root.exists():
        return {"raw_root": str(raw_root), "exists": False, "removed_count": 0, "removed": [], "kept_files": 0, "issue_count": 1, "issues": ["raw root not found"]}
    for child in sorted(raw_root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        rel = child.relative_to(raw_root)
        if is_internal_path(rel):
            removed.append(str(child))
            if not dry_run:
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)
        elif child.is_file():
            kept += 1
    return {"raw_root": str(raw_root), "exists": True, "dry_run": dry_run, "removed_count": len(removed), "removed": removed, "kept_files": kept, "issue_count": 0, "issues": []}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Clean internal/generated artifacts from <okf>/raw evidence")
    ap.add_argument("raw_root", nargs="?", help="Path to <okf>/raw or a specific <okf>/raw/<name> folder")
    ap.add_argument("--raw-root", dest="raw_root_opt")
    ap.add_argument("--catalog", help="Path to <okf>/catalog; raw root is inferred as sibling <okf>/raw")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])
    target = args.raw_root_opt or args.raw_root
    if args.catalog:
        target = str(Path(args.catalog).expanduser().resolve().parent / "raw")
    if not target:
        ap.error("provide raw_root, --raw-root, or --catalog")
    result = clean(Path(target).expanduser(), dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("issue_count", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
