"""Tests for the learning-agents plugin.

Validates requirements: LA-REQ-001, LA-REQ-001.1, LA-REQ-001.2, LA-REQ-001.3,
LA-REQ-001.4, LA-REQ-001.5, LA-REQ-001.6, LA-REQ-001.7, LA-REQ-001.8.

Each test class maps to a numbered requirement section in
specs/learning-agents/LA-REQ-001-plugin-structure.md.

Only deterministic, boolean-verifiable requirements have tests here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "learning_agents"
MARKETPLACE_PATH = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"


# ---------------------------------------------------------------------------
# LA-REQ-001.1: Plugin Manifest
# ---------------------------------------------------------------------------


class TestPluginManifest:
    """Tests for the plugin manifest (LA-REQ-001.1)."""

    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

    def test_manifest_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: manifest exists at learning_agents/.claude-plugin/plugin.json."""
        assert self.manifest_path.exists()

    def test_manifest_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: name is 'learning-agents'."""
        data = json.loads(self.manifest_path.read_text())
        assert data["name"] == "learning-agents"

    def test_manifest_description_non_empty(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: description is a non-empty string."""
        data = json.loads(self.manifest_path.read_text())
        assert isinstance(data["description"], str)
        assert len(data["description"]) > 0

    def test_manifest_version_semver(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: version is in semver format."""
        data = json.loads(self.manifest_path.read_text())
        assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"]), (
            f"version '{data['version']}' is not semver"
        )

    def test_manifest_author_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: author.name is a non-empty string."""
        data = json.loads(self.manifest_path.read_text())
        assert isinstance(data["author"]["name"], str)
        assert len(data["author"]["name"]) > 0

    def test_manifest_repository_url(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.1).
        """LA-REQ-001.1: repository is a valid URL string."""
        data = json.loads(self.manifest_path.read_text())
        assert isinstance(data["repository"], str)
        assert data["repository"].startswith("https://")


# ---------------------------------------------------------------------------
# LA-REQ-001.2: Marketplace Registration
# ---------------------------------------------------------------------------


class TestMarketplaceRegistration:
    """Tests for marketplace registration (LA-REQ-001.2)."""

    def _get_learning_agents_entry(self) -> dict[str, Any]:
        data = json.loads(MARKETPLACE_PATH.read_text())
        for plugin in data["plugins"]:
            if plugin["name"] == "learning-agents":
                return dict(plugin)
        raise AssertionError("No plugin with name 'learning-agents' found in marketplace.json")

    def test_marketplace_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.2).
        """LA-REQ-001.2: marketplace.json exists."""
        assert MARKETPLACE_PATH.exists()

    def test_marketplace_name_matches_manifest(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.2).
        """LA-REQ-001.2: marketplace name matches plugin manifest name."""
        entry = self._get_learning_agents_entry()
        assert entry["name"] == "learning-agents"

    def test_marketplace_source(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.2).
        """LA-REQ-001.2: source points to plugin root directory."""
        entry = self._get_learning_agents_entry()
        assert entry["source"] == "./learning_agents"

    def test_marketplace_category(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.2).
        """LA-REQ-001.2: category is 'learning'."""
        entry = self._get_learning_agents_entry()
        assert entry["category"] == "learning"


# ---------------------------------------------------------------------------
# LA-REQ-001.3: Plugin Root Directory Layout
# ---------------------------------------------------------------------------


class TestPluginDirectoryLayout:
    """Tests for plugin root directory layout (LA-REQ-001.3)."""

    REQUIRED_SUBDIRS = [
        ".claude-plugin",
        "agents",
        "doc",
        "hooks",
        "scripts",
        "skills",
    ]

    def test_required_subdirectories_exist(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.3).
        """LA-REQ-001.3: all required subdirectories exist."""
        for subdir in self.REQUIRED_SUBDIRS:
            path = PLUGIN_DIR / subdir
            assert path.is_dir(), f"Required subdirectory '{subdir}' missing"


# ---------------------------------------------------------------------------
# LA-REQ-001.4: Hooks Configuration
# ---------------------------------------------------------------------------


class TestHooksConfiguration:
    """Tests for hooks configuration (LA-REQ-001.4)."""

    hooks_path = PLUGIN_DIR / "hooks" / "hooks.json"

    def _load_hooks(self) -> dict:
        return dict(json.loads(self.hooks_path.read_text()))

    def test_hooks_json_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.4).
        """LA-REQ-001.4: hooks/hooks.json exists."""
        assert self.hooks_path.exists()

    def test_post_tool_use_hook(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.4).
        """LA-REQ-001.4: PostToolUse hook with matcher 'Task' executing post_task.sh."""
        data = self._load_hooks()
        post_tool_use = data["hooks"]["PostToolUse"]
        assert len(post_tool_use) >= 1
        task_hook = next((h for h in post_tool_use if h["matcher"] == "Task"), None)
        assert task_hook is not None, "No PostToolUse hook with matcher 'Task'"
        cmd = task_hook["hooks"][0]["command"]
        assert cmd.endswith("post_task.sh")

    def test_stop_hook(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.4).
        """LA-REQ-001.4: Stop hook with empty matcher executing session_stop.sh."""
        data = self._load_hooks()
        stop_hooks = data["hooks"]["Stop"]
        assert len(stop_hooks) >= 1
        stop_hook = next((h for h in stop_hooks if h["matcher"] == ""), None)
        assert stop_hook is not None, "No Stop hook with empty matcher"
        cmd = stop_hook["hooks"][0]["command"]
        assert cmd.endswith("session_stop.sh")


