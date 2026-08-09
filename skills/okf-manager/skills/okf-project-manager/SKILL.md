---
name: okf-project-manager
description: Manage portable Open Knowledge Format (OKF) catalogs in Codex, including catalog creation, source ingestion, provenance retention, concept listing/reading/writing, validation, glossary, index and log maintenance, guarded web enrichment, optional BigQuery enrichment, and interactive graph generation. Use for requests to create or inspect an OKF bundle, ingest files or URLs into OKF, update a knowledge catalog, validate or repair OKF documents and links, regenerate derived catalog artifacts, or display the knowledge graph.
---

# OKF Project Manager

Use the deterministic runner in `scripts/okf_run.py` for catalog operations. Resolve all paths explicitly and run the script from this installed skill directory, never from retained evidence.

Read these references only when needed:

- `references/okf-format.md` for concept structure and preservation rules.
- `references/commands.md` for exact runner commands and JSON plan shapes.
- `references/web-ingestion.md` for URL crawl guards and enrichment rules.
- `references/bigquery.md` for optional BigQuery enrichment.

## Resolve the catalog

1. Read applicable workspace `AGENTS.md` files and user-named evidence manifests.
2. Prefer an explicit catalog path.
3. Otherwise use the sole existing workspace catalog when exactly one `okf/**/catalog` or `okf/catalog` directory is unambiguous.
4. Otherwise propose `<workspace-root>/okf/catalog`. If no workspace exists, propose `~/okf/catalog`.
5. Ask which catalog to use when multiple candidates exist.

## Confirm creation

Before creating a missing catalog, stop and ask for explicit confirmation. Report:

- project-local or user-global mode;
- exact catalog path;
- evidence paths or seed URLs;
- first intended operation.

Only after confirmation may a creation command include `--allow-create`. Never infer confirmation from an earlier unrelated write request.

## Operate safely

- Treat user-designated sources as immutable.
- Inventory unstructured sources before deriving concepts.
- Exclude repositories, hidden files, caches, virtual environments, dependencies, logs, and generated artifacts unless explicitly selected.
- Retain used evidence under sibling `<okf-root>/raw/<meaningful-name>/`.
- Never execute or import retained evidence.
- Preserve source paths, URLs, hashes, and citations; do not invent provenance.
- Build a compact JSON concept plan for multi-file ingestion and review it before sequential writes.
- Preserve unknown frontmatter keys and existing content when updating concepts.
- Use relative internal links only to known concepts or sibling raw evidence.
- Keep `index.md` for generated directory indexes, `glossary.md` for the generated alphabetical glossary, and `log.md` for chronological updates.

## Complete catalog changes

After graph-visible concept changes:

1. Append a concise log entry when the catalog uses a log.
2. Run the `pipeline` command to clean raw evidence, regenerate and link-check the glossary, lint concept links/frontmatter, regenerate indexes, generate `viz.html`, and verify its embedded graph.
3. Report concept, edge, and type counts from `verify-graph`.
4. Open `viz.html` in the available browser when the user asks to see the graph; always provide its absolute clickable path.

For read-only inspection, use `concept-list`, `concept-read`, `validate`, or `verify-graph` without rewriting derived artifacts.

## Web and external systems

Fetch only user-provided or explicitly approved URLs. Declare network use and apply the host, path, page, and depth guards in `references/web-ingestion.md`.

Treat BigQuery as optional. Do not install its dependency or access a dataset unless the user requests BigQuery enrichment. Report missing credentials or dependencies without weakening local bundle behavior.

## Report

Return exact catalog and evidence paths, changed files, operation counts, validation results, graph statistics, assumptions, and anything not verified. Never claim success when a deterministic command failed.
