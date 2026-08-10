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

### R-OKF-015: Generated catalog glossary

The plugin shall maintain a root-level `glossary.md` as a deterministic generated catalog artifact. It shall extract conservatively identified common terms and acronyms from concept documents, require common terms to occur in at least two distinct concepts, retain explicit acronym expansions when present, order entries alphabetically without regard to case, and link every entry to its contributing concepts.

Glossary generation shall be available as an individual runner command and shall run before index generation in the normal pipeline. Generated glossary content shall be validated for links, excluded from concept counts and graph nodes, and reproducible for unchanged catalog input.

### R-OKF-016: Split navigation and glossary sidebar

The generated graph workspace shall divide its left sidebar into independently collapsible navigation and glossary sections separated by a draggable horizontal resize control. The upper section shall contain concept search and the hierarchical navigation tree. The lower section shall render the generated catalog glossary, including meanings and links to contributing concepts.

Glossary concept links shall select the associated graph node and update the detail panel through the same navigation path as a node click. Collapsing either section shall make the remaining expanded section use the available sidebar height.

### R-OKF-017: Sectioned concept details sidebar

The generated graph workspace shall divide the concept-detail content into independently collapsible Outgoing Links, Backlinks, and Body Preview sections. Adjacent sections shall be separated by draggable horizontal resize controls, while concept identity, metadata, and navigation-history controls remain available above the section stack.

Collapsing a detail section shall redistribute the available height among the remaining expanded sections. Links in the Outgoing Links, Backlinks, and Markdown Body Preview sections shall continue to select the associated concept through the normal detail-navigation path.

### R-OKF-018: Generator identity and update information

The generated graph workspace shall provide an About control in the upper-right header. Activating it shall display the generator name, the exact plugin version read from the plugin manifest, and a clickable canonical GitHub URL for plugin installation and updates.

The About display shall support explicit dismissal, outside-click dismissal, and Escape-key dismissal without navigating away from the graph.

## Local-test milestone

The local-test milestone is complete only when the Codex plugin and skill validators pass, the end-to-end worker tests pass, the local marketplace exposes `okf-manager`, Codex reports the plugin as installed, and a fresh Codex task can load the updated skill.
