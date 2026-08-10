# OKF Manager Architecture

## Package structure

```text
okf-manager/
├── .codex-plugin/plugin.json
├── assets/
├── Documentation/
├── Requirements/
├── tests/
└── skills/okf-project-manager/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/viz-template.html
    ├── references/
    ├── requirements-worker.txt
    ├── requirements-bigquery.txt
    └── scripts/
```

The skill owns workflow and policy. References provide progressive disclosure. Scripts provide low-variance filesystem, ingestion, validation, glossary, indexing, graph, guarded network, and optional BigQuery operations. `assets/viz-template.html` is the canonical interactive graph shell; `okf_visualize_bundle.py` injects escaped bundle identity and serialized graph data into its placeholders.

## Glossary interface

`okf_generate_glossary.py` scans concept Markdown while excluding generated documents and raw evidence. It recognizes explicit acronym definitions, repeated uppercase acronyms, frontmatter titles and tags, Markdown headings, and conservative capitalized multi-word phrases. Candidates must occur in at least two distinct concepts. The generated root `glossary.md` lists entries case-insensitively in alphabetical order, preserves a deterministic expansion or matching concept description when available, and links to every contributing concept. It is a derived catalog document, not a concept or graph node.

## Visualization interface

The graph shell uses three resizable desktop regions: a left navigation/glossary sidebar, a D3 graph canvas, and concept details. The left sidebar has independently collapsible sections separated by a draggable horizontal splitter: concept search and the hierarchical navigation tree above, and the generated catalog glossary below. Glossary source links select the corresponding graph concept. The tree has global, type, and concept visibility controls with live counts and starts with only its top-level Types branch expanded. The detail panel keeps concept metadata and back/forward history above independently collapsible, vertically resizable Outgoing Links, Backlinks, and Body Preview sections. Body Preview renders a safe Markdown subset, and links in every detail section follow the same concept-selection path. Canvas controls provide zoom, fit, reset-unpin-refit, and dismissible help. The header About control displays the generator name, manifest-derived plugin version, and canonical GitHub installation/update link. Generated graph, glossary, and generator metadata remain embedded in `viz.html`; D3 is loaded from jsDelivr when the page opens.

## Runtime

`okf_run.py` is the stable entry point. On first use it bootstraps a worker virtual environment beneath the user-local Codex cache:

- Windows: `%LOCALAPPDATA%/Codex/okf-manager/venv`
- Other platforms: `${XDG_CACHE_HOME:-~/.cache}/codex/okf-manager/venv`

`OKF_MANAGER_HOME` overrides the worker-data root for isolated tests. Mutable catalogs and raw evidence remain outside the plugin package.

## Agent Zero parity map

| Agent Zero behavior | Codex implementation |
| --- | --- |
| `okf_context` | Explicit catalog/source arguments resolved by `SKILL.md` |
| list/read/write concept tools | `okf_concepts.py` and runner commands |
| source inventory and bulk write | `okf_plan_sources.py`, `okf_bulk_write.py` |
| raw evidence cleanup | `okf_clean_raw.py` |
| validation and link lint | `okf_validate_bundle.py`, `okf_lint_catalog.py` |
| generated indexes | `okf_regenerate_indexes.py` |
| generated glossary | `okf_generate_glossary.py` |
| live graph and verification | `okf_visualize_bundle.py`, `okf_verify_graph.py` |
| guarded URL fetch state | `okf_fetch_url.py` |
| BigQuery discovery/read/sample | optional `okf_bigquery.py` |
| specialist-agent orchestration | concise Codex skill plus deterministic runner |

Agent Zero profile registries, `/a0` paths, `call_subordinate`, and framework tool shims are intentionally not copied because Codex supplies its own skill and tool orchestration.

## Safety boundaries

- Catalog creation requires both conversational confirmation and `--allow-create`.
- Raw evidence is never an execution location.
- Source inventory and copying exclude internal/generated paths.
- Web crawling is explicit, stateful, and guard-limited.
- Web-pass writes preserve existing schemas, citations, and unknown metadata.
- BigQuery remains optional and credential-dependent.
