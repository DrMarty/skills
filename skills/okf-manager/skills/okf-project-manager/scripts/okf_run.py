#!/usr/bin/env python3
"""Stable cross-platform runner for deterministic OKF Manager operations."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    override = os.environ.get("OKF_MANAGER_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Codex" / "okf-manager"
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "codex" / "okf-manager"


def worker_python() -> Path:
    return data_root() / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(command: list[str], *, cwd: Path | None = None) -> int:
    return subprocess.run(command, cwd=str(cwd) if cwd else None).returncode


def ensure_env(root: Path, no_bootstrap: bool) -> Path:
    python = worker_python()
    if no_bootstrap and not python.exists():
        raise FileNotFoundError(f"worker python not found: {python}; run scripts/okf_bootstrap_env.py")
    if not no_bootstrap:
        code = run([sys.executable, str(root / "scripts" / "okf_bootstrap_env.py")])
        if code:
            raise RuntimeError(f"worker environment bootstrap failed with exit code {code}")
    return python


def selected(args, positional: str, *options: str) -> str:
    for name in options:
        value = getattr(args, name, None)
        if value:
            return str(value)
    value = getattr(args, positional, None)
    if value:
        return str(value)
    raise SystemExit(f"missing required path: {positional}")


def add_catalog(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("catalog_root", nargs="?", help="Path to <okf>/catalog")
    parser.add_argument("--catalog", dest="catalog_opt", help="Path to <okf>/catalog")


def main(argv: list[str]) -> int:
    root = skill_root()
    scripts = root / "scripts"
    parser = argparse.ArgumentParser(description="Run OKF Manager deterministic operations")
    parser.add_argument("--no-bootstrap", action="store_true", help="Reuse the existing user-local worker environment")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("plan-sources", help="Inventory source evidence without inferring concepts")
    command.add_argument("source_root", nargs="?")
    command.add_argument("--source-root", dest="source_root_opt")
    command.add_argument("--out")
    command.add_argument("--max-preview-chars", type=int, default=600)

    command = sub.add_parser("bulk-write", help="Write a reviewed JSON concept plan sequentially")
    add_catalog(command)
    command.add_argument("plan_json", nargs="?")
    command.add_argument("--plan", dest="plan_opt")
    command.add_argument("--overwrite", action="store_true")
    command.add_argument("--allow-create", action="store_true")
    command.add_argument("--source-root")
    command.add_argument("--raw-name")

    command = sub.add_parser("clean-raw", help="Remove internal artifacts from retained evidence")
    command.add_argument("raw_root", nargs="?")
    command.add_argument("--raw-root", dest="raw_root_opt")
    command.add_argument("--catalog", dest="catalog_opt")
    command.add_argument("--dry-run", action="store_true")

    for name, help_text in (("lint", "Lint catalog and links"), ("validate", "Validate catalog"), ("glossary", "Generate glossary.md"), ("index", "Regenerate indexes"), ("visualize", "Generate viz.html")):
        command = sub.add_parser(name, help=help_text)
        add_catalog(command)
        if name in {"lint", "validate"}:
            command.add_argument("--non-strict", action="store_true")

    command = sub.add_parser("verify-graph", help="Verify the embedded graph payload")
    command.add_argument("path", nargs="?")
    command.add_argument("--path", dest="path_opt")
    command.add_argument("--catalog", dest="catalog_opt")
    command.add_argument("--min-concepts", type=int, default=0)
    command.add_argument("--min-edges", type=int, default=0)

    command = sub.add_parser("pipeline", help="Clean, lint, generate glossary and indexes, visualize, and verify")
    add_catalog(command)
    command.add_argument("--min-concepts", type=int, default=0)
    command.add_argument("--min-edges", type=int, default=0)

    command = sub.add_parser("concept-list", help="List catalog concepts")
    add_catalog(command)
    command = sub.add_parser("concept-read", help="Read one catalog concept")
    add_catalog(command)
    command.add_argument("concept_id")
    command.add_argument("--raw", action="store_true")
    command = sub.add_parser("concept-write", help="Write one JSON concept document")
    add_catalog(command)
    command.add_argument("document_json")
    command.add_argument("--overwrite", action="store_true")
    command.add_argument("--web-pass", action="store_true")
    command.add_argument("--allow-create", action="store_true")
    command = sub.add_parser("log", help="Append a chronological catalog log entry")
    add_catalog(command)
    command.add_argument("message")

    command = sub.add_parser("fetch-url", help="Fetch one approved web page with crawl guards")
    command.add_argument("url")
    command.add_argument("--state")
    command.add_argument("--seed", action="append")
    command.add_argument("--allowed-host", action="append")
    command.add_argument("--allowed-path-prefix", action="append")
    command.add_argument("--denied-path-substring", action="append")
    command.add_argument("--max-pages", type=int, default=100)
    command.add_argument("--max-depth", type=int, default=2)
    command.add_argument("--reset-state", action="store_true")
    command.add_argument("--out")

    command = sub.add_parser("install-bigquery", help="Install the optional BigQuery dependency")
    command = sub.add_parser("bigquery-list", help="List BigQuery concepts")
    command.add_argument("--dataset", required=True)
    command.add_argument("--billing-project")
    command = sub.add_parser("bigquery-read", help="Read BigQuery concept metadata")
    command.add_argument("--dataset", required=True)
    command.add_argument("--billing-project")
    command.add_argument("concept_id")
    command = sub.add_parser("bigquery-sample", help="Sample rows from a BigQuery table")
    command.add_argument("--dataset", required=True)
    command.add_argument("--billing-project")
    command.add_argument("concept_id")
    command.add_argument("--count", type=int, default=5)

    args = parser.parse_args(argv[1:])
    try:
        python = ensure_env(root, args.no_bootstrap)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    if args.command == "plan-sources":
        command = [str(python), str(scripts / "okf_plan_sources.py"), selected(args, "source_root", "source_root_opt"), "--max-preview-chars", str(args.max_preview_chars)]
        if args.out:
            command += ["--out", args.out]
        return run(command)
    if args.command == "bulk-write":
        command = [str(python), str(scripts / "okf_bulk_write.py"), selected(args, "catalog_root", "catalog_opt"), selected(args, "plan_json", "plan_opt")]
        for enabled, flag in ((args.overwrite, "--overwrite"), (args.allow_create, "--allow-create")):
            if enabled:
                command.append(flag)
        for value, flag in ((args.source_root, "--source-root"), (args.raw_name, "--raw-name")):
            if value:
                command += [flag, value]
        return run(command)
    if args.command == "clean-raw":
        command = [str(python), str(scripts / "okf_clean_raw.py")]
        if args.catalog_opt:
            command += ["--catalog", args.catalog_opt]
        else:
            command.append(selected(args, "raw_root", "raw_root_opt"))
        if args.dry_run:
            command.append("--dry-run")
        return run(command)
    if args.command in {"lint", "validate", "glossary", "index", "visualize"}:
        script_name = {
            "lint": "okf_lint_catalog.py",
            "validate": "okf_validate_bundle.py",
            "glossary": "okf_generate_glossary.py",
            "index": "okf_regenerate_indexes.py",
            "visualize": "okf_visualize_bundle.py",
        }[args.command]
        command = [str(python), str(scripts / script_name), selected(args, "catalog_root", "catalog_opt")]
        if getattr(args, "non_strict", False):
            command.append("--non-strict")
        return run(command)
    if args.command == "verify-graph":
        path = args.catalog_opt or args.path_opt or args.path
        if not path:
            parser.error("verify-graph requires path, --path, or --catalog")
        return run([str(python), str(scripts / "okf_verify_graph.py"), path, "--min-concepts", str(args.min_concepts), "--min-edges", str(args.min_edges)])
    if args.command == "pipeline":
        catalog = selected(args, "catalog_root", "catalog_opt")
        steps = [
            [str(python), str(scripts / "okf_clean_raw.py"), "--catalog", catalog],
            [str(python), str(scripts / "okf_generate_glossary.py"), catalog],
            [str(python), str(scripts / "okf_lint_catalog.py"), catalog],
            [str(python), str(scripts / "okf_regenerate_indexes.py"), catalog],
            [str(python), str(scripts / "okf_visualize_bundle.py"), catalog],
            [str(python), str(scripts / "okf_verify_graph.py"), str(Path(catalog) / "viz.html"), "--min-concepts", str(args.min_concepts), "--min-edges", str(args.min_edges)],
        ]
        for step in steps:
            code = run(step)
            if code:
                print(json.dumps({"ok": False, "failed_step": step, "exit_code": code}, indent=2))
                return code
        print(json.dumps({"ok": True, "pipeline": "clean-raw-glossary-lint-index-visualize-verify", "catalog": str(Path(catalog).resolve())}, indent=2))
        return 0
    if args.command.startswith("concept-") or args.command == "log":
        operation = {"concept-list": "list", "concept-read": "read", "concept-write": "write", "log": "append-log"}[args.command]
        command = [str(python), str(scripts / "okf_concepts.py"), operation, selected(args, "catalog_root", "catalog_opt")]
        if args.command == "concept-read":
            command.append(args.concept_id)
            if args.raw:
                command.append("--raw")
        elif args.command == "concept-write":
            command.append(args.document_json)
            for enabled, flag in ((args.overwrite, "--overwrite"), (args.web_pass, "--web-pass"), (args.allow_create, "--allow-create")):
                if enabled:
                    command.append(flag)
        elif args.command == "log":
            command.append(args.message)
        return run(command)
    if args.command == "fetch-url":
        command = [str(python), str(scripts / "okf_fetch_url.py"), args.url, "--max-pages", str(args.max_pages), "--max-depth", str(args.max_depth)]
        for value, flag in ((args.state, "--state"), (args.out, "--out")):
            if value:
                command += [flag, value]
        for values, flag in ((args.seed, "--seed"), (args.allowed_host, "--allowed-host"), (args.allowed_path_prefix, "--allowed-path-prefix"), (args.denied_path_substring, "--denied-path-substring")):
            for value in values or []:
                command += [flag, value]
        if args.reset_state:
            command.append("--reset-state")
        return run(command)
    if args.command == "install-bigquery":
        return run([str(python), "-m", "pip", "install", "-r", str(root / "requirements-bigquery.txt")])
    bigquery_operation = {"bigquery-list": "list", "bigquery-read": "read", "bigquery-sample": "sample"}.get(args.command)
    if bigquery_operation:
        command = [str(python), str(scripts / "okf_bigquery.py"), "--dataset", args.dataset]
        if args.billing_project:
            command += ["--billing-project", args.billing_project]
        command.append(bigquery_operation)
        if args.command != "bigquery-list":
            command.append(args.concept_id)
        if args.command == "bigquery-sample":
            command += ["--count", str(args.count)]
        return run(command)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
