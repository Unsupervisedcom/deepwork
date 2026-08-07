"""Tests for the OpenClaw bundle scaffold."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "openclaw"
SKILLS_DIR = PLUGIN_DIR / "skills"
HOOKS_DIR = PLUGIN_DIR / "hooks"


def _parse_yaml_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


class TestPluginManifest:
    manifest_path = PLUGIN_DIR / ".codex-plugin" / "plugin.json"

    def test_manifest_exists(self) -> None:
        assert self.manifest_path.exists()

    def test_manifest_declares_skills_and_hooks(self) -> None:
        data = json.loads(self.manifest_path.read_text())
        assert data["name"] == "deepwork"
        assert data["skills"] == ["skills"]
        assert data["hooks"] == ["hooks"]


class TestMcpRegistration:
    mcp_json_path = PLUGIN_DIR / ".mcp.json"

    def test_mcp_json_exists(self) -> None:
        assert self.mcp_json_path.exists()

    def test_mcp_json_uses_openclaw_platform(self) -> None:
        data = json.loads(self.mcp_json_path.read_text())
        server = data["mcpServers"]["deepwork"]
        assert server["command"] == "uvx"
        assert server["args"] == ["deepwork", "serve", "--platform", "openclaw"]


class TestDeepworkSkill:
    skill_path = SKILLS_DIR / "deepwork" / "SKILL.md"

    def test_skill_exists(self) -> None:
        assert self.skill_path.exists()

    def test_skill_frontmatter(self) -> None:
        frontmatter = _parse_yaml_frontmatter(self.skill_path)
        assert frontmatter["name"] == "deepwork"

    def test_skill_mentions_resume_and_mcp_tools(self) -> None:
        content = self.skill_path.read_text(encoding="utf-8")
        for token in (
            "deepwork__get_workflows",
            "deepwork__get_active_workflow",
            "deepwork__start_workflow",
            "deepwork__validate_step_outputs",
            "deepwork__finished_step",
        ):
            assert token in content


class TestReviewSkill:
    skill_path = SKILLS_DIR / "review" / "SKILL.md"

    def test_skill_exists(self) -> None:
        assert self.skill_path.exists()

    def test_skill_mentions_openclaw_review_flow(self) -> None:
        content = self.skill_path.read_text(encoding="utf-8")
        assert "deepwork__get_review_instructions" in content
        assert "sessions_spawn" in content
        assert "timeoutSeconds" in content


class TestBootstrapHook:
    hook_dir = HOOKS_DIR / "deepwork-openclaw-bootstrap"

    def test_hook_files_exist(self) -> None:
        assert (self.hook_dir / "HOOK.md").exists()
        assert (self.hook_dir / "handler.ts").exists()

    def test_hook_is_registered_for_agent_bootstrap(self) -> None:
        content = (self.hook_dir / "HOOK.md").read_text(encoding="utf-8")
        assert "agent:bootstrap" in content
        assert "DeepWork session" in content
