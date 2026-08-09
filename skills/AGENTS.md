# Skills Collection

## Purpose

- Own all Codex skill and plugin packages published from this repository.

## Ownership

- Each direct child directory is an independently versioned skill or plugin package.
- Package-specific requirements, documentation, source, assets, and verification belong inside that package directory.

## Local Contracts

- Do not place package-specific requirements or documentation at repository root.
- Give every durable package its own `AGENTS.md`, `Requirements/Index.md`, and `Documentation/Index.md`.
- Keep plugin manifests and package metadata self-contained and publication-ready.

## Work Guidance

- Add new packages as `skills/<package-name>/` using lower-case hyphenated names.
- Update the repository README when adding or removing a package.

## Verification

- Validate changed plugin manifests and skill frontmatter with the available Codex plugin and skill validators.
- Run deterministic package-specific checks documented by the package before publishing changes.

## Child DOX Index

- `okf-manager/AGENTS.md` owns the OKF Manager Codex plugin and its progressive Agent Zero port.

