#!/usr/bin/env python3
"""List, read, write, and log OKF concept documents deterministically."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

REQUIRED = ("type", "title", "description", "timestamp")
ORDER = ("type", "resource", "title", "description", "tags", "timestamp")
SEGMENT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
FIELD_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")
RESERVED = {"index", "log", "glossary"}


def split_document(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    frontmatter = yaml.safe_load(text[4:end]) or {}
    return (frontmatter if isinstance(frontmatter, dict) else {}), text[end + 4 :].lstrip("\n")


def concept_id(value: str) -> str:
    value = value.strip().strip("/")
    if value.endswith(".md"):
        value = value[:-3]
    parts = value.split("/") if value else []
    if not parts:
        raise ValueError("concept_id is required")
    for part in parts:
        if part in RESERVED:
            raise ValueError("reserved filenames index.md, log.md, and glossary.md cannot be concept documents")
        if not SEGMENT_RE.fullmatch(part):
            raise ValueError(f"invalid concept id segment: {part!r}")
    return "/".join(parts)


def concept_path(catalog: Path, value: str) -> Path:
    cid = concept_id(value)
    return catalog.joinpath(*cid.split("/")).with_suffix(".md")


def ordered_frontmatter(frontmatter: dict) -> dict:
    out = {key: frontmatter[key] for key in ORDER if key in frontmatter}
    out.update({key: value for key, value in frontmatter.items() if key not in out})
    out.setdefault("timestamp", dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())
    missing = [key for key in REQUIRED if not out.get(key)]
    if missing:
        raise ValueError(f"missing required frontmatter: {', '.join(missing)}")
    if "tags" in out and not isinstance(out["tags"], list):
        raise ValueError("frontmatter tags must be a YAML list")
    return out


def section_lines(body: str, heading: str) -> list[str]:
    active = False
    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            active = stripped == heading
            continue
        if active and stripped:
            lines.append(line)
    return lines


def schema_fields(body: str) -> set[str]:
    fields: set[str] = set()
    for line in section_lines(body, "# Schema"):
        fields.update(FIELD_RE.findall(line))
    return fields


def citation_count(body: str) -> int:
    return len(section_lines(body, "# Citations"))


def list_concepts(catalog: Path) -> list[dict]:
    concepts = []
    for path in sorted(catalog.rglob("*.md")):
        if path.name in {"index.md", "log.md", "glossary.md"}:
            continue
        frontmatter, _ = split_document(path.read_text(encoding="utf-8", errors="replace"))
        concepts.append({
            "id": path.relative_to(catalog).with_suffix("").as_posix(),
            "type": frontmatter.get("type", ""),
            "resource": frontmatter.get("resource"),
            "title": frontmatter.get("title", ""),
            "description": frontmatter.get("description", ""),
        })
    return concepts


def write_concept(catalog: Path, document: dict, *, overwrite: bool, web_pass: bool, allow_create: bool) -> dict:
    if not catalog.exists():
        if not allow_create:
            raise FileNotFoundError(f"catalog does not exist: {catalog}; creation requires explicit confirmation and --allow-create")
        catalog.mkdir(parents=True)
    if not catalog.is_dir():
        raise NotADirectoryError(str(catalog))
    cid = concept_id(str(document.get("concept_id") or document.get("id") or ""))
    path = concept_path(catalog, cid)
    existing_frontmatter: dict = {}
    existing_body = ""
    if path.exists():
        existing_frontmatter, existing_body = split_document(path.read_text(encoding="utf-8"))
        if not overwrite and not web_pass:
            raise FileExistsError(f"{path} exists; pass --overwrite to replace")
    frontmatter = dict(existing_frontmatter)
    frontmatter.update(dict(document.get("frontmatter") or {}))
    frontmatter = ordered_frontmatter(frontmatter)
    body = str(document.get("body") or "")
    if web_pass and path.exists():
        missing_fields = sorted(schema_fields(existing_body) - schema_fields(body))
        if missing_fields:
            raise ValueError(f"web-pass update would remove schema fields: {', '.join(missing_fields)}")
        if citation_count(body) < citation_count(existing_body):
            raise ValueError("web-pass update would reduce citation entries")
    rendered = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip() + "\n---\n\n" + body.rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return {"id": cid, "path": str(path), "bytes": len(rendered.encode("utf-8"))}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Operate on local OKF concept documents")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("list")
    command.add_argument("catalog")

    command = sub.add_parser("read")
    command.add_argument("catalog")
    command.add_argument("concept_id")
    command.add_argument("--raw", action="store_true")

    command = sub.add_parser("write")
    command.add_argument("catalog")
    command.add_argument("document_json")
    command.add_argument("--overwrite", action="store_true")
    command.add_argument("--web-pass", action="store_true")
    command.add_argument("--allow-create", action="store_true")

    command = sub.add_parser("append-log")
    command.add_argument("catalog")
    command.add_argument("message")

    args = parser.parse_args(argv[1:])
    catalog = Path(args.catalog).expanduser().resolve()
    try:
        if args.command == "list":
            if not catalog.is_dir():
                raise FileNotFoundError(f"catalog not found: {catalog}")
            result = {"catalog": str(catalog), "concepts": list_concepts(catalog)}
            result["concept_count"] = len(result["concepts"])
        elif args.command == "read":
            path = concept_path(catalog, args.concept_id)
            if not path.is_file():
                raise FileNotFoundError(f"concept not found: {path}")
            text = path.read_text(encoding="utf-8")
            if args.raw:
                print(text, end="")
                return 0
            frontmatter, body = split_document(text)
            result = {"id": concept_id(args.concept_id), "path": str(path), "frontmatter": frontmatter, "body": body}
        elif args.command == "write":
            document = json.loads(Path(args.document_json).expanduser().resolve().read_text(encoding="utf-8"))
            result = write_concept(catalog, document, overwrite=args.overwrite, web_pass=args.web_pass, allow_create=args.allow_create)
        else:
            if not catalog.is_dir():
                raise FileNotFoundError(f"catalog not found: {catalog}")
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
            log_path = catalog / "log.md"
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"- {timestamp} — {args.message.strip()}\n")
            result = {"path": str(log_path), "timestamp": timestamp, "message": args.message.strip()}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "command": args.command, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
