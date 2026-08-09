# Repository Architecture

## Layout

```text
skills-repository/
├── AGENTS.md
├── .agents/plugins/marketplace.json
├── Documentation/
├── Requirements/
└── skills/
    ├── AGENTS.md
    └── <package-name>/
        ├── AGENTS.md
        ├── Documentation/
        ├── Requirements/
        └── <package implementation>
```

Root documentation and requirements govern the collection as a whole. Each package is a durable ownership boundary containing its implementation intent, implementation documentation, validation guidance, and distribution metadata.

The repository-local marketplace exposes canonical package directories for local Codex installation before public submission. Marketplace entries must not require duplicate plugin copies outside `skills/`.

## Package independence

Packages use lower-case hyphenated directory names and should remain understandable and validatable from within their own directory. Adding or removing a package requires updating the root README and the `skills/AGENTS.md` child index.
