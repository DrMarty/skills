from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
SKILL_MD = PACKAGE_ROOT / "skills" / "okf" / "SKILL.md"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"{path} is missing a YAML frontmatter block"
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter


class ClaudePluginPackagingTest(unittest.TestCase):
    """R-OKF-020: the okf skill must be independently installable in Claude Code
    without forking its content out of the Codex-native package."""

    def test_claude_plugin_manifest_is_valid(self) -> None:
        manifest = _load_json(PACKAGE_ROOT / ".claude-plugin" / "plugin.json")
        self.assertEqual(manifest["name"], "okf-manager")
        for field in ("description", "version", "author", "homepage", "repository", "license"):
            self.assertIn(field, manifest)
        # Claude Code auto-discovers skills/, so no "skills" pointer is required
        # or expected here (unlike the Codex manifest).
        self.assertNotIn("skills", manifest)

    def test_codex_and_claude_manifests_share_identity_fields(self) -> None:
        codex_manifest = _load_json(PACKAGE_ROOT / ".codex-plugin" / "plugin.json")
        claude_manifest = _load_json(PACKAGE_ROOT / ".claude-plugin" / "plugin.json")
        self.assertEqual(codex_manifest["name"], claude_manifest["name"])
        self.assertEqual(codex_manifest["description"], claude_manifest["description"])
        self.assertEqual(codex_manifest["license"], claude_manifest["license"])
        self.assertEqual(codex_manifest["homepage"], claude_manifest["homepage"])
        self.assertEqual(codex_manifest["repository"], claude_manifest["repository"])

    def test_root_claude_marketplace_points_at_canonical_package(self) -> None:
        marketplace = _load_json(REPO_ROOT / ".claude-plugin" / "marketplace.json")
        self.assertIn("plugins", marketplace)
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        self.assertIn("okf-manager", entries)
        self.assertEqual(entries["okf-manager"]["source"], "./skills/okf-manager")

    def test_skill_frontmatter_is_shared_and_host_agnostic(self) -> None:
        frontmatter = _skill_frontmatter(SKILL_MD)
        self.assertEqual(frontmatter.get("name"), "okf")
        self.assertTrue(frontmatter.get("description"), "SKILL.md needs a non-empty description")
        body = SKILL_MD.read_text(encoding="utf-8")
        # The body must stay usable by any host: no runner logic gated on a
        # specific coding assistant.
        self.assertNotIn("codex_only", body.lower())


if __name__ == "__main__":
    unittest.main()