# ---------------------------------------------------------------------------
# LA-REQ-001.5: Hook Script References
# ---------------------------------------------------------------------------


class TestHookScriptReferences:
    """Tests for hook script path references (LA-REQ-001.5)."""

    hooks_path = PLUGIN_DIR / "hooks" / "hooks.json"

    def test_commands_use_plugin_root_prefix(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.5).
        """LA-REQ-001.5: all hook commands use ${CLAUDE_PLUGIN_ROOT} prefix."""
        data = json.loads(self.hooks_path.read_text())
        for event_name, entries in data["hooks"].items():
            for entry in entries:
                for hook in entry["hooks"]:
                    cmd = hook["command"]
                    assert cmd.startswith("${CLAUDE_PLUGIN_ROOT}"), (
                        f"Hook command in {event_name} does not use "
                        f"${{CLAUDE_PLUGIN_ROOT}} prefix: {cmd}"
                    )


# ---------------------------------------------------------------------------
# LA-REQ-001.6: Hook Scripts Exit Code
# ---------------------------------------------------------------------------


class TestHookScriptsExitCode:
    """Tests for hook script exit codes (LA-REQ-001.6)."""

    HOOK_SCRIPTS = [
        PLUGIN_DIR / "hooks" / "post_task.sh",
        PLUGIN_DIR / "hooks" / "session_stop.sh",
    ]

    def test_hook_scripts_exist(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.6).
        """LA-REQ-001.6: all hook scripts exist."""
        for script in self.HOOK_SCRIPTS:
            assert script.exists(), f"Hook script missing: {script.name}"

    def test_hook_scripts_end_with_exit_zero(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.6).
        """LA-REQ-001.6: all hook scripts end with 'exit 0'."""
        for script in self.HOOK_SCRIPTS:
            content = script.read_text()
            # Strip trailing whitespace/newlines and check last non-empty line
            lines = [ln.strip() for ln in content.strip().splitlines() if ln.strip()]
            assert lines[-1] == "exit 0", (
                f"{script.name} does not end with 'exit 0' (last line: '{lines[-1]}')"
            )


# ---------------------------------------------------------------------------
# LA-REQ-001.7: Hook Scripts Output Format
# ---------------------------------------------------------------------------


class TestHookScriptsOutputFormat:
    """Tests for hook script JSON output format (LA-REQ-001.7)."""

    HOOK_SCRIPTS = [
        PLUGIN_DIR / "hooks" / "post_task.sh",
        PLUGIN_DIR / "hooks" / "session_stop.sh",
    ]

    def test_hook_scripts_output_empty_json_on_noop(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.7).
        """LA-REQ-001.7: scripts output '{}' when there is nothing to communicate."""
        for script in self.HOOK_SCRIPTS:
            content = script.read_text()
            assert "echo '{}'" in content or 'echo "{}"' in content, (
                f"{script.name} does not output '{{}}' for no-op cases"
            )

    def test_hook_scripts_output_system_message_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.7).
        """LA-REQ-001.7: when communicating, scripts output JSON with systemMessage or hookSpecificOutput."""
        for script in self.HOOK_SCRIPTS:
            content = script.read_text()
            # Each script should have at least one structured JSON output path
            has_structured = "systemMessage" in content or "hookSpecificOutput" in content
            has_noop = "echo '{}'" in content or 'echo "{}"' in content
            # Scripts must have both a structured output and a no-op path
            assert has_noop, f"{script.name} missing no-op JSON output"
            assert has_structured, f"{script.name} missing structured JSON output"


# ---------------------------------------------------------------------------
# LA-REQ-001.8: Meta-Agent Definition
# ---------------------------------------------------------------------------


class TestMetaAgentDefinition:
    """Tests for the meta-agent definition (LA-REQ-001.8)."""

    agent_path = PLUGIN_DIR / "agents" / "learning-agent-expert.md"

    def test_meta_agent_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.8).
        """LA-REQ-001.8: agents/learning-agent-expert.md exists."""
        assert self.agent_path.exists()

    def test_meta_agent_has_dynamic_context_injection(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.8).
        """LA-REQ-001.8: agent uses !`...` syntax to load doc/ files."""
        content = self.agent_path.read_text()
        # Must have at least one !`cat ${CLAUDE_PLUGIN_ROOT}/doc/...` command
        pattern = r"!\`cat \$\{CLAUDE_PLUGIN_ROOT\}/doc/"
        matches = re.findall(pattern, content)
        assert len(matches) > 0, (
            "Meta-agent must include dynamic context injection "
            "commands loading from ${CLAUDE_PLUGIN_ROOT}/doc/"
        )

    def test_meta_agent_loads_all_doc_files(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-001.8).
        """LA-REQ-001.8: agent loads all reference documentation from doc/."""
        content = self.agent_path.read_text()
        doc_dir = PLUGIN_DIR / "doc"
        md_files = sorted(doc_dir.glob("*.md"))
        assert len(md_files) > 0, "No .md files found in doc/"
        for md_file in md_files:
            expected_ref = f"${{CLAUDE_PLUGIN_ROOT}}/doc/{md_file.name}"
            assert expected_ref in content, f"Meta-agent does not load doc file: {md_file.name}"
