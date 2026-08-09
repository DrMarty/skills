# OKF Manager Requirements

## Functional outcomes

### R-OKF-001: Valid Codex package

The repository shall contain an `okf-manager` directory with a valid Codex plugin manifest and at least one discoverable skill.

### R-OKF-002: Local-first development

The initial implementation shall support validation as a local Codex plugin without requiring a hosted service or MCP server.

### R-OKF-003: Agent Zero behavioral parity

The Codex plugin shall provide the portable behavior of the Agent Zero implementation: catalog discovery, creation confirmation, source inventory, evidence retention, concept listing/reading/writing, guarded web ingestion, validation, indexing, logging guidance, graph generation, and graph verification.

### R-OKF-004: Deterministic catalog operations

Bundle validation, index generation, and graph generation shall use deterministic helpers with explicit inputs, outputs, and failure reporting.

### R-OKF-005: Data separation

Mutable OKF catalogs and retained source evidence shall remain outside the installed plugin directory.

### R-OKF-006: Provenance and safety

The plugin shall preserve source provenance, require confirmation before creating a new catalog bundle, and avoid executing retained source evidence.

### R-OKF-007: Publication readiness

The package structure, metadata, documentation, licensing, and validation approach shall be suitable for eventual publication as a Codex plugin.

### R-OKF-008: Explicit Codex runtime

Codex shall invoke bundled worker operations through a stable runner using explicit paths. Worker dependencies shall be isolated from user projects and the installed plugin package.

### R-OKF-009: Concept integrity

Concept operations shall enforce path-safe IDs, reserved filename protection, required reference-compatible frontmatter, preservation of unknown metadata, citations for generated concept plans, and guarded web-pass updates that do not shrink schemas or citations.

### R-OKF-010: Evidence inventory and retention

Source inventory and raw-evidence retention shall exclude hidden files, repositories, caches, virtual environments, dependency folders, logs, and generated artifacts unless explicitly selected by the user.

### R-OKF-011: Guarded web ingestion

URL ingestion shall require explicit seeds and enforce HTTP(S), allowed hosts, allowed path prefixes, denied path substrings, crawl depth, page budgets, visited-state tracking, response size limits, and user-directed network disclosure.

### R-OKF-012: Optional BigQuery enrichment

BigQuery concept listing, metadata reads, and row sampling shall remain available as optional operations and shall fail clearly when the optional dependency or credentials are unavailable.

### R-OKF-013: End-to-end local verification

Automated tests shall exercise source planning, sequential concept writing, evidence cleanup, concept inspection, validation, index generation, visualization, graph verification, and guarded local HTTP ingestion without requiring external services.

### R-OKF-014: Interactive graph workspace

Generated `viz.html` files shall provide the validated interactive workspace used during Test Project catalog development: quarter-width resizable side panels, a searchable hierarchical concept tree with global/type/concept visibility controls, collapsed type branches on first load, concept detail history, safe Markdown body previews, and in-graph zoom, fit, reset, and popup-help controls.

Reset shall unpin every node and refit the graph. Concept and type visibility controls shall update nodes, links, counts, and indeterminate selection states without requiring regeneration.

## Local-test milestone

The local-test milestone is complete only when the Codex plugin and skill validators pass, the end-to-end worker tests pass, the local marketplace exposes `okf-manager`, Codex reports the plugin as installed, and a fresh Codex task can load the updated skill.
