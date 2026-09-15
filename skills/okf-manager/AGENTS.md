# OKF Manager

## Purpose

- Own the portable Open Knowledge Format catalog management implementation, packaged for both Codex and Claude Code / Claude Cowork.

## Ownership

- `.codex-plugin/` owns Codex package metadata.
- `.claude-plugin/` owns Claude Code / Claude Cowork package metadata.
- `skills/` owns model-facing workflows and bundled helpers, shared unmodified across both host manifests.
- `tests/` owns local deterministic workflow coverage.
- `assets/` owns package presentation assets.
- `Requirements/` owns OKF Manager functional intent.
- `Documentation/` describes the implemented OKF Manager architecture and interfaces.

## Local Contracts

- Preserve functional parity with the supported Agent Zero OKF Manager operations while using native packaging and workflows for each supported host.
- Keep mutable catalogs and retained evidence outside the installed plugin directory.
- Require explicit confirmation before creating a new OKF bundle.
- Preserve source provenance and never execute retained evidence.
- Maintain requirements before implementation and documentation alongside behavior changes.
- Keep `skills/okf/SKILL.md` and its bundled scripts, references, and assets host-agnostic; host-specific behavior lives only in `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `skills/okf/agents/openai.yaml`.

## Work Guidance

- Prefer deterministic helpers for validation, glossary generation, indexing, and visualization.
- Expose the package workflow through the canonical `okf` skill, invoked as `$okf` in Codex and `/okf-manager:okf` (or plain-language request) in Claude Code / Claude Cowork.
- Treat root `glossary.md` as a generated catalog artifact: keep it alphabetically ordered, source-linked, reproducible, and excluded from concept and graph counts.
- Treat `skills/okf/assets/viz-template.html` as the canonical generated graph UI and cover its durable controls with workflow tests.
- Treat ` / ` in concept `type` values as the canonical arbitrary-depth hierarchy separator; generate and verify a recursive type-tree payload and aggregate descendant visibility at every parent branch.
- Keep Agent Zero-specific paths and APIs out of the implementation.
- Treat custom subagents and MCP integration as optional until a validated use case requires them.
- Keep worker dependencies in the user-local OKF Manager cache rather than the installed plugin or user project.
- Keep `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` in sync on shared fields (`version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`) whenever one changes.

## Verification

- Validate `.codex-plugin/plugin.json` with the Codex plugin validator.
- Validate `.claude-plugin/plugin.json` with `claude plugin validate skills/okf-manager` (or load it locally with `claude --plugin-dir skills/okf-manager`).
- Validate each `SKILL.md` with the Codex skill validator; Claude Code loads the same file from `skills/okf/SKILL.md`.
- Compile bundled Python scripts before running them.
- Run `python -m unittest discover -s tests -v` with the user-local worker environment bootstrapped.
- Verify glossary generation is deterministic, alphabetically ordered, link-valid, and excluded from concept and graph counts.
- Verify local marketplace installation and plugin discovery before declaring a local-test milestone ready, for both the Codex marketplace (`.agents/plugins/marketplace.json`) and the Claude Code marketplace (`.claude-plugin/marketplace.json`).

## Child DOX Index

- No child `AGENTS.md` files are currently required; this contract covers the complete package subtree.
