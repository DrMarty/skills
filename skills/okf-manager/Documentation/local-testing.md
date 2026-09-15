# Local Testing

## Validate implementation

From the repository root on Windows PowerShell:

```powershell
python skills/okf-manager/skills/okf/scripts/okf_bootstrap_env.py
python -m unittest discover -s skills/okf-manager/tests -v
```

Also run the Codex plugin validator against `skills/okf-manager` and the skill validator against `skills/okf-manager/skills/okf`.

## Install into Codex

Add the repository marketplace once:

```powershell
codex plugin marketplace add "<absolute-repository-root>"
```

Open the Codex Plugins interface, select `okf-manager` from **DrMarty Skills (Local)**, and install it. The current CLI exposes marketplace management but does not install individual plugins.

Start a new Codex task so the installed skill metadata is loaded. During development, reinstall the plugin after package changes so Codex refreshes its cached copy.

## Install into Claude Code / Claude Cowork

Validate the manifest, then load the package directly for local development:

```powershell
claude plugin validate skills/okf-manager
claude --plugin-dir skills/okf-manager
```

To install through a marketplace instead (matching how an end user would get it):

```text
/plugin marketplace add "<absolute-repository-root>"
/plugin install okf-manager@drmarty-skills
```

Run `/reload-plugins` after package changes during development instead of restarting. `claude plugin marketplace add "<absolute-repository-root>"` from the CLI is equivalent to the `/plugin marketplace add` slash command.

## Suggested smoke prompts

Codex (`$okf`):

- `Use $okf to inspect the OKF catalog in this workspace.`
- `Use $okf to validate this catalog and report broken links.`
- `Use $okf to regenerate the catalog glossary and show the common terms and acronyms.`
- `Use $okf to ingest these source files into a new OKF catalog.`
- `Use $okf to regenerate and show the catalog graph.`

Claude Code / Claude Cowork (`/okf-manager:okf`, or plain language):

- `Inspect the OKF catalog in this workspace.`
- `/okf-manager:okf validate this catalog and report broken links.`
- `Regenerate the catalog glossary and show the common terms and acronyms.`
- `Ingest these source files into a new OKF catalog.`
- `Regenerate and show the catalog graph.`

New bundle creation should pause for confirmation of the exact catalog path before any directory is created, on either host.

Graph generation is local, but the generated interactive page loads D3 from jsDelivr when opened.
