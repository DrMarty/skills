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
    ├── references/
    ├── requirements-worker.txt
    ├── requirements-bigquery.txt
    └── scripts/
```

The skill owns workflow and policy. References provide progressive disclosure. Scripts provide low-variance filesystem, ingestion, validation, indexing, graph, guarded network, and optional BigQuery operations.

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
