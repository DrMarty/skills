# OKF Manager for Codex

OKF Manager ports the portable behavior of the [Agent Zero OKF Manager](https://github.com/DrMarty/okf_manager) into a skills-first Codex plugin.

It supports:

- catalog discovery and confirmation-gated creation;
- file inventory, JSON concept planning, and raw evidence retention;
- concept listing, reading, guarded writing, and chronological logs;
- strict frontmatter and relative-link validation;
- deterministic alphabetical glossary generation for common terms and acronyms;
- deterministic index generation;
- interactive `viz.html` graph generation with an embedded glossary, hierarchical visibility controls, collapsible and resizable side-panel sections, Markdown details, navigation history, and payload verification;
- stateful, host/path/depth/page-limited web ingestion;
- optional BigQuery concept discovery, metadata reads, and sampling.

The package uses a user-local worker environment and does not require an MCP server or hosted service for local catalog operation.

## Local installation

This repository exposes the plugin through its local marketplace:

```text
codex plugin marketplace add <absolute-path-to-this-repository>
```

Then open the Codex Plugins interface, select `okf-manager` from **DrMarty Skills (Local)**, and install it. Start a new Codex task after installation. See [`Documentation/local-testing.md`](./Documentation/local-testing.md) for validation commands and smoke prompts.

See [`Requirements`](./Requirements/Index.md) and [`Documentation`](./Documentation/Index.md) for the governing requirements and architecture.
