# OKF Format Reference

## Bundle model

An OKF bundle is a UTF-8 Markdown directory tree. A concept ID is its relative file path without `.md`.

Reserved names:

- `index.md`: generated progressive-disclosure directory listing.
- `glossary.md`: generated alphabetical extract of terms and acronyms common to at least two concept documents.
- `log.md`: chronological update history.

Every other Markdown file is a concept document.

## Concept frontmatter

Use the stricter reference-compatible profile for durable output:

```yaml
---
type: Concept Type
resource: optional canonical URI
title: Human-readable title
description: One-sentence summary.
tags: [optional, tags]
timestamp: 2026-08-09T00:00:00+00:00
---
```

Require `type`, `title`, `description`, and `timestamp`. Keep tags as a YAML list. Order standard fields as `type`, `resource`, `title`, `description`, `tags`, `timestamp`, followed by preserved extension keys.

## Body conventions

- Use structural Markdown with clear top-level sections.
- Use `# Schema` for fields or columns where applicable.
- Use `# Relationships`, `# Joins`, or relative Markdown links for known relationships.
- Use `# Examples` or `# Common query patterns` for concrete use.
- Use `# Citations` for source files and URLs supporting claims.
- Do not mint unsupported concepts or links from inference alone.

## Update integrity

- Read existing content before updating it.
- Preserve unknown frontmatter keys.
- Prefer focused augmentation over wholesale replacement.
- During web enrichment, never remove existing schema fields or reduce citations.
- Keep concept IDs stable. When renaming is necessary, update all links and validate afterward.
