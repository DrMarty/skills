# Deterministic Runner Commands

Resolve `<skill-dir>` as the directory containing `SKILL.md`. Use an available Python 3 executable explicitly:

```text
python <skill-dir>/scripts/okf_run.py <command> ...
```

The first run creates a user-local worker environment. Set `OKF_MANAGER_HOME` only when an isolated worker location is required.

## Source and concept operations

```text
plan-sources --source-root <source> --out <inventory.json>
bulk-write --catalog <catalog> --plan <concept-plan.json> [--allow-create] [--overwrite] [--source-root <source>] [--raw-name <name>]
concept-list --catalog <catalog>
concept-read --catalog <catalog> <concept-id> [--raw]
concept-write --catalog <catalog> <document.json> [--allow-create] [--overwrite] [--web-pass]
log --catalog <catalog> "<message>"
```

Use `--allow-create` only after explicit confirmation of the exact catalog path.

Single-document JSON:

```json
{
  "concept_id": "systems/example",
  "frontmatter": {
    "type": "System",
    "title": "Example",
    "description": "Example system."
  },
  "body": "Overview.\n\n# Citations\n\n- [Source](../../raw/example/README.md)"
}
```

Bulk plan JSON:

```json
{
  "raw_name": "example-sources",
  "raw_sources": ["README.md", "docs/architecture.md"],
  "concepts": [
    {
      "concept_id": "systems/example",
      "frontmatter": {
        "type": "System",
        "title": "Example",
        "description": "Example system."
      },
      "body": "Overview.\n\n# Citations\n\n- [README](../../raw/example-sources/README.md)"
    }
  ]
}
```

## Validation and graph operations

```text
clean-raw --catalog <catalog> [--dry-run]
lint --catalog <catalog>
validate --catalog <catalog>
index --catalog <catalog>
visualize --catalog <catalog>
verify-graph --catalog <catalog> [--min-concepts N] [--min-edges N]
pipeline --catalog <catalog> [--min-concepts N] [--min-edges N]
```

Use `pipeline` after concept writes. Use individual read-only commands when inspection must not regenerate artifacts.

