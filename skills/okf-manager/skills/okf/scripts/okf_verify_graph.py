#!/usr/bin/env python3
"""Verify an OKF viz.html graph artifact and report embedded bundle-data stats."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

_TYPE_SEPARATOR = " / "


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


def inspect_type_tree(tree, valid_types: set[str]) -> dict:
    if tree is None:
        return {"present": False, "nodes": 0, "depth": 0, "issues": []}
    issues: list[str] = []
    direct_occurrences: dict[str, int] = {}
    node_count = 0
    max_depth = 0

    def walk(branches, parent_path: str, depth: int) -> set[str]:
        nonlocal node_count, max_depth
        if not isinstance(branches, list):
            issues.append(f"typeTree children under {parent_path or '<root>'} must be a list")
            return set()
        aggregate: set[str] = set()
        sibling_paths: set[str] = set()
        for branch in branches:
            if not isinstance(branch, dict):
                issues.append(f"typeTree branch under {parent_path or '<root>'} must be an object")
                continue
            node_count += 1
            max_depth = max(max_depth, depth)
            name = str(branch.get("name") or "").strip()
            path = str(branch.get("path") or "").strip()
            expected_path = name if not parent_path else parent_path + _TYPE_SEPARATOR + name
            if not name:
                issues.append(f"typeTree branch under {parent_path or '<root>'} has no name")
            if path != expected_path:
                issues.append(f"typeTree path {path!r} does not match expected {expected_path!r}")
            if path in sibling_paths:
                issues.append(f"duplicate typeTree branch path: {path}")
            sibling_paths.add(path)

            branch_types = branch.get("types")
            direct_types = branch.get("directTypes")
            if not isinstance(branch_types, list):
                issues.append(f"typeTree branch {path!r} types must be a list")
                branch_types = []
            if not isinstance(direct_types, list):
                issues.append(f"typeTree branch {path!r} directTypes must be a list")
                direct_types = []
            branch_type_set = {str(item) for item in branch_types}
            direct_type_set = {str(item) for item in direct_types}
            unknown = branch_type_set - valid_types
            if unknown:
                issues.append(f"typeTree branch {path!r} contains unknown types: {sorted(unknown)}")
            if not direct_type_set.issubset(branch_type_set):
                issues.append(f"typeTree branch {path!r} directTypes are not contained in types")
            for type_name in direct_type_set:
                direct_occurrences[type_name] = direct_occurrences.get(type_name, 0) + 1

            child_types = walk(branch.get("children"), path, depth + 1)
            expected_types = direct_type_set | child_types
            if branch_type_set != expected_types:
                issues.append(f"typeTree branch {path!r} aggregate types do not match direct and child types")
            aggregate.update(branch_type_set)
        return aggregate

    root_types = walk(tree, "", 1)
    if root_types != valid_types:
        issues.append("typeTree root aggregate does not match graph types")
    for type_name in sorted(valid_types):
        if direct_occurrences.get(type_name, 0) != 1:
            issues.append(f"graph type {type_name!r} must occur in exactly one directTypes branch")
    return {"present": True, "nodes": node_count, "depth": max_depth, "issues": issues}


def verify(path: Path) -> dict:
    if path.is_dir():
        path = path / "viz.html"
    page = path.read_text(encoding="utf-8")
    graph = extract_graph(page)
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or graph.get("links") or []
    types = graph.get("types") or sorted({str(n.get("type", "")) for n in nodes if n.get("type")})
    type_tree = inspect_type_tree(graph.get("typeTree") if "typeTree" in graph else None, {str(item) for item in types})
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
        "type_tree_present": type_tree["present"],
        "type_tree_nodes": type_tree["nodes"],
        "type_tree_depth": type_tree["depth"],
        "type_tree_issues": type_tree["issues"],
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
        issues.extend(result.pop("type_tree_issues", []))
        result["issue_count"] = len(issues)
        result["issues"] = issues
        print(json.dumps(result, indent=2))
        return 1 if issues else 0
    except Exception as exc:
        print(json.dumps({"path": args.path, "issue_count": 1, "issues": [str(exc)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
