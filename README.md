# Skills

Codex skills and plugins maintained by DrMarty.

## Plugins

- [`okf-manager`](./skills/okf-manager/): Codex-native Open Knowledge Format [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) plugin for curating your personal knowledge base / [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Repository structure

- `skills/` contains independently packaged Codex skills and plugins.
- `Requirements/` contains repository-wide functional requirements.
- `Documentation/` describes repository-wide architecture and contribution boundaries.
- Each package keeps its own requirements and documentation inside its package directory.

## Development status

The `okf-manager` local-validation milestone provides a skills-first Codex plugin with portable catalog, provenance, ingestion, validation, indexing, visualization, and guarded web operations derived from the [Agent Zero implementation](https://github.com/DrMarty/okf_manager). Its canonical skill invocation is `$okf`.
