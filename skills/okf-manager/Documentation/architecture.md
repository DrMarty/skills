# OKF Manager Architecture

## Initial architecture

OKF Manager begins as a skills-first Codex plugin:

```text
okf-manager/
├── .codex-plugin/
│   └── plugin.json
└── skills/
    └── okf-project-manager/
        └── SKILL.md
```

The skill is the workflow and policy layer. Deterministic helpers will be added beneath the skill as individual Agent Zero behaviors are ported and locally validated.

Package-specific requirements and documentation remain inside the `okf-manager` directory so the package stays self-contained within the multi-skill repository.

## Porting boundaries

- Agent Zero's `plugin.yaml` is replaced by `.codex-plugin/plugin.json`.
- Agent Zero-specific paths, project metadata, browser calls, and subordinate-agent APIs are not carried into Codex unchanged.
- The Agent Zero specialist profile will initially be represented by focused skill instructions.
- A custom Codex subagent remains optional and must not be required for basic plugin operation.
- An MCP server will be considered only when controlled tools, remote services, authentication, or an interactive MCP UI provide a concrete benefit.
- Generated catalogs remain project or user data and are never written into the installed plugin package.

## Progressive milestones

1. Establish and validate the Codex package.
2. Port catalog discovery and creation confirmation.
3. Port deterministic validation and index generation.
4. Port evidence ingestion and provenance handling.
5. Port graph generation and local display.
6. Harden metadata, testing, and documentation for publication.
