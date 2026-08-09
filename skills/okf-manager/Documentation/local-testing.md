# Local Testing

## Validate implementation

From the repository root on Windows PowerShell:

```powershell
python skills/okf-manager/skills/okf-project-manager/scripts/okf_bootstrap_env.py
python -m unittest discover -s skills/okf-manager/tests -v
```

Also run the Codex plugin validator against `skills/okf-manager` and the skill validator against `skills/okf-manager/skills/okf-project-manager`.

## Install into Codex

Add the repository marketplace once:

```powershell
codex plugin marketplace add "<absolute-repository-root>"
```

Open the Codex Plugins interface, select `okf-manager` from **DrMarty Skills (Local)**, and install it. The current CLI exposes marketplace management but does not install individual plugins.

Start a new Codex task so the installed skill metadata is loaded. During development, reinstall the plugin after package changes so Codex refreshes its cached copy.

## Suggested smoke prompts

- `Use $okf-project-manager to inspect the OKF catalog in this workspace.`
- `Use $okf-project-manager to validate this catalog and report broken links.`
- `Use $okf-project-manager to regenerate the catalog glossary and show the common terms and acronyms.`
- `Use $okf-project-manager to ingest these source files into a new OKF catalog.`
- `Use $okf-project-manager to regenerate and show the catalog graph.`

New bundle creation should pause for confirmation of the exact catalog path before any directory is created.

Graph generation is local, but the generated interactive page loads D3 from jsDelivr when opened.
