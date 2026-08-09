# Skills

Codex skills and plugins maintained by DrMarty.

## Plugins

- [`okf-manager`](./skills/okf-manager/): progressive Codex port of the Agent Zero OKF Manager plugin.

## Repository structure

- `skills/` contains independently packaged Codex skills and plugins.
- `Requirements/` contains repository-wide functional requirements.
- `Documentation/` describes repository-wide architecture and contribution boundaries.
- Each package keeps its own requirements and documentation inside its package directory.

## Development status

The initial `okf-manager` milestone establishes a valid, skills-first Codex plugin package for local validation. OKF ingestion, validation, indexing, and visualization behavior will be ported incrementally from the [Agent Zero implementation](https://github.com/DrMarty/okf_manager).
