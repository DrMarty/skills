# Skills

Codex skills and plugins maintained by DrMarty.

## Plugins

- [`okf-manager`](./skills/okf-manager/): Codex-native OKF Manager plugin with an Agent Zero-compatible functional baseline.

## Repository structure

- `skills/` contains independently packaged Codex skills and plugins.
- `Requirements/` contains repository-wide functional requirements.
- `Documentation/` describes repository-wide architecture and contribution boundaries.
- Each package keeps its own requirements and documentation inside its package directory.

## Development status

The `okf-manager` local-validation milestone provides a skills-first Codex plugin with the portable catalog, ingestion, validation, indexing, visualization, guarded web, and optional BigQuery operations from the [Agent Zero implementation](https://github.com/DrMarty/okf_manager).
