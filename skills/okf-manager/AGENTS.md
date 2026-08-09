# OKF Manager

## Purpose

- Own the Codex implementation of portable Open Knowledge Format catalog management.

## Ownership

- `.codex-plugin/` owns Codex package metadata.
- `skills/` owns model-facing workflows and bundled helpers.
- `Requirements/` owns OKF Manager functional intent.
- `Documentation/` describes the implemented OKF Manager architecture and interfaces.

## Local Contracts

- Port Agent Zero behavior progressively; do not claim unported operations work.
- Keep mutable catalogs and retained evidence outside the installed plugin directory.
- Require explicit confirmation before creating a new OKF bundle.
- Preserve source provenance and never execute retained evidence.
- Maintain requirements before implementation and documentation alongside behavior changes.

## Work Guidance

- Prefer deterministic helpers for validation, indexing, and visualization.
- Keep Agent Zero-specific paths and APIs out of the Codex implementation.
- Treat custom subagents and MCP integration as optional until a validated use case requires them.

## Verification

- Validate `.codex-plugin/plugin.json` with the Codex plugin validator.
- Validate each `SKILL.md` with the Codex skill validator.
- Add and run operation-specific tests as catalog behavior is ported.

## Child DOX Index

- No child `AGENTS.md` files are currently required; this contract covers the complete package subtree.

