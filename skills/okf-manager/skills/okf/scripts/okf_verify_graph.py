#!/usr/bin/env python3
"""Verify an OKF viz.html graph artifact and report embedded bundle-data stats."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


def extract_graph(page: str) -> dict:
    patterns = [
        r'<script\s+id=["\']bundle-data["\']\s+type=["\']application/json["\']\s*>\s*(.*?)\s*</script>',
        r'<script\s+type=["\']application/json["\']\s+id=["\']bundle-data["\']\s*>\s*(.*?)\s*</script>',
        r'<script\s+id=["\']graph-data["\']\s+type=["\']application/json["\']\s*>\s*(.*?)\s*</script>',
        r'const\s+GRAPH_DATA\s*=\s*(\{.*?\});\s*</script>',
        r'const\s+graphData\s*=\s*(\{.*?\});\s*</script>',
        r'window\.GRAPH_DATA\s*=\s*(\{.*?\});\s*</script>',
    ]
    for pattern in patterns:
        match = re.search(pattern, page, re.S)
        if not match:
            continue
        raw = html.unescape(match.group(1).strip())
        return json.loads(raw)
    raise ValueError("No embedded graph payload found; expected #bundle-data or compatible graph-data marker")


def verify(path: Path) -> dict:
    if path.is_dir():
        path = path / "viz.html"
    page = path.read_text(encoding="utf-8")
    graph = extract_graph(page)
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or graph.get("links") or []
    types = graph.get("types") or sorted({str(n.get("type", "")) for n in nodes if n.get("type")})
    stats = graph.get("stats") or {}
    mode = graph.get("mode") or graph.get("metadata", {}).get("mode") or stats.get("mode")
    if not mode and "d3@7" in page and ('id="bundle-data"' in page or "id='bundle-data'" in page):
        mode = "live-d3-self-graph"
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size,
        "mode": mode or "unknown",
        "concepts": len(nodes),
        "edges": len(edges),
        "types": len(types),
        "declared_stats": stats,
        "has_bundle_data_marker": 'id="bundle-data"' in page or "id='bundle-data'" in page,
        "has_d3_runtime": "d3@7" in page,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Verify an OKF viz.html graph artifact")
    ap.add_argument("path", help="Path to viz.html or an OKF bundle directory containing viz.html")
    ap.add_argument("--min-concepts", type=int, default=0)
    ap.add_argument("--min-edges", type=int, default=0)
    args = ap.parse_args(argv[1:])
    try:
        result = verify(Path(args.path).expanduser().resolve())
        issues = []
        if result["concepts"] < args.min_concepts:
            issues.append(f"concepts {result['concepts']} < required {args.min_concepts}")
        if result["edges"] < args.min_edges:
            issues.append(f"edges {result['edges']} < required {args.min_edges}")
        result["issue_count"] = len(issues)
        result["issues"] = issues
        print(json.dumps(result, indent=2))
        return 1 if issues else 0
    except Exception as exc:
        print(json.dumps({"path": args.path, "issue_count": 1, "issues": [str(exc)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
