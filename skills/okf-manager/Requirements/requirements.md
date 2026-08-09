# OKF Manager Requirements

## Functional outcomes

### R-OKF-001: Valid Codex package

The repository shall contain an `okf-manager` directory with a valid Codex plugin manifest and at least one discoverable skill.

### R-OKF-002: Local-first development

The initial implementation shall support validation as a local Codex plugin without requiring a hosted service or MCP server.

### R-OKF-003: Progressive behavioral port

OKF catalog discovery, creation confirmation, evidence preservation, concept maintenance, validation, indexing, logging, and visualization shall be ported incrementally from the Agent Zero implementation.

### R-OKF-004: Deterministic catalog operations

Bundle validation, index generation, and graph generation shall use deterministic helpers with explicit inputs, outputs, and failure reporting.

### R-OKF-005: Data separation

Mutable OKF catalogs and retained source evidence shall remain outside the installed plugin directory.

### R-OKF-006: Provenance and safety

The plugin shall preserve source provenance, require confirmation before creating a new catalog bundle, and avoid executing retained source evidence.

### R-OKF-007: Publication readiness

The package structure, metadata, documentation, licensing, and validation approach shall be suitable for eventual publication as a Codex plugin.

## Initial milestone

The first milestone is limited to repository creation, a valid skills-first plugin scaffold, documentation, and structural validation. It does not port or execute OKF catalog operations.

