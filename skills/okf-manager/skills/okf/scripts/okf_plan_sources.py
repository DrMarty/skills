#!/usr/bin/env python3
"""Create a compact source inventory JSON for unstructured OKF ingests.

The output deliberately makes no assumptions about what the files mean or which
concepts should exist. It inventories non-internal evidence and emits a JSON
plan scaffold that downstream agent/code can enrich into concepts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path

INTERNAL_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".npm", ".venv", "venv", "dist", "build"}
INTERNAL_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".swp"}
INTERNAL_FILENAMES = {".DS_Store"}
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".js", ".ts", ".html", ".css", ".toml", ".ini", ".csv"}


def is_internal(rel: Path) -> bool:
    return (
        any(part in INTERNAL_DIRS or part.startswith(".") for part in rel.parts)
        or rel.suffix in INTERNAL_SUFFIXES
        or rel.name in INTERNAL_FILENAMES
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def preview(path: Path, max_chars: int) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES or max_chars <= 0:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def inventory(source_root: Path, max_preview_chars: int = 600) -> dict:
    source_root = source_root.resolve()
    files = []
    skipped_internal = []
    for path in sorted(source_root.rglob("*")) if source_root.is_dir() else [source_root]:
        if not path.is_file():
            continue
        rel = path.relative_to(source_root) if source_root.is_dir() else Path(path.name)
        if is_internal(rel):
            skipped_internal.append(rel.as_posix())
            continue
        stat = path.stat()
        mime, _ = mimetypes.guess_type(str(path))
        files.append({
            "path": rel.as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256(path),
            "mime": mime or "application/octet-stream",
            "suffix": path.suffix.lower(),
            "preview": preview(path, max_preview_chars),
        })
    return {
        "schema": "okf.source_inventory.v1",
        "source_root": str(source_root),
        "file_count": len(files),
        "files": files,
        "skipped_internal_count": len(skipped_internal),
        "skipped_internal": skipped_internal,
        "notes": [
            "This is an evidence inventory for an unstructured file collection.",
            "It intentionally makes no assumptions about concept boundaries, types, or relationships.",
            "Use it to build a separate JSON concept plan; preserve the listed files under <okf>/raw/<meaningful-name>/.",
        ],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Inventory non-internal files for an unstructured OKF ingest")
    ap.add_argument("source_root")
    ap.add_argument("--out", help="Write inventory JSON to this path instead of stdout")
    ap.add_argument("--max-preview-chars", type=int, default=600)
    args = ap.parse_args(argv[1:])
    result = inventory(Path(args.source_root).expanduser(), args.max_preview_chars)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).expanduser().resolve().write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
