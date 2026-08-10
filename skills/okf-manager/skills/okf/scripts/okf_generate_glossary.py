#!/usr/bin/env python3
"""Generate a deterministic glossary from repeated OKF catalog terminology."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

GENERATED_DOCUMENTS = {"index.md", "log.md", "glossary.md"}
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:[-/][A-Z0-9]+)*\b")
LONG_FORM_RE = r"[A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){1,7}"
DEFINED_ACRONYM_RE = re.compile(rf"\b({LONG_FORM_RE})\s+\(({ACRONYM_RE.pattern[2:-2]})\)")
REVERSED_ACRONYM_RE = re.compile(rf"\b({ACRONYM_RE.pattern[2:-2]})\s+\(({LONG_FORM_RE})\)")
CAPITALIZED_PHRASE_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*(?:\s+[A-Z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*){1,4}\b"
)
LEADING_WORDS = {"a", "an", "and", "for", "in", "of", "on", "or", "the", "to", "with"}
IGNORED_TERMS = {"citation", "citations", "schema"}


def _split_document(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    frontmatter = yaml.safe_load(text[4:end]) or {}
    return (frontmatter if isinstance(frontmatter, dict) else {}), text[end + 4 :].lstrip("\n")


def _is_raw_evidence(relative_path: Path) -> bool:
    parts = relative_path.parts
    return len(parts) >= 2 and parts[0] == "sources" and parts[1] == "raw"


def _normalize(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip(" \t\r\n.,:;!?()[]{}\"'`")).casefold()


def _clean_phrase(term: str) -> str:
    words = re.sub(r"\s+", " ", term).strip().split()
    while len(words) > 1 and words[0].casefold() in LEADING_WORDS:
        words.pop(0)
    while len(words) > 1 and words[-1].casefold() in LEADING_WORDS:
        words.pop()
    return " ".join(words).strip(" \t\r\n.,:;!?()[]{}\"'`")


def _acronym_expansion(long_form: str, acronym: str) -> str:
    words = _clean_phrase(long_form).split()
    initials = "".join(character for character in acronym if character.isalnum()).casefold()
    for start in range(len(words) - 1, -1, -1):
        candidate = words[start:]
        if "".join(word[0] for word in candidate).casefold() == initials:
            return " ".join(candidate)
    return " ".join(words)


def _markdown_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!?(?:\[([^]]*)\])\([^)]*\)", r"\1", text)
    return text


def _add(term: str, concept_id: str, displays: dict[str, Counter], sources: dict[str, set[str]]) -> str | None:
    cleaned = _clean_phrase(term)
    key = _normalize(cleaned)
    if not key or key in IGNORED_TERMS:
        return None
    displays[key][cleaned] += 1
    sources[key].add(concept_id)
    return key


def _display(counter: Counter) -> str:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))[0][0]


def generate(catalog: Path, minimum_documents: int = 2) -> dict:
    catalog = catalog.expanduser().resolve()
    if not catalog.is_dir():
        raise FileNotFoundError(f"Catalog directory not found: {catalog}")

    displays: dict[str, Counter] = defaultdict(Counter)
    sources: dict[str, set[str]] = defaultdict(set)
    expansions: dict[str, Counter] = defaultdict(Counter)
    title_descriptions: dict[str, Counter] = defaultdict(Counter)
    concept_titles: dict[str, str] = {}
    document_count = 0

    for path in sorted(catalog.rglob("*.md")):
        relative_path = path.relative_to(catalog)
        if path.name in GENERATED_DOCUMENTS or _is_raw_evidence(relative_path):
            continue
        document_count += 1
        concept_id = relative_path.with_suffix("").as_posix()
        frontmatter, body = _split_document(path.read_text(encoding="utf-8", errors="replace"))
        title = str(frontmatter.get("title") or "").strip()
        concept_titles[concept_id] = title or concept_id
        description = str(frontmatter.get("description") or "").strip()
        if title:
            key = _add(title, concept_id, displays, sources)
            if key and description:
                title_descriptions[key][description] += 1
        tags = frontmatter.get("tags") or []
        if isinstance(tags, list):
            for tag in tags:
                _add(str(tag), concept_id, displays, sources)

        searchable = _markdown_text("\n".join((title, description, body)))
        for match in DEFINED_ACRONYM_RE.finditer(searchable):
            acronym = match.group(2)
            long_form = _acronym_expansion(match.group(1), acronym)
            key = _add(acronym, concept_id, displays, sources)
            if key:
                expansions[key][long_form] += 1
        for match in REVERSED_ACRONYM_RE.finditer(searchable):
            acronym = match.group(1)
            long_form = _acronym_expansion(match.group(2), acronym)
            key = _add(acronym, concept_id, displays, sources)
            if key:
                expansions[key][long_form] += 1
        for acronym in ACRONYM_RE.findall(searchable):
            if len(acronym.replace("-", "").replace("/", "")) >= 2:
                _add(acronym, concept_id, displays, sources)
        for line in searchable.splitlines():
            for phrase in CAPITALIZED_PHRASE_RE.findall(line):
                words = _clean_phrase(phrase).split()
                _add(" ".join(words), concept_id, displays, sources)
                for start in range(len(words) - 1):
                    for end in range(start + 2, len(words) + 1):
                        _add(" ".join(words[start:end]), concept_id, displays, sources)

    entries = []
    for key, concept_ids in sources.items():
        if len(concept_ids) < minimum_documents:
            continue
        term = _display(displays[key])
        if expansions.get(key):
            meaning = _display(expansions[key])
        elif title_descriptions.get(key):
            meaning = _display(title_descriptions[key])
        else:
            meaning = ""
        entries.append({"term": term, "meaning": meaning, "sources": sorted(concept_ids, key=str.casefold)})
    entries.sort(key=lambda item: (item["term"].casefold(), item["term"]))

    lines = [
        "# Glossary",
        "",
        "> Generated by OKF Manager from terms present in at least "
        f"{minimum_documents} concept documents. Do not edit manually.",
        "",
    ]
    if entries:
        lines.extend(["| Term | Meaning | Sources |", "| --- | --- | --- |"])
        for entry in entries:
            term = entry["term"].replace("|", "\\|")
            meaning = entry["meaning"].replace("|", "\\|") or "—"
            links = []
            for concept_id in entry["sources"]:
                title = concept_titles[concept_id].replace("|", "\\|").replace("]", "\\]")
                links.append(f"[{title}]({concept_id}.md)")
            lines.append(f"| {term} | {meaning} | {', '.join(links)} |")
    else:
        lines.append("No terms currently meet the cross-document threshold.")
    rendered = "\n".join(lines) + "\n"
    output = catalog / "glossary.md"
    output.write_text(rendered, encoding="utf-8")
    return {
        "catalog": str(catalog),
        "path": str(output),
        "documents_scanned": document_count,
        "entry_count": len(entries),
        "minimum_documents": minimum_documents,
        "entries": entries,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate an alphabetical glossary from repeated OKF catalog terminology")
    parser.add_argument("catalog_root", help="Path to <okf>/catalog")
    parser.add_argument("--minimum-documents", type=int, default=2)
    args = parser.parse_args(argv[1:])
    if args.minimum_documents < 2:
        parser.error("--minimum-documents must be at least 2")
    try:
        print(json.dumps(generate(Path(args.catalog_root), args.minimum_documents), indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
