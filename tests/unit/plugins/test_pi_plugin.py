"""Tests for the Pi CLI DeepWork package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ROOT_PACKAGE = PROJECT_ROOT / "package.json"
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "pi"
SKILLS_DIR = PLUGIN_DIR / "skills"


def _parse_yaml_frontmatter(skill_path: Path) -> dict[str, Any]:
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


class TestPiPackageManifest:
    def test_root_package_exposes_pi_resources(self) -> None:
        data = json.loads(ROOT_PACKAGE.read_text(encoding="utf-8"))
        assert "pi-package" in data["keywords"]
        assert "plugins/pi/extensions/index.ts" in data["pi"]["extensions"]
        assert "plugins/pi/skills" in data["pi"]["skills"]

    def test_plugin_package_exposes_pi_resources(self) -> None:
        data = json.loads((PLUGIN_DIR / "package.json").read_text(encoding="utf-8"))
        assert "pi-package" in data["keywords"]
        assert "./extensions/index.ts" in data["pi"]["extensions"]
        assert "./skills" in data["pi"]["skills"]

    def test_mcp_adapter_is_packaged(self) -> None:
        root_data = json.loads(ROOT_PACKAGE.read_text(encoding="utf-8"))
        plugin_data = json.loads((PLUGIN_DIR / "package.json").read_text(encoding="utf-8"))
        assert "pi-mcp-adapter" in root_data["dependencies"]
        assert "pi-mcp-adapter" in plugin_data["dependencies"]


class TestPiMcpConfig:
    mcp_path = PLUGIN_DIR / "mcp.json.example"

    def test_example_registers_deepwork_server(self) -> None:
        data = json.loads(self.mcp_path.read_text(encoding="utf-8"))
        server = data["mcpServers"]["deepwork"]
        assert server["command"] == "uvx"
        assert server["args"][:2] == ["deepwork", "serve"]
        assert "--platform" in server["args"]
        assert server["args"][server["args"].index("--platform") + 1] == "pi"

    def test_example_promotes_core_tools(self) -> None:
        data = json.loads(self.mcp_path.read_text(encoding="utf-8"))
        direct_tools = data["mcpServers"]["deepwork"]["directTools"]
        for tool in ("get_workflows", "start_workflow", "finished_step"):
            assert tool in direct_tools


class TestPiExtension:
    extension_path = PLUGIN_DIR / "extensions" / "index.ts"

    def test_extension_registers_setup_command(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert 'registerCommand("deepwork_setup"' in content
        assert ".mcp.json" in content

    def test_extension_registers_review_commands(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert 'registerCommand("review"' in content
        assert 'registerCommand("deepwork_review"' in content
        assert "runDeepworkReview(pi, ctx.cwd)" in content

    def test_extension_registers_hooks(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert 'pi.on("resources_discover"' in content
        assert 'pi.on("before_agent_start"' in content
        assert 'pi.on("tool_result"' in content
        assert "deepschema_write" in content

    def test_subagents_are_pinged_lazily_for_review_only(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        startup_section = content.split('pi.registerCommand("review"')[0]
        assert "subagents:rpc" not in startup_section
        assert "let subagentsAvailability: Promise<boolean> | null = null" in content
        assert "subagentsAvailability === null" in content
        assert 'requestSubagentRpc<{ version: string }>(pi, "ping", {})' in content
        assert "getSubagentsAvailable(pi)" in content

    def test_review_uses_subagents_rpc_when_available(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert 'requestSubagentRpc<{ id: string }>(pi, "spawn"' in content
        assert 'pi.events.emit(`subagents:rpc:${method}`' in content
        assert "run_in_background: true" in content
        assert "subagentReviewPrompt(task)" in content

    def test_review_has_sequential_fallback(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert "if (!subagentsAvailable)" in content
        assert "sequentialReviewPrompt(tasks)" in content
        assert "Run these DeepWork review tasks sequentially" in content

    def test_review_parses_pi_formatter_output(self) -> None:
        content = self.extension_path.read_text(encoding="utf-8")
        assert "function parseReviewTasks" in content
        assert 'line.startsWith("description: ")' in content
        assert 'startsWith("reviewer: ")' in content
        assert 'startsWith("prompt_file: ")' in content


class TestPiSkills:
    expected_skills = {
        "deepwork",
        "review",
        "configure_reviews",
        "new_user",
        "record",
        "deepschema",
        "deepreviews",
        "deepplan",
    }

    def test_expected_skill_files_exist(self) -> None:
        for skill in self.expected_skills:
            assert (SKILLS_DIR / skill / "SKILL.md").exists()

    def test_skill_names_match_directories(self) -> None:
        for skill in self.expected_skills:
            skill_file = SKILLS_DIR / skill / "SKILL.md"
            fm = _parse_yaml_frontmatter(skill_file)
            assert fm["name"] == skill
            assert fm["description"]

    def test_no_learning_agents_skill_is_packaged(self) -> None:
        assert not (SKILLS_DIR / "learning-agents").exists()
        packaged_text = "\n".join(
            path.read_text(encoding="utf-8") for path in SKILLS_DIR.glob("*/SKILL.md")
        )
        assert "learning-agents" not in packaged_text

    def test_deepwork_skill_references_mcp_workflow_tools(self) -> None:
        content = (SKILLS_DIR / "deepwork" / "SKILL.md").read_text(encoding="utf-8")
        for tool in ("get_workflows", "start_workflow", "finished_step"):
            assert tool in content

    def test_review_skill_uses_pi_review_contract(self) -> None:
        content = (SKILLS_DIR / "review" / "SKILL.md").read_text(encoding="utf-8")
        assert "get_review_instructions" in content
        assert "prompt_file" in content
        assert "Pi's DeepWork extension registers `/review` as a command" in content
