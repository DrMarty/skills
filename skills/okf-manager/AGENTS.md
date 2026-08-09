# OKF Manager

## Purpose

- Own the Codex implementation of portable Open Knowledge Format catalog management.

## Ownership

- `.codex-plugin/` owns Codex package metadata.
- `skills/` owns model-facing workflows and bundled helpers.
- `tests/` owns local deterministic workflow coverage.
- `assets/` owns package presentation assets.
- `Requirements/` owns OKF Manager functional intent.
- `Documentation/` describes the implemented OKF Manager architecture and interfaces.

## Local Contracts

- Preserve functional parity with the supported Agent Zero OKF Manager operations while using Codex-native packaging and workflows.
- Keep mutable catalogs and retained evidence outside the installed plugin directory.
- Require explicit confirmation before creating a new OKF bundle.
- Preserve source provenance and never execute retained evidence.
- Maintain requirements before implementation and documentation alongside behavior changes.

## Work Guidance

- Prefer deterministic helpers for validation, glossary generation, indexing, and visualization.
- Treat root `glossary.md` as a generated catalog artifact: keep it alphabetically ordered, source-linked, reproducible, and excluded from concept and graph counts.
- Treat `skills/okf-project-manager/assets/viz-template.html` as the canonical generated graph UI and cover its durable controls with workflow tests.
- Keep Agent Zero-specific paths and APIs out of the Codex implementation.
- Treat custom subagents and MCP integration as optional until a validated use case requires them.
- Keep worker dependencies in the user-local OKF Manager cache rather than the installed plugin or user project.

## Verification

- Validate `.codex-plugin/plugin.json` with the Codex plugin validator.
- Validate each `SKILL.md` with the Codex skill validator.
- Compile bundled Python scripts before running them.
- Run `python -m unittest discover -s tests -v` with the user-local worker environment bootstrapped.
- Verify glossary generation is deterministic, alphabetically ordered, link-valid, and excluded from concept and graph counts.
- Verify local marketplace installation and plugin discovery before declaring a local-test milestone ready.

## Child DOX Index

- No child `AGENTS.md` files are currently required; this contract covers the complete package subtree.
