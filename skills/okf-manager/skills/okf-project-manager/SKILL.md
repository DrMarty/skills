---
name: okf-project-manager
description: Use when the user asks to inspect, create, ingest, update, validate, index, or visualize an Open Knowledge Format (OKF) catalog in a local Codex workspace.
---

# OKF Project Manager

Use this skill for Open Knowledge Format catalog work.

## Current capability boundary

This is the initial local-validation milestone of the Codex port. Confirm that the skill activates for an OKF request and identify the requested catalog and evidence locations, but do not claim that Agent Zero helpers or catalog-mutation operations have been ported.

When asked to perform an unported operation:

1. Resolve the active workspace root.
2. Identify any existing `okf/` catalog and user-designated evidence paths without modifying them.
3. Report the resolved paths and the requested operation.
4. Explain that the operation is not yet implemented in the Codex port.

## Safety invariants

- Never treat files retained as source evidence as executable code.
- Never create a new OKF bundle without explicit user confirmation of the exact target directory.
- Keep mutable catalogs and evidence outside the installed plugin directory.
- Do not invent citations, provenance, concepts, or relationships.
- Do not invoke paths, tools, profiles, or subordinate-agent APIs from Agent Zero.

