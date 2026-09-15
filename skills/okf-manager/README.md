# OKF Manager

OKF Manager ports the portable behavior of the [Agent Zero OKF Manager](https://github.com/DrMarty/okf_manager) into a skills-first plugin. The package ships one shared skill, `skills/okf/SKILL.md`, packaged behind two host manifests so it installs unmodified into Codex and into Claude Code / Claude Cowork.

It supports:

- catalog discovery and confirmation-gated creation;
- file inventory, JSON concept planning, and raw evidence retention;
- concept listing, reading, guarded writing, and chronological logs;
- strict frontmatter and relative-link validation;
- deterministic alphabetical glossary generation for common terms and acronyms;
- deterministic index generation;
- interactive `viz.html` graph generation with an embedded glossary, arbitrary-depth recursive type navigation and visibility controls, collapsible and resizable side-panel sections, Markdown details, navigation history, manifest-derived About information, and payload verification;
- stateful, host/path/depth/page-limited web ingestion.

The package uses a user-local worker environment and does not require an MCP server or hosted service for local catalog operation.

## Local installation

### Codex

This repository exposes the plugin through its local Codex marketplace:

```text
codex plugin marketplace add <absolute-path-to-this-repository>
```

Then open the Codex Plugins interface, select `okf-manager` from **DrMarty Skills (Local)**, and install it. Start a new Codex task after installation. Invoke the installed skill as `$okf`.

### Claude Code / Claude Cowork

This repository also exposes the plugin through a Claude Code marketplace at `.claude-plugin/marketplace.json`:

```text
/plugin marketplace add <absolute-path-to-this-repository>
/plugin install okf-manager@drmarty-skills
```

(or `claude plugin marketplace add <path>` / `claude --plugin-dir <path>/skills/okf-manager` from the CLI). Invoke the installed skill as `/okf-manager:okf`, or let Claude invoke it automatically from a plain-language request — its description covers OKF catalog creation, ingestion, validation, and visualization.

See [`Documentation/local-testing.md`](./Documentation/local-testing.md) for validation commands and smoke prompts for both hosts.

See [`Requirements`](./Requirements/Index.md) and [`Documentation`](./Documentation/Index.md) for the governing requirements and architecture.
