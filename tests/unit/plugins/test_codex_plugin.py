"""Tests for the Codex plugin bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "deepwork"
SKILLS_DIR = PLUGIN_DIR / "skills"
MARKETPLACE_PATH = PROJECT_ROOT / ".agents" / "plugins" / "marketplace.json"


def _parse_yaml_frontmatter(skill_path: Path) -> dict[str, Any]:
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


class TestPluginManifest:
    manifest_path = PLUGIN_DIR / ".codex-plugin" / "plugin.json"

    def test_manifest_exists(self) -> None:
        assert self.manifest_path.exists()

    def test_manifest_name_is_deepwork(self) -> None:
        data = json.loads(self.manifest_path.read_text())
        assert data["name"] == "deepwork"

    def test_manifest_references_skills_and_mcp_config(self) -> None:
        data = json.loads(self.manifest_path.read_text())
        assert data["skills"] == "./skills/"
        assert data["mcpServers"] == "./.mcp.json"


class TestMarketplace:
    def test_marketplace_exists(self) -> None:
        assert MARKETPLACE_PATH.exists()

    def test_marketplace_registers_local_plugin(self) -> None:
        data = json.loads(MARKETPLACE_PATH.read_text())
        plugin = next(entry for entry in data["plugins"] if entry["name"] == "deepwork")
        assert plugin["source"]["source"] == "local"
        assert plugin["source"]["path"] == "./plugins/deepwork"


class TestReviewReferenceDocumentation:
    symlink_path = PLUGIN_DIR / "README_REVIEWS.md"

    def test_readme_reviews_exists(self) -> None:
        assert self.symlink_path.exists()

    def test_readme_reviews_is_symlink(self) -> None:
        assert self.symlink_path.is_symlink()

    def test_symlink_target(self) -> None:
        assert str(self.symlink_path.readlink()) == "../../README_REVIEWS.md"

    def test_example_reviews_exist(self) -> None:
        assert (PLUGIN_DIR / "example_reviews" / "prompt_best_practices.md").is_symlink()
        assert (PLUGIN_DIR / "example_reviews" / "suggest_new_reviews.md").is_symlink()


class TestMCPServerRegistration:
    mcp_json_path = PLUGIN_DIR / ".mcp.json"

    def test_mcp_json_exists(self) -> None:
        assert self.mcp_json_path.exists()

    def test_mcp_json_registers_deepwork_server(self) -> None:
        data = json.loads(self.mcp_json_path.read_text())
        assert "deepwork" in data["mcpServers"]

    def test_mcp_command_is_uvx_deepwork_serve(self) -> None:
        data = json.loads(self.mcp_json_path.read_text())
        server = data["mcpServers"]["deepwork"]
        assert server["command"] == "uvx"
        assert server["args"][:2] == ["deepwork", "serve"]

    def test_mcp_args_include_codex_platform_and_path(self) -> None:
        data = json.loads(self.mcp_json_path.read_text())
        args = data["mcpServers"]["deepwork"]["args"]
        assert args[args.index("--platform") + 1] == "codex"
        assert args[args.index("--path") + 1] == "."


class TestSkills:
    def test_skill_files_exist(self) -> None:
        expected = {"deepwork", "review", "configure_reviews", "deepschema"}
        actual = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
        assert expected <= actual
        for skill_name in expected:
            assert (SKILLS_DIR / skill_name / "SKILL.md").exists()

    def test_frontmatter_names_match_directories(self) -> None:
        for skill_dir in (path for path in SKILLS_DIR.iterdir() if path.is_dir()):
            fm = _parse_yaml_frontmatter(skill_dir / "SKILL.md")
            assert fm["name"] == skill_dir.name

    def test_deepwork_skill_references_workflow_tools(self) -> None:
        content = (SKILLS_DIR / "deepwork" / "SKILL.md").read_text(encoding="utf-8")
        for tool in ("get_workflows", "start_workflow", "finished_step"):
            assert tool in content

    def test_review_skill_references_review_tools(self) -> None:
        content = (SKILLS_DIR / "review" / "SKILL.md").read_text(encoding="utf-8")
        assert "get_configured_reviews" in content
        assert "get_review_instructions" in content
        assert "AskUserQuestion" in content
        assert "configure_reviews" in content

    def test_configure_reviews_skill_references_review_docs_and_tools(self) -> None:
        content = (SKILLS_DIR / "configure_reviews" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "README_REVIEWS.md" in content
        assert "get_review_instructions" in content

    def test_deepschema_skill_references_schema_discovery(self) -> None:
        content = (SKILLS_DIR / "deepschema" / "SKILL.md").read_text(encoding="utf-8")
        assert "get_named_schemas" in content
