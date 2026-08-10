#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    try:
        import yaml
        fm = yaml.safe_load(text[4:end]) or {}
        return fm if isinstance(fm, dict) else {}
    except Exception:
        return {}


def index_text(entries):
    grouped = defaultdict(list)
    for typ, title, link, desc in entries:
        grouped[typ or "Other"].append((title, link, desc))
    sections = []
    for typ in sorted(grouped):
        lines = [f"# {typ}", ""]
        for title, link, desc in sorted(grouped[typ], key=lambda item: item[0].lower()):
            lines.append(f"* [{title}]({link})" + (f" - {desc}" if desc else ""))
        sections.append("\n".join(lines))
    return "\n\n".join(sections) + "\n"



def _is_raw_evidence(rel) -> bool:
    parts = rel.parts if hasattr(rel, "parts") else Path(str(rel)).parts
    return len(parts) >= 2 and parts[0] == "sources" and parts[1] == "raw"

def regenerate(root: Path) -> list[str]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Bundle directory not found: {root}")
    dirs = set()
    for md in root.rglob("*.md"):
        rel = md.relative_to(root)
        if md.name in {"index.md", "log.md"} or _is_raw_evidence(rel):
            continue
        cur = md.parent
        while True:
            dirs.add(cur)
            if cur == root:
                break
            cur = cur.parent
    written = []
    descriptions = {}
    for directory in sorted(dirs, key=lambda p: (-len(p.relative_to(root).parts), str(p))):
        entries = []
        for child in sorted(directory.iterdir()):
            if child.name == "index.md":
                continue
            if child.is_file() and child.suffix == ".md" and child.name != "log.md" and not _is_raw_evidence(child.relative_to(root)):
                fm = frontmatter(child)
                entries.append((str(fm.get("type") or "Other"), str(fm.get("title") or child.stem), child.name, str(fm.get("description") or "")))
            elif child.is_dir():
                entries.append(("Subdirectories", child.name, f"{child.name}/index.md", descriptions.get(child, "")))
        if not entries:
            continue
        path = directory / "index.md"
        path.write_text(index_text(entries), encoding="utf-8")
        written.append(path.relative_to(root).as_posix())
        if directory != root:
            pairs = [(title, desc) for _, title, _, desc in entries]
            descriptions[directory] = pairs[0][1] if len(pairs) == 1 and pairs[0][1] else f"Contains {len(pairs)} entries."
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] in {"-h", "--help"}:
        print("Usage: okf_regenerate_indexes.py <bundle_root>")
        return 2
    written = regenerate(Path(argv[1]))
    print("Written indexes:")
    for item in written:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
