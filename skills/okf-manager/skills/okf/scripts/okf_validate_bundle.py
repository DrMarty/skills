#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

_LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[A-Za-z0-9_-]*)?\)")
_SEGMENT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}, text, "missing YAML frontmatter at line 1"
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text, "unterminated YAML frontmatter"
    try:
        import yaml
        fm = yaml.safe_load(text[4:end]) or {}
    except Exception as exc:
        return {}, text, f"invalid YAML frontmatter: {exc}"
    if not isinstance(fm, dict):
        return {}, text, "frontmatter must be mapping"
    return fm, text[end + 4 :].lstrip("\n"), ""



def _is_raw_evidence(rel) -> bool:
    parts = rel.parts if hasattr(rel, "parts") else Path(str(rel)).parts
    return len(parts) >= 2 and parts[0] == "sources" and parts[1] == "raw"


def _is_allowed_raw_link(root: Path, dest: Path) -> bool:
    try:
        rel = dest.resolve().relative_to(root.parent.resolve())
    except Exception:
        return False
    return len(rel.parts) >= 2 and rel.parts[0] == "raw"


def _link_issues(path: Path, body: str, root: Path, rel: str) -> list[dict]:
    issues = []
    for match in _LINK_RE.finditer(body):
        target = match.group(1)
        if "://" in target or target.startswith("#") or target.startswith("mailto:"):
            continue
        if target.startswith("/"):
            issues.append({"path": rel, "issue": f"root-relative internal link discouraged: {target}"})
            continue
        dest = (path.parent / target).resolve()
        try:
            dest.relative_to(root)
            allowed = True
        except Exception:
            allowed = _is_allowed_raw_link(root, dest)
        if not allowed:
            issues.append({"path": rel, "issue": f"link escapes catalog and is not under sibling raw/: {target}"})
        elif not dest.exists():
            issues.append({"path": rel, "issue": f"broken link: {target}"})
    return issues

def validate(root: Path, strict: bool = True) -> dict:
    root = root.expanduser().resolve()
    issues = []
    count = 0
    if not root.is_dir():
        return {"concept_count": 0, "issue_count": 1, "issues": [{"path": str(root), "issue": "bundle directory not found"}]}
    for path in sorted(root.rglob("*.md")):
        rel_path = path.relative_to(root)
        rel = rel_path.as_posix()
        if _is_raw_evidence(rel_path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name in {"index.md", "log.md", "glossary.md"}:
            issues.extend(_link_issues(path, text, root, rel))
            continue
        count += 1
        concept_parts = rel_path.with_suffix("").parts
        if any(not _SEGMENT_RE.fullmatch(part) for part in concept_parts):
            issues.append({"path": rel, "issue": "concept id contains a path-unsafe segment"})
        fm, body, err = split_frontmatter(text)
        if err:
            issues.append({"path": rel, "issue": err})
            continue
        required = ["type"] + (["title", "description", "timestamp"] if strict else [])
        for key in required:
            if not fm.get(key):
                issues.append({"path": rel, "issue": f"missing frontmatter {key}"})
        if "tags" in fm and not isinstance(fm["tags"], list):
            issues.append({"path": rel, "issue": "tags must be a YAML list"})
        if strict and fm.get("timestamp"):
            try:
                datetime.fromisoformat(str(fm["timestamp"]).replace("Z", "+00:00"))
            except ValueError:
                issues.append({"path": rel, "issue": "timestamp must be ISO 8601"})
        issues.extend(_link_issues(path, body, root, rel))
    return {"concept_count": count, "issue_count": len(issues), "issues": issues}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print("Usage: okf_validate_bundle.py <bundle_root> [--non-strict]")
        return 2
    strict = "--non-strict" not in argv[2:]
    result = validate(Path(argv[1]), strict=strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["issue_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
