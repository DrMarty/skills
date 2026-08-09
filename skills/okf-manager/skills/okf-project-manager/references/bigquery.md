# Optional BigQuery Enrichment

BigQuery support is optional and requires user-requested dependency installation plus Google Cloud credentials.

Install only when requested:

```text
python <skill-dir>/scripts/okf_run.py install-bigquery
```

Operations:

```text
bigquery-list --dataset <project.dataset> [--billing-project <project>]
bigquery-read --dataset <project.dataset> [--billing-project <project>] <concept-id>
bigquery-sample --dataset <project.dataset> [--billing-project <project>] <tables/name> [--count 5]
```

Use dataset concepts as `datasets/<dataset-id>`. Use table concepts as `tables/<table-id>`. Sharded tables ending in six-to-eight digits are grouped by their stable prefix for discovery; metadata reads use a representative latest shard.

Do not install dependencies, query tables, or sample rows without user authorization. Treat credential, billing-project, API, and permissions failures as external blockers and keep local bundle operations available.

