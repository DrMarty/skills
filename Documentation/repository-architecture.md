# Repository Architecture

## Layout

```text
skills-repository/
├── AGENTS.md
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

## Package independence

Packages use lower-case hyphenated directory names and should remain understandable and validatable from within their own directory. Adding or removing a package requires updating the root README and the `skills/AGENTS.md` child index.

