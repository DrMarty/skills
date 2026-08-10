# Guarded Web Ingestion

Disclose network use and obtain explicit seed URLs or approval before fetching.

## Required guards

- Permit only `http` and `https`.
- Default allowed hosts to the approved seed hosts.
- Narrow allowed path prefixes when the source site is broad.
- Deny login, account, logout, administration, search, or other irrelevant paths when appropriate.
- Set deliberate maximum pages and crawl depth.
- Persist crawl state so visited URLs, discovered depth, and page budget survive separate calls.
- Fetch only approved seeds or links reachable from them within the saved crawl graph.

Example:

```text
fetch-url https://docs.example.com/start \
  --state <catalog-parent>/raw/vendor/crawl-state.json \
  --seed https://docs.example.com/start \
  --allowed-host docs.example.com \
  --allowed-path-prefix /guide/ \
  --denied-path-substring /login \
  --max-pages 20 \
  --max-depth 2 \
  --out <catalog-parent>/raw/vendor/start.json
```

On PowerShell, provide the same arguments on one line or use PowerShell continuation syntax.

## Enrichment workflow

1. List existing concepts once.
2. Fetch approved pages sequentially with one state file.
3. Preserve fetched JSON or a URL manifest under sibling raw evidence.
4. Augment a matching concept, mint a reusable `references/<slug>` concept, or skip the page.
5. Read an existing concept before changing it.
6. Use `concept-write --web-pass` for guarded augmentation.
7. Cite only fetched URLs or sources already present in the catalog.
8. Run the full validation pipeline after changes.

