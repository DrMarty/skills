#!/usr/bin/env python3
"""Code-driven OKF catalog lint after document modifications.

Checks concept frontmatter and relative Markdown links, including links from
<okf>/catalog concept docs to sibling <okf>/raw/<meaningful-name>/ evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from okf_validate_bundle import validate


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Lint an OKF catalog, including sibling raw evidence links")
    ap.add_argument("catalog_root", help="Path to <project>/okf/catalog")
    ap.add_argument("--non-strict", action="store_true")
    args = ap.parse_args(argv[1:])
    root = Path(args.catalog_root).expanduser().resolve()
    result = validate(root, strict=not args.non_strict)
    result.update({
        "lint": "okf-catalog-link-and-raw-check",
        "catalog_root": str(root),
        "raw_root": str(root.parent / "raw"),
        "raw_link_policy": "Concept documents may link to sibling ../raw/<meaningful-name>/ evidence; links are checked for existence in code.",
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("issue_count") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
