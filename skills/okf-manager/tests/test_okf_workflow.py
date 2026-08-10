from __future__ import annotations

import functools
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PACKAGE_ROOT / "skills" / "okf-project-manager"
RUNNER = SKILL_ROOT / "scripts" / "okf_run.py"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


class OkfWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="okf-manager-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        (self.source / "docs").mkdir(parents=True)
        (self.source / ".git").mkdir()
        (self.source / "node_modules").mkdir()
        (self.source / "README.md").write_text("# Demo\n\nEvidence.\n", encoding="utf-8")
        (self.source / "docs" / "notes.txt").write_text("Notes.\n", encoding="utf-8")
        (self.source / ".git" / "config").write_text("ignored\n", encoding="utf-8")
        (self.source / "node_modules" / "ignored.js").write_text("ignored\n", encoding="utf-8")
        self.catalog = self.root / "project" / "okf" / "catalog"
        self.plan = self.root / "plan.json"
        self.plan.write_text(json.dumps({
            "raw_name": "demo",
            "raw_sources": ["README.md", "docs/notes.txt"],
            "concepts": [
                {
                    "concept_id": "systems/demo",
                    "frontmatter": {"type": "System", "title": "Demo", "description": "Demo system."},
                    "body": "The Control Loop exposes an Application Programming Interface (API).\n\n# Schema\n\n- `id`: identifier\n\n# Citations\n\n- [README](../../raw/demo/README.md)",
                },
                {
                    "concept_id": "concepts/related",
                    "frontmatter": {"type": "Concept", "title": "Related", "description": "Related concept."},
                    "body": "The Control Loop uses the API for coordination. See [Demo](../systems/demo.md).\n\n# Citations\n\n- [Notes](../../raw/demo/docs/notes.txt)",
                },
            ],
        }, indent=2), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_okf(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--no-bootstrap", *map(str, args)],
            text=True,
            capture_output=True,
        )
        if result.returncode != expect:
            self.fail(f"command returned {result.returncode}, expected {expect}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def test_end_to_end_local_catalog(self) -> None:
        inventory = self.root / "inventory.json"
        self.run_okf("plan-sources", "--source-root", self.source, "--out", inventory)
        inventory_data = json.loads(inventory.read_text(encoding="utf-8"))
        self.assertEqual(inventory_data["file_count"], 2)
        self.assertEqual({item["path"] for item in inventory_data["files"]}, {"README.md", "docs/notes.txt"})

        self.run_okf("bulk-write", "--catalog", self.catalog, "--plan", self.plan, "--source-root", self.source, expect=1)
        self.assertFalse(self.catalog.exists())
        self.run_okf("bulk-write", "--catalog", self.catalog, "--plan", self.plan, "--source-root", self.source, "--allow-create")

        listed = json.loads(self.run_okf("concept-list", "--catalog", self.catalog).stdout)
        self.assertEqual(listed["concept_count"], 2)
        read = json.loads(self.run_okf("concept-read", "--catalog", self.catalog, "systems/demo").stdout)
        self.assertEqual(read["frontmatter"]["title"], "Demo")
        self.assertTrue(read["frontmatter"]["timestamp"])

        bad_update = self.root / "bad-update.json"
        bad_update.write_text(json.dumps({
            "concept_id": "systems/demo",
            "frontmatter": {"description": "Web enriched."},
            "body": "No schema.\n\n# Citations\n\n- https://example.invalid",
        }), encoding="utf-8")
        self.run_okf("concept-write", "--catalog", self.catalog, bad_update, "--web-pass", expect=1)

        good_update = self.root / "good-update.json"
        good_update.write_text(json.dumps({
            "concept_id": "systems/demo",
            "frontmatter": {"description": "Web enriched."},
            "body": "Updated Control Loop with an Application Programming Interface (API).\n\n# Schema\n\n- `id`: identifier\n\n# Citations\n\n- [README](../../raw/demo/README.md)",
        }), encoding="utf-8")
        self.run_okf("concept-write", "--catalog", self.catalog, good_update, "--web-pass")
        self.run_okf("log", "--catalog", self.catalog, "Updated demo concepts")
        pipeline = self.run_okf("pipeline", "--catalog", self.catalog, "--min-concepts", "2", "--min-edges", "1")
        self.assertIn('"ok": true', pipeline.stdout.lower())
        graph = json.loads(self.run_okf("verify-graph", "--catalog", self.catalog, "--min-concepts", "2", "--min-edges", "1").stdout)
        self.assertEqual(graph["mode"], "live-d3-self-graph")
        self.assertGreaterEqual(graph["concepts"], 2)
        self.assertGreaterEqual(graph["edges"], 1)
        self.assertTrue((self.catalog / "index.md").exists())
        glossary_path = self.catalog / "glossary.md"
        self.assertTrue(glossary_path.exists())
        glossary = glossary_path.read_text(encoding="utf-8")
        self.assertIn("| API | Application Programming Interface |", glossary)
        self.assertIn("| Control Loop | — |", glossary)
        self.assertLess(glossary.index("| API |"), glossary.index("| Control Loop |"))
        first_glossary = glossary_path.read_bytes()
        glossary_result = json.loads(self.run_okf("glossary", "--catalog", self.catalog).stdout)
        self.assertGreaterEqual(glossary_result["entry_count"], 2)
        self.assertEqual(first_glossary, glossary_path.read_bytes())
        listed_after_glossary = json.loads(self.run_okf("concept-list", "--catalog", self.catalog).stdout)
        self.assertEqual(listed_after_glossary["concept_count"], 2)
        self.assertIn("[glossary](glossary.md)", (self.catalog / "index.md").read_text(encoding="utf-8"))
        viz = (self.catalog / "viz.html").read_text(encoding="utf-8")
        self.assertIn('--left-panel-width:clamp(240px, 25vw, 520px)', viz)
        self.assertIn('id="conceptTree"', viz)
        self.assertIn('id="navigationSection"', viz)
        self.assertIn('id="glossarySection"', viz)
        self.assertIn('id="sidebarSplitter"', viz)
        self.assertIn('id="glossaryList"', viz)
        self.assertIn('function initSidebarSections()', viz)
        self.assertIn('function renderGlossary()', viz)
        self.assertIn('"term": "API"', viz)
        self.assertIn('id="typesToggleAll"', viz)
        self.assertIn('class="tree-type" data-type=', viz)
        self.assertNotIn('class="tree-type" data-type="System" open', viz)
        self.assertIn('class="concept-toggle"', viz)
        self.assertNotIn('id="typeFilter"', viz)
        self.assertIn('id="detailBack"', viz)
        self.assertIn('id="detailForward"', viz)
        self.assertIn('class="detail-sections" id="detailSections"', viz)
        self.assertIn("detailSectionHtml(0, 'outgoing', 'Outgoing Links'", viz)
        self.assertIn("detailSectionHtml(1, 'backlinks', 'Backlinks'", viz)
        self.assertIn("detailSectionHtml(2, 'bodyPreview', 'Body Preview'", viz)
        self.assertIn('id="outgoingSplitter"', viz)
        self.assertIn('id="backlinksSplitter"', viz)
        self.assertIn('function layoutDetailSections(', viz)
        self.assertIn('function initDetailSections(', viz)
        self.assertIn('function renderMarkdown(', viz)
        self.assertIn('id="fitBtn"', viz)
        self.assertIn('id="resetBtn"', viz)
        self.assertIn('id="helpBtn"', viz)
        self.assertIn('id="aboutBtn"', viz)
        self.assertIn('id="aboutPopover"', viz)
        self.assertIn('id="aboutPluginName"', viz)
        self.assertIn('id="aboutPluginVersion"', viz)
        self.assertIn('id="aboutPluginLink"', viz)
        manifest = json.loads((PACKAGE_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn(f'"version": "{manifest["version"]}"', viz)
        self.assertIn('"name": "OKF Manager"', viz)
        self.assertIn('https://github.com/DrMarty/skills/tree/master/skills/okf-manager', viz)
        self.assertIn('nodes.forEach(n => { n.fx = null; n.fy = null; });', viz)
        self.assertIn("event.key === 'Escape'", viz)
        self.assertTrue((self.catalog.parent / "raw" / "demo" / "README.md").exists())

    def test_guarded_web_fetch(self) -> None:
        web_root = self.root / "web"
        (web_root / "guide").mkdir(parents=True)
        (web_root / "guide" / "index.html").write_text('<html><head><title>Start</title></head><body><a href="next.html">Next</a><h1>Start</h1></body></html>', encoding="utf-8")
        (web_root / "guide" / "next.html").write_text('<html><head><title>Next</title></head><body><h1>Next</h1></body></html>', encoding="utf-8")
        handler = functools.partial(QuietHandler, directory=str(web_root))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host = f"127.0.0.1:{server.server_port}"
            seed = f"http://{host}/guide/index.html"
            next_url = f"http://{host}/guide/next.html"
            state = self.root / "crawl-state.json"
            first = json.loads(self.run_okf(
                "fetch-url", seed,
                "--state", state,
                "--seed", seed,
                "--allowed-host", host,
                "--allowed-path-prefix", "/guide/",
                "--max-pages", "2",
                "--max-depth", "1",
            ).stdout)
            self.assertEqual(first["title"], "Start")
            second = json.loads(self.run_okf("fetch-url", next_url, "--state", state).stdout)
            self.assertEqual(second["title"], "Next")
            self.run_okf("fetch-url", seed, "--state", state, expect=1)
            saved_state = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(saved_state["fetched_count"], 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
