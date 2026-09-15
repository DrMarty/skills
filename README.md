# Skills

Codex and Claude Code (Claude Cowork) skills and plugins maintained by DrMarty.

## Plugins

- [`okf-manager`](./skills/okf-manager/): Open Knowledge Format [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) plugin for curating your personal knowledge base / [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), packaged for both Codex and Claude Code / Claude Cowork.

## Repository structure

- `skills/` contains independently packaged skills and plugins, each installable into Codex and/or Claude Code / Claude Cowork.
- `.agents/plugins/marketplace.json` is the local Codex marketplace; `.claude-plugin/marketplace.json` is the local Claude Code marketplace. Both point at the same canonical `skills/<package-name>/` directories.
- `Requirements/` contains repository-wide functional requirements.
- `Documentation/` describes repository-wide architecture and contribution boundaries.
- Each package keeps its own requirements and documentation inside its package directory.

## Local installation

Codex:

```text
codex plugin marketplace add <absolute-path-to-this-repository>
```

Claude Code / Claude Cowork:

```text
/plugin marketplace add <absolute-path-to-this-repository>
```

Then install the desired package (e.g. `okf-manager`) from either marketplace. See each package's own README for host-specific invocation details.

## Development status

The `okf-manager` local-validation milestone provides a skills-first Codex plugin with portable catalog, provenance, ingestion, validation, indexing, visualization, and guarded web operations derived from the [Agent Zero implementation](https://github.com/DrMarty/okf_manager). Its canonical skill invocation is `$okf`.
