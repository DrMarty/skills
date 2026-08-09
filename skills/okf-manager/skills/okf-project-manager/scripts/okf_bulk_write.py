#!/usr/bin/env python3
"""Sequentially write a JSON concept plan into an OKF catalog and retain raw evidence under sibling okf/raw/<name>."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

RESERVED = {"index", "log", "index.md", "log.md"}
SEGMENT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
INTERNAL_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".npm", ".venv", "venv", "dist", "build"}
INTERNAL_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".swp"}
INTERNAL_FILENAMES = {".DS_Store"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("._-") or "ingest"


def validate_concept_id(concept_id: str) -> str:
    cid = concept_id.strip().strip("/")
    if cid.endswith(".md"):
        cid = cid[:-3]
    if not cid or cid.endswith("/") or ".." in Path(cid).parts:
        raise ValueError(f"invalid concept_id: {concept_id!r}")
    parts = Path(cid).parts
    if any(part in RESERVED for part in parts):
        raise ValueError(f"reserved concept_id component in {concept_id!r}")
    if any(not SEGMENT_RE.fullmatch(part) for part in parts):
        raise ValueError(f"path-unsafe concept_id component in {concept_id!r}")
    return cid


def ordered_frontmatter(fm: dict) -> dict:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    out = {}
    for key in ["type", "resource", "title", "description", "tags", "timestamp"]:
        if key in fm and fm[key] not in (None, ""):
            out[key] = fm[key]
    out.setdefault("timestamp", now)
    for key, value in fm.items():
        if key not in out:
            out[key] = value
    for required in ["type", "title", "description"]:
        if not out.get(required):
            raise ValueError(f"frontmatter missing required key: {required}")
    if "tags" in out and not isinstance(out["tags"], list):
        raise ValueError("frontmatter tags must be a YAML list")
    return out


def write_doc(catalog_root: Path, record: dict, overwrite: bool) -> Path:
    cid = validate_concept_id(str(record.get("concept_id") or record.get("id") or ""))
    fm = ordered_frontmatter(dict(record.get("frontmatter") or {}))
    body = str(record.get("body") or "").rstrip() + "\n"
    if "# Citations" not in body:
        raise ValueError(f"{cid}: body must include # Citations")
    dest = catalog_root / f"{cid}.md"
    if dest.exists() and not overwrite:
        raise FileExistsError(f"{dest} exists; pass --overwrite to replace")
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n" + body
    dest.write_text(text, encoding="utf-8")
    return dest


def is_internal_path(path: Path) -> bool:
    return (
        any(part in INTERNAL_DIRS or part.startswith(".") for part in path.parts)
        or path.suffix in INTERNAL_SUFFIXES
        or path.name in INTERNAL_FILENAMES
    )


def clean_internal_files(raw_root: Path) -> list[str]:
    """Remove generated/internal artifacts from retained raw evidence."""
    removed: list[str] = []
    if not raw_root.exists():
        return removed
    for child in sorted(raw_root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        try:
            rel = child.relative_to(raw_root)
        except ValueError:
            continue
        if is_internal_path(rel):
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            elif child.exists():
                child.unlink(missing_ok=True)
            removed.append(str(child))
    return removed


def raw_root_for_catalog(catalog_root: Path, raw_name: str) -> Path:
    # Expected layout: <project>/okf/catalog and sibling <project>/okf/raw/<meaningful-name>.
    okf_root = catalog_root.parent if catalog_root.name == "catalog" else catalog_root.parent
    return okf_root / "raw" / _slug(raw_name)


def default_raw_name(source_root: Path | None, plan_path: Path) -> str:
    return _slug((source_root.name if source_root else plan_path.stem) or "ingest")


def copy_raw_sources(catalog_root: Path, sources: list[str], raw_name: str, source_root: Path | None = None) -> list[str]:
    raw_root = raw_root_for_catalog(catalog_root, raw_name)
    copied = []
    for source in sources:
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", source):
            parsed = urlparse(source)
            name = _slug((parsed.netloc + parsed.path).strip("/") or parsed.netloc)
            dest = raw_root / "urls" / name
            dest = dest.with_suffix(dest.suffix or ".url.txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(source + "\n", encoding="utf-8")
            copied.append(str(dest))
            continue
        src = Path(source)
        if not src.is_absolute() and source_root:
            src = source_root / src
        src = src.resolve()
        if not src.exists():
            continue
        rel = src.name if not source_root else src.relative_to(source_root.resolve())
        rel_path = Path(rel)
        if is_internal_path(rel_path):
            continue
        dest = raw_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*INTERNAL_DIRS, ".*", "*.pyc", "*.pyo", "*.log", "*.tmp"))
        else:
            shutil.copy2(src, dest)
        copied.append(str(dest))
    return copied


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Sequentially write OKF concept records from JSON into <okf>/catalog")
    ap.add_argument("catalog_root")
    ap.add_argument("plan_json", help="JSON list or {concepts:[...], raw_sources:[...], raw_name: ...}")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--allow-create", action="store_true", help="Create a missing catalog only after explicit user confirmation")
    ap.add_argument("--source-root", default="")
    ap.add_argument("--raw-name", default="", help="Meaningful folder name under sibling <okf>/raw/")
    args = ap.parse_args(argv[1:])
    root = Path(args.catalog_root).expanduser().resolve()
    if not root.exists():
        if not args.allow_create:
            raise SystemExit(f"catalog does not exist: {root}; creation requires explicit confirmation and --allow-create")
        root.mkdir(parents=True)
    if not root.is_dir():
        raise SystemExit(f"catalog path is not a directory: {root}")
    plan_path = Path(args.plan_json).expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    concepts = plan.get("concepts", plan) if isinstance(plan, dict) else plan
    if not isinstance(concepts, list):
        raise SystemExit("plan must be a list or an object with concepts: []")
    written = [str(write_doc(root, record, args.overwrite)) for record in concepts]
    copied = []
    raw_root = None
    if isinstance(plan, dict) and plan.get("raw_sources"):
        source_root = Path(args.source_root).expanduser().resolve() if args.source_root else None
        raw_name = args.raw_name or str(plan.get("raw_name") or default_raw_name(source_root, plan_path))
        raw_root = raw_root_for_catalog(root, raw_name)
        copied = copy_raw_sources(root, list(plan["raw_sources"]), raw_name, source_root)
        removed_internal = clean_internal_files(raw_root)
    else:
        removed_internal = []
    print(json.dumps({"written_count": len(written), "written": written, "raw_root": str(raw_root) if raw_root else None, "raw_sources_copied": copied, "raw_internal_removed": removed_internal}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
