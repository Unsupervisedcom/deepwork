"""Tests for the Claude Code plugin — validates PLUG-REQ-001.

Each test class maps to a numbered requirement section in
specs/deepwork/cli_plugins/PLUG-REQ-001-claude-code-plugin.md.

Requirements that need judgment to evaluate (e.g., "skill MUST instruct the
agent to do X") are validated by review rules in .deepreview, not by tests.
Only deterministic, boolean-verifiable requirements have tests here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "claude"
SKILLS_DIR = PLUGIN_DIR / "skills"
PLATFORM_DIR = PROJECT_ROOT / "platform"


def _parse_yaml_frontmatter(skill_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


# ---------------------------------------------------------------------------
# PLUG-REQ-001.1: Plugin Manifest
# ---------------------------------------------------------------------------


class TestPluginManifest:
    """Tests for the plugin manifest (PLUG-REQ-001.1)."""

    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

    def test_manifest_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.1.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.1.1: manifest exists at plugins/claude/.claude-plugin/plugin.json."""
        assert self.manifest_path.exists()

    def test_manifest_name_is_deepwork(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.1.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.1.2: manifest name field is 'deepwork'."""
        data = json.loads(self.manifest_path.read_text())
        assert data["name"] == "deepwork"

    def test_manifest_required_fields(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.1.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.1.3: manifest includes description, version, author, repository."""
        data = json.loads(self.manifest_path.read_text())
        for field in ("description", "version", "author", "repository"):
            assert field in data, f"manifest is missing required field: {field}"


# ---------------------------------------------------------------------------
# PLUG-REQ-001.2: MCP Server Registration
# ---------------------------------------------------------------------------


class TestMCPServerRegistration:
    """Tests for MCP server registration (PLUG-REQ-001.2)."""

    mcp_json_path = PLUGIN_DIR / ".mcp.json"

    def test_mcp_json_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.2.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.2.1: .mcp.json exists at plugins/claude/.mcp.json."""
        assert self.mcp_json_path.exists()

    def test_mcp_json_registers_deepwork_server(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.2.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.2.1: .mcp.json registers a 'deepwork' MCP server."""
        data = json.loads(self.mcp_json_path.read_text())
        assert "mcpServers" in data
        assert "deepwork" in data["mcpServers"]

    def test_mcp_command_is_uvx_deepwork_serve(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.2.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.2.2: command is uvx with deepwork and serve as first two args."""
        data = json.loads(self.mcp_json_path.read_text())
        server = data["mcpServers"]["deepwork"]
        assert server["command"] == "uvx"
        args = server["args"]
        assert args[0] == "deepwork"
        assert args[1] == "serve"

    def test_mcp_args_include_platform_claude(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.2.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.2.3: arguments include --platform claude."""
        data = json.loads(self.mcp_json_path.read_text())
        args = data["mcpServers"]["deepwork"]["args"]
        assert "--platform" in args
        platform_idx = args.index("--platform")
        assert args[platform_idx + 1] == "claude"

    def test_mcp_args_include_path_dot(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.2.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.2.4: arguments include --path ."""
        data = json.loads(self.mcp_json_path.read_text())
        args = data["mcpServers"]["deepwork"]["args"]
        assert "--path" in args
        path_idx = args.index("--path")
        assert args[path_idx + 1] == "."


# ---------------------------------------------------------------------------
# PLUG-REQ-001.3: Deepwork Skill
#
# 001.3.1-3, 001.3.5: Tested here (deterministic: file exists, name field,
#   specific identifiers present).
# 001.3.4: Validated by review rule (requires judgment about whether the
#   skill instructions adequately support discovery, inference, and prompting).
# ---------------------------------------------------------------------------


class TestDeepworkSkill:
    """Tests for the deepwork skill (PLUG-REQ-001.3)."""

    skill_path = SKILLS_DIR / "deepwork" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.3.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.3.1: deepwork skill exists at expected path."""
        assert self.skill_path.exists()

    def test_skill_invocable_as_deepwork(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.3.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.3.2: skill is invocable as /deepwork."""
        fm = _parse_yaml_frontmatter(self.skill_path)
        assert fm["name"] == "deepwork"

    def test_skill_references_mcp_tools(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.3.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.3.3: skill instructs agent to use MCP tools."""
        content = self.skill_path.read_text(encoding="utf-8")
        for tool in ("get_workflows", "start_workflow", "finished_step"):
            assert tool in content, f"skill must reference MCP tool: {tool}"

    def test_skill_supports_creating_new_jobs(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.3.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.3.5: skill supports creating jobs via deepwork_jobs new_job."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "deepwork_jobs" in content
        assert "new_job" in content


# ---------------------------------------------------------------------------
# PLUG-REQ-001.4: Review Skill
#
# 001.4.1-3, 001.4.6, 001.4.8: Tested here (deterministic: file exists, name
#   field, specific identifiers like mcp__deepwork__*, AskUserQuestion,
#   configure_reviews).
# 001.4.4, 001.4.5, 001.4.7, 001.4.9: Validated by review rule (require
#   judgment about whether instructions adequately convey parallel execution,
#   auto-apply policy, iteration behavior, and no-rules handling).
# ---------------------------------------------------------------------------


class TestReviewSkill:
    """Tests for the review skill (PLUG-REQ-001.4)."""

    skill_path = SKILLS_DIR / "review" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.4.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.4.1: review skill exists at expected path."""
        assert self.skill_path.exists()

    def test_skill_invocable_as_review(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.4.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.4.2: skill is invocable as /review."""
        fm = _parse_yaml_frontmatter(self.skill_path)
        assert fm["name"] == "review"

    def test_skill_uses_mcp_review_tools(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.4.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.4.3: skill uses MCP review tools, not CLI commands."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "mcp__deepwork__get_review_instructions" in content

    def test_skill_instructs_present_tradeoffs(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.4.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.4.6: skill instructs agent to present trade-off findings to user."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "AskUserQuestion" in content

    def test_skill_redirects_config_to_configure_reviews(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.4.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.4.8: skill redirects configuration to configure_reviews."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "configure_reviews" in content


# ---------------------------------------------------------------------------
# PLUG-REQ-001.5: Configure Reviews Skill
#
# 001.5.1-3, 001.5.5: Tested here (deterministic: file exists, name field,
#   specific identifiers README_REVIEWS.md, mcp__deepwork__*).
# 001.5.4: Validated by review rule (requires judgment about whether
#   instructions adequately convey reuse of existing rules).
# ---------------------------------------------------------------------------


class TestConfigureReviewsSkill:
    """Tests for the configure_reviews skill (PLUG-REQ-001.5)."""

    skill_path = SKILLS_DIR / "configure_reviews" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.5.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.5.1: configure_reviews skill exists at expected path."""
        assert self.skill_path.exists()

    def test_skill_invocable_as_configure_reviews(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.5.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.5.2: skill is invocable as /configure_reviews."""
        fm = _parse_yaml_frontmatter(self.skill_path)
        assert fm["name"] == "configure_reviews"

    def test_skill_consults_readme(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.5.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.5.3: skill tells agent to consult README_REVIEWS.md."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "README_REVIEWS.md" in content

    def test_skill_instructs_test_new_rules(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.5.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.5.5: skill tells agent to test by triggering a review run."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "mcp__deepwork__get_review_instructions" in content


# ---------------------------------------------------------------------------
# PLUG-REQ-001.6: Review Reference Documentation
# ---------------------------------------------------------------------------


class TestReviewReferenceDocumentation:
    """Tests for README_REVIEWS.md in the plugin (PLUG-REQ-001.6)."""

    symlink_path = PLUGIN_DIR / "README_REVIEWS.md"

    def test_readme_reviews_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.6.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.6.1: README_REVIEWS.md exists at plugins/claude/."""
        assert self.symlink_path.exists()

    def test_readme_reviews_is_symlink(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.6.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.6.2: README_REVIEWS.md is a symlink."""
        assert self.symlink_path.is_symlink()

    def test_symlink_target(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.6.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.6.2: symlink points to ../../README_REVIEWS.md."""
        target = self.symlink_path.readlink()
        assert str(target) == "../../README_REVIEWS.md"


# ---------------------------------------------------------------------------
# PLUG-REQ-001.7: Post-Commit Review Reminder
# ---------------------------------------------------------------------------


class TestPostCommitReviewReminder:
    """Tests for the post-commit hook (PLUG-REQ-001.7)."""

    hooks_json_path = PLUGIN_DIR / "hooks" / "hooks.json"

    def test_hooks_json_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.7.1: hooks.json exists in plugin hooks directory."""
        assert self.hooks_json_path.exists()

    def test_registers_post_tool_use_on_bash(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.7.1: hooks.json registers PostToolUse hook on Bash tool."""
        data = json.loads(self.hooks_json_path.read_text())
        assert "hooks" in data
        assert "PostToolUse" in data["hooks"]
        hooks = data["hooks"]["PostToolUse"]
        bash_matchers = [h for h in hooks if h.get("matcher") == "Bash"]
        assert len(bash_matchers) >= 1, "No PostToolUse hook with Bash matcher found"

    def test_hook_script_detects_git_commit(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.7.2: hook script detects git commit and prompts review."""
        data = json.loads(self.hooks_json_path.read_text())
        hooks = data["hooks"]["PostToolUse"]
        bash_hook = next(h for h in hooks if h.get("matcher") == "Bash")

        # Get the hook command path
        hook_commands = bash_hook.get("hooks", [])
        assert len(hook_commands) >= 1

        # Read the actual hook script
        command = hook_commands[0]["command"]
        # The command uses ${CLAUDE_PLUGIN_ROOT} — resolve relative to plugin dir
        script_name = command.split("/")[-1]
        script_path = PLUGIN_DIR / "hooks" / script_name
        assert script_path.exists(), f"Hook script not found: {script_path}"

        content = script_path.read_text(encoding="utf-8")
        assert "git commit" in content, "Hook script must detect git commit commands"
        assert "review" in content.lower(), "Hook script must prompt for review"


# ---------------------------------------------------------------------------
# PLUG-REQ-001.8: Skill Directory Conventions
# ---------------------------------------------------------------------------


class TestSkillDirectoryConventions:
    """Tests for skill directory structure (PLUG-REQ-001.8)."""

    def test_each_skill_in_own_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.8.1: each skill resides in its own directory."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 3  # deepwork, review, configure_reviews

    def test_each_skill_has_skill_md(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.8.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.8.2: each skill directory contains a SKILL.md file."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            assert (skill_dir / "SKILL.md").exists(), f"{skill_dir.name} is missing SKILL.md"

    def test_name_matches_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.8.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.8.3: frontmatter name matches directory name."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                fm = _parse_yaml_frontmatter(skill_file)
                assert fm["name"] == skill_dir.name, (
                    f"Skill {skill_dir.name} has name={fm['name']} in frontmatter"
                )

    def test_each_skill_has_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.8.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.8.4: each skill's frontmatter includes a description."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                fm = _parse_yaml_frontmatter(skill_file)
                assert "description" in fm, f"Skill {skill_dir.name} is missing description"
                assert len(fm["description"]) > 0, f"Skill {skill_dir.name} has empty description"


# ---------------------------------------------------------------------------
# PLUG-REQ-001.9: Shared Skill Content
# ---------------------------------------------------------------------------


class TestSharedSkillContent:
    """Tests for shared skill content sync (PLUG-REQ-001.9)."""

    claude_skill = SKILLS_DIR / "deepwork" / "SKILL.md"
    gemini_skill = PROJECT_ROOT / "plugins" / "gemini" / "skills" / "deepwork" / "SKILL.md"
    platform_body = PLATFORM_DIR / "skill-body.md"

    def test_claude_skill_body_matches_platform(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.9.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.9.1: Claude deepwork skill body is in sync with platform/skill-body.md."""
        platform_content = self.platform_body.read_text(encoding="utf-8").strip()
        claude_content = self.claude_skill.read_text(encoding="utf-8")

        # Strip YAML frontmatter from Claude skill to get the body
        assert claude_content.startswith("---")
        end = claude_content.index("---", 3)
        claude_body = claude_content[end + 3 :].strip()

        assert claude_body == platform_content, (
            "Claude skill body has diverged from platform/skill-body.md"
        )

    def test_gemini_skill_body_matches_platform(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.9.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.9.2: Gemini deepwork skill body is in sync with platform/skill-body.md."""
        platform_content = self.platform_body.read_text(encoding="utf-8").strip()
        gemini_content = self.gemini_skill.read_text(encoding="utf-8")

        # Strip TOML frontmatter from Gemini skill to get the body
        assert gemini_content.startswith("+++")
        end = gemini_content.index("+++", 3)
        gemini_body = gemini_content[end + 3 :].strip()

        assert gemini_body == platform_content, (
            "Gemini skill body has diverged from platform/skill-body.md"
        )


# ---------------------------------------------------------------------------
# PLUG-REQ-001.10: MCP configures Claude Code
# ---------------------------------------------------------------------------


class TestMCPConfiguresClaude:
    """Tests for MCP auto-approval configuration (PLUG-REQ-001.10)."""

    plugin_json_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    mcp_json_path = PLUGIN_DIR / ".mcp.json"

    @pytest.mark.xfail(reason="PLUG-REQ-001.10 not yet implemented — needs auto-approval config")
    def test_plugin_configures_mcp_tool_auto_approval(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.10.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PLUG-REQ-001.10.1: plugin configures Claude Code to allow MCP tools without prompts."""
        # The plugin must include a mechanism that auto-approves its MCP tool
        # calls. This could be via allowedTools in plugin settings, a
        # settings.json in the plugin directory, or plugin.json metadata.
        plugin_data = json.loads(self.plugin_json_path.read_text())
        has_settings = "settings" in plugin_data or "allowedTools" in plugin_data

        settings_path = PLUGIN_DIR / ".claude-plugin" / "settings.json"
        has_settings_file = settings_path.exists()

        assert has_settings or has_settings_file, (
            "Plugin must include auto-approval configuration for MCP tools. "
            "Expected either 'settings' or 'allowedTools' in plugin.json, "
            "or a separate settings.json in the .claude-plugin directory."
        )


# ---------------------------------------------------------------------------
# PLUG-REQ-001.11: Post-Compaction Context Restoration
# ---------------------------------------------------------------------------


class TestPostCompactionHook:
    """Tests for the post-compaction context restoration hook (PLUG-REQ-001.11)."""

    hooks_json_path = PLUGIN_DIR / "hooks" / "hooks.json"
    hook_script_path = PLUGIN_DIR / "hooks" / "post_compact.sh"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hooks_json_registers_session_start_compact(self) -> None:
        """PLUG-REQ-001.11.1: hooks.json registers SessionStart hook with matcher 'compact'."""
        data = json.loads(self.hooks_json_path.read_text())
        session_start = data["hooks"]["SessionStart"]
        assert any(entry.get("matcher") == "compact" for entry in session_start), (
            "hooks.json must have a SessionStart entry with matcher 'compact'"
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hooks_json_compact_points_to_post_compact_sh(self) -> None:
        """PLUG-REQ-001.11.1: compact matcher hook points to post_compact.sh."""
        data = json.loads(self.hooks_json_path.read_text())
        session_start = data["hooks"]["SessionStart"]
        compact_entry = next(e for e in session_start if e.get("matcher") == "compact")
        commands = [h["command"] for h in compact_entry["hooks"]]
        assert any("post_compact.sh" in cmd for cmd in commands)

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hook_script_calls_get_stack(self) -> None:
        """PLUG-REQ-001.11.2: hook script calls 'deepwork jobs get-stack'."""
        content = self.hook_script_path.read_text()
        assert "deepwork jobs get-stack" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hook_script_outputs_additional_context(self) -> None:
        """PLUG-REQ-001.11.3: hook script outputs hookSpecificOutput with additionalContext."""
        content = self.hook_script_path.read_text()
        assert "additionalContext" in content
        assert "hookSpecificOutput" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hook_script_outputs_empty_json_on_failure(self) -> None:
        """PLUG-REQ-001.11.4: hook script outputs empty {} on failure."""
        content = self.hook_script_path.read_text()
        # Script must have fallback patterns that output {}
        assert content.count("echo '{}'") >= 1, "Script must output '{}' on failure paths"
        assert "trap" in content, "Script must have an ERR trap for graceful degradation"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.11.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hook_script_always_exits_zero(self) -> None:
        """PLUG-REQ-001.11.5: hook script never produces non-zero exit codes."""
        content = self.hook_script_path.read_text()
        # ERR trap must exit 0
        assert "exit 0" in content
        assert "trap" in content
