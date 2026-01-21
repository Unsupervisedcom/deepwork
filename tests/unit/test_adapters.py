"""Tests for agent adapters."""

import json
from pathlib import Path
from typing import Any

import pytest

from deepwork.core.adapters import (
    AdapterError,
    AgentAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    SkillLifecycleHook,
)


class TestAgentAdapterRegistry:
    """Tests for AgentAdapter registry functionality."""

    def test_get_all_returns_registered_adapters(self) -> None:
        """Test that get_all returns all registered adapters."""
        adapters = AgentAdapter.get_all()

        assert "claude" in adapters
        assert adapters["claude"] is ClaudeAdapter
        assert "gemini" in adapters
        assert adapters["gemini"] is GeminiAdapter

    def test_get_returns_correct_adapter(self) -> None:
        """Test that get returns the correct adapter class."""
        assert AgentAdapter.get("claude") is ClaudeAdapter
        assert AgentAdapter.get("gemini") is GeminiAdapter

    def test_get_raises_for_unknown_adapter(self) -> None:
        """Test that get raises AdapterError for unknown adapter."""
        with pytest.raises(AdapterError, match="Unknown adapter 'unknown'"):
            AgentAdapter.get("unknown")

    def test_list_names_returns_all_names(self) -> None:
        """Test that list_names returns all registered adapter names."""
        names = AgentAdapter.list_names()

        assert "claude" in names
        assert "gemini" in names
        assert len(names) >= 2  # At least claude and gemini


class TestClaudeAdapter:
    """Tests for ClaudeAdapter."""

    def test_class_attributes(self) -> None:
        """Test Claude adapter class attributes."""
        assert ClaudeAdapter.name == "claude"
        assert ClaudeAdapter.display_name == "Claude Code"
        assert ClaudeAdapter.config_dir == ".claude"
        assert ClaudeAdapter.skills_dir == "skills"

    def test_init_with_project_root(self, temp_dir: Path) -> None:
        """Test initialization with project root."""
        adapter = ClaudeAdapter(temp_dir)

        assert adapter.project_root == temp_dir

    def test_init_without_project_root(self) -> None:
        """Test initialization without project root."""
        adapter = ClaudeAdapter()

        assert adapter.project_root is None

    def test_detect_when_present(self, temp_dir: Path) -> None:
        """Test detect when .claude directory exists."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        assert adapter.detect() is True

    def test_detect_when_absent(self, temp_dir: Path) -> None:
        """Test detect when .claude directory doesn't exist."""
        adapter = ClaudeAdapter(temp_dir)

        assert adapter.detect() is False

    def test_detect_with_explicit_project_root(self, temp_dir: Path) -> None:
        """Test detect with explicit project root parameter."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter()

        assert adapter.detect(temp_dir) is True

    def test_get_template_dir(self, temp_dir: Path) -> None:
        """Test get_template_dir."""
        adapter = ClaudeAdapter()
        templates_root = temp_dir / "templates"

        result = adapter.get_template_dir(templates_root)

        assert result == templates_root / "claude"

    def test_get_skills_dir(self, temp_dir: Path) -> None:
        """Test get_skills_dir."""
        adapter = ClaudeAdapter(temp_dir)

        result = adapter.get_skills_dir()

        assert result == temp_dir / ".claude" / "skills"

    def test_get_skills_dir_with_explicit_root(self, temp_dir: Path) -> None:
        """Test get_skills_dir with explicit project root."""
        adapter = ClaudeAdapter()

        result = adapter.get_skills_dir(temp_dir)

        assert result == temp_dir / ".claude" / "skills"

    def test_get_skills_dir_raises_without_root(self) -> None:
        """Test get_skills_dir raises when no project root specified."""
        adapter = ClaudeAdapter()

        with pytest.raises(AdapterError, match="No project root specified"):
            adapter.get_skills_dir()

    def test_get_meta_skill_filename(self) -> None:
        """Test get_meta_skill_filename returns directory/SKILL.md format."""
        adapter = ClaudeAdapter()

        result = adapter.get_meta_skill_filename("my_job")

        assert result == "my_job/SKILL.md"

    def test_get_step_skill_filename_returns_directory_format(self) -> None:
        """Test get_step_skill_filename returns directory/SKILL.md format."""
        adapter = ClaudeAdapter()

        result = adapter.get_step_skill_filename("my_job", "step_one")

        assert result == "my_job.step_one/SKILL.md"

    def test_get_step_skill_filename_exposed(self) -> None:
        """Test get_step_skill_filename with exposed=True (same format)."""
        adapter = ClaudeAdapter()

        result = adapter.get_step_skill_filename("my_job", "step_one", exposed=True)

        assert result == "my_job.step_one/SKILL.md"

    def test_sync_hooks_creates_settings_file(self, temp_dir: Path) -> None:
        """Test sync_hooks creates settings.json when it doesn't exist."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)
        hooks = {
            "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "test.sh"}]}]
        }

        count = adapter.sync_hooks(temp_dir, hooks)

        assert count == 1
        settings_file = temp_dir / ".claude" / "settings.json"
        assert settings_file.exists()
        settings = json.loads(settings_file.read_text())
        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]

    def test_sync_hooks_merges_with_existing(self, temp_dir: Path) -> None:
        """Test sync_hooks merges with existing settings."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(json.dumps({"existing_key": "value", "hooks": {}}))

        adapter = ClaudeAdapter(temp_dir)
        hooks = {
            "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "test.sh"}]}]
        }

        adapter.sync_hooks(temp_dir, hooks)

        settings = json.loads(settings_file.read_text())
        assert settings["existing_key"] == "value"
        assert "PreToolUse" in settings["hooks"]

    def test_sync_hooks_empty_hooks_returns_zero(self, temp_dir: Path) -> None:
        """Test sync_hooks returns 0 for empty hooks."""
        adapter = ClaudeAdapter(temp_dir)

        count = adapter.sync_hooks(temp_dir, {})

        assert count == 0

    def test_sync_permissions_creates_settings_file(self, temp_dir: Path) -> None:
        """Test sync_permissions creates settings.json when it doesn't exist."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        count = adapter.sync_permissions(temp_dir)

        assert count == 3  # Read, Edit, Write for .deepwork/tmp/**
        settings_file = temp_dir / ".claude" / "settings.json"
        assert settings_file.exists()
        settings = json.loads(settings_file.read_text())
        assert "permissions" in settings
        assert "allow" in settings["permissions"]
        assert "Read(./.deepwork/tmp/**)" in settings["permissions"]["allow"]
        assert "Edit(./.deepwork/tmp/**)" in settings["permissions"]["allow"]
        assert "Write(./.deepwork/tmp/**)" in settings["permissions"]["allow"]

    def test_sync_permissions_merges_with_existing(self, temp_dir: Path) -> None:
        """Test sync_permissions merges with existing settings."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(
            json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}})
        )

        adapter = ClaudeAdapter(temp_dir)
        adapter.sync_permissions(temp_dir)

        settings = json.loads(settings_file.read_text())
        assert "Bash(ls:*)" in settings["permissions"]["allow"]
        assert "Read(./.deepwork/tmp/**)" in settings["permissions"]["allow"]

    def test_sync_permissions_idempotent(self, temp_dir: Path) -> None:
        """Test sync_permissions is idempotent (doesn't duplicate permissions)."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        # First call adds permissions
        count1 = adapter.sync_permissions(temp_dir)
        assert count1 == 3

        # Second call should add nothing
        count2 = adapter.sync_permissions(temp_dir)
        assert count2 == 0

        # Verify no duplicates
        settings_file = temp_dir / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text())
        allow_list = settings["permissions"]["allow"]
        assert allow_list.count("Read(./.deepwork/tmp/**)") == 1
        assert allow_list.count("Edit(./.deepwork/tmp/**)") == 1
        assert allow_list.count("Write(./.deepwork/tmp/**)") == 1

    def test_add_permission_single(self, temp_dir: Path) -> None:
        """Test add_permission adds a single permission."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        result = adapter.add_permission(temp_dir, "Bash(custom:*)")

        assert result is True
        settings_file = temp_dir / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text())
        assert "Bash(custom:*)" in settings["permissions"]["allow"]

    def test_add_permission_idempotent(self, temp_dir: Path) -> None:
        """Test add_permission doesn't duplicate existing permissions."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        # First call adds
        result1 = adapter.add_permission(temp_dir, "Bash(custom:*)")
        assert result1 is True

        # Second call should return False
        result2 = adapter.add_permission(temp_dir, "Bash(custom:*)")
        assert result2 is False

        # Verify no duplicates
        settings_file = temp_dir / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text())
        assert settings["permissions"]["allow"].count("Bash(custom:*)") == 1

    def test_add_permission_with_settings_dict(self, temp_dir: Path) -> None:
        """Test add_permission with pre-loaded settings (doesn't save)."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)
        settings: dict[str, Any] = {"permissions": {"allow": []}}

        result = adapter.add_permission(temp_dir, "Bash(test:*)", settings)

        assert result is True
        assert "Bash(test:*)" in settings["permissions"]["allow"]
        # File should not exist since we passed settings dict
        settings_file = temp_dir / ".claude" / "settings.json"
        assert not settings_file.exists()

    def test_extract_skill_name_from_path(self, temp_dir: Path) -> None:
        """Test _extract_skill_name extracts skill name from skill path."""
        adapter = ClaudeAdapter(temp_dir)

        # Test meta-skill path
        path1 = temp_dir / ".claude" / "skills" / "my_job" / "SKILL.md"
        assert adapter._extract_skill_name(path1) == "my_job"

        # Test step skill path
        path2 = temp_dir / ".claude" / "skills" / "my_job.step_one" / "SKILL.md"
        assert adapter._extract_skill_name(path2) == "my_job.step_one"

    def test_extract_skill_name_returns_none_for_invalid_path(self, temp_dir: Path) -> None:
        """Test _extract_skill_name returns None for paths without skills dir."""
        adapter = ClaudeAdapter(temp_dir)

        path = temp_dir / ".claude" / "commands" / "my_command.md"
        assert adapter._extract_skill_name(path) is None

    def test_add_skill_permissions(self, temp_dir: Path) -> None:
        """Test add_skill_permissions adds Skill permissions for each skill."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        skill_paths = [
            temp_dir / ".claude" / "skills" / "job_a" / "SKILL.md",
            temp_dir / ".claude" / "skills" / "job_a.step_one" / "SKILL.md",
            temp_dir / ".claude" / "skills" / "job_b" / "SKILL.md",
        ]

        count = adapter.add_skill_permissions(temp_dir, skill_paths)

        assert count == 3
        settings_file = temp_dir / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text())
        assert "Skill(job_a)" in settings["permissions"]["allow"]
        assert "Skill(job_a.step_one)" in settings["permissions"]["allow"]
        assert "Skill(job_b)" in settings["permissions"]["allow"]

    def test_add_skill_permissions_idempotent(self, temp_dir: Path) -> None:
        """Test add_skill_permissions doesn't duplicate permissions."""
        (temp_dir / ".claude").mkdir()
        adapter = ClaudeAdapter(temp_dir)

        skill_paths = [temp_dir / ".claude" / "skills" / "my_job" / "SKILL.md"]

        # First call adds
        count1 = adapter.add_skill_permissions(temp_dir, skill_paths)
        assert count1 == 1

        # Second call should add nothing
        count2 = adapter.add_skill_permissions(temp_dir, skill_paths)
        assert count2 == 0

    def test_add_skill_permissions_empty_list(self, temp_dir: Path) -> None:
        """Test add_skill_permissions with empty list returns 0."""
        adapter = ClaudeAdapter(temp_dir)

        count = adapter.add_skill_permissions(temp_dir, [])

        assert count == 0


class TestGeminiAdapter:
    """Tests for GeminiAdapter."""

    def test_class_attributes(self) -> None:
        """Test Gemini adapter class attributes."""
        assert GeminiAdapter.name == "gemini"
        assert GeminiAdapter.display_name == "Gemini CLI"
        assert GeminiAdapter.config_dir == ".gemini"
        assert GeminiAdapter.skills_dir == "skills"
        assert GeminiAdapter.skill_template == "skill-job-step.toml.jinja"

    def test_init_with_project_root(self, temp_dir: Path) -> None:
        """Test initialization with project root."""
        adapter = GeminiAdapter(temp_dir)

        assert adapter.project_root == temp_dir

    def test_init_without_project_root(self) -> None:
        """Test initialization without project root."""
        adapter = GeminiAdapter()

        assert adapter.project_root is None

    def test_detect_when_present(self, temp_dir: Path) -> None:
        """Test detect when .gemini directory exists."""
        (temp_dir / ".gemini").mkdir()
        adapter = GeminiAdapter(temp_dir)

        assert adapter.detect() is True

    def test_detect_when_absent(self, temp_dir: Path) -> None:
        """Test detect when .gemini directory doesn't exist."""
        adapter = GeminiAdapter(temp_dir)

        assert adapter.detect() is False

    def test_detect_with_explicit_project_root(self, temp_dir: Path) -> None:
        """Test detect with explicit project root parameter."""
        (temp_dir / ".gemini").mkdir()
        adapter = GeminiAdapter()

        assert adapter.detect(temp_dir) is True

    def test_get_template_dir(self, temp_dir: Path) -> None:
        """Test get_template_dir."""
        adapter = GeminiAdapter()
        templates_root = temp_dir / "templates"

        result = adapter.get_template_dir(templates_root)

        assert result == templates_root / "gemini"

    def test_get_skills_dir(self, temp_dir: Path) -> None:
        """Test get_skills_dir."""
        adapter = GeminiAdapter(temp_dir)

        result = adapter.get_skills_dir()

        assert result == temp_dir / ".gemini" / "skills"

    def test_get_skills_dir_with_explicit_root(self, temp_dir: Path) -> None:
        """Test get_skills_dir with explicit project root."""
        adapter = GeminiAdapter()

        result = adapter.get_skills_dir(temp_dir)

        assert result == temp_dir / ".gemini" / "skills"

    def test_get_skills_dir_raises_without_root(self) -> None:
        """Test get_skills_dir raises when no project root specified."""
        adapter = GeminiAdapter()

        with pytest.raises(AdapterError, match="No project root specified"):
            adapter.get_skills_dir()

    def test_get_meta_skill_filename(self) -> None:
        """Test get_meta_skill_filename returns index.toml in subdirectory."""
        adapter = GeminiAdapter()

        result = adapter.get_meta_skill_filename("my_job")

        # Gemini uses subdirectories with index.toml for meta-skills
        assert result == "my_job/index.toml"

    def test_get_step_skill_filename_returns_clean_name(self) -> None:
        """Test get_step_skill_filename returns clean TOML with subdirectory."""
        adapter = GeminiAdapter()

        result = adapter.get_step_skill_filename("my_job", "step_one")

        # Gemini uses subdirectories for namespacing (colon becomes path)
        # No prefix on skill filenames
        assert result == "my_job/step_one.toml"

    def test_get_step_skill_filename_exposed(self) -> None:
        """Test get_step_skill_filename with exposed=True (same result, no prefix)."""
        adapter = GeminiAdapter()

        result = adapter.get_step_skill_filename("my_job", "step_one", exposed=True)

        # Same filename whether exposed or not
        assert result == "my_job/step_one.toml"

    def test_get_step_skill_filename_with_underscores(self) -> None:
        """Test get_step_skill_filename with underscores in names."""
        adapter = GeminiAdapter()

        result = adapter.get_step_skill_filename("competitive_research", "identify_competitors")

        assert result == "competitive_research/identify_competitors.toml"

    def test_hook_name_mapping_is_empty(self) -> None:
        """Test that Gemini has no skill-level hooks."""
        assert GeminiAdapter.hook_name_mapping == {}

    def test_supports_hook_returns_false_for_all_hooks(self) -> None:
        """Test that Gemini doesn't support any skill-level hooks."""
        adapter = GeminiAdapter()

        for hook in SkillLifecycleHook:
            assert adapter.supports_hook(hook) is False

    def test_get_platform_hook_name_returns_none(self) -> None:
        """Test that get_platform_hook_name returns None for all hooks."""
        adapter = GeminiAdapter()

        for hook in SkillLifecycleHook:
            assert adapter.get_platform_hook_name(hook) is None

    def test_sync_hooks_returns_zero(self, temp_dir: Path) -> None:
        """Test sync_hooks always returns 0 (no hook support)."""
        (temp_dir / ".gemini").mkdir()
        adapter = GeminiAdapter(temp_dir)
        hooks = {
            "SomeEvent": [{"matcher": "", "hooks": [{"type": "command", "command": "test.sh"}]}]
        }

        count = adapter.sync_hooks(temp_dir, hooks)

        assert count == 0

    def test_sync_hooks_empty_hooks_returns_zero(self, temp_dir: Path) -> None:
        """Test sync_hooks returns 0 for empty hooks."""
        adapter = GeminiAdapter(temp_dir)

        count = adapter.sync_hooks(temp_dir, {})

        assert count == 0

    def test_sync_hooks_does_not_create_settings_file(self, temp_dir: Path) -> None:
        """Test that sync_hooks doesn't create settings.json (unlike Claude)."""
        gemini_dir = temp_dir / ".gemini"
        gemini_dir.mkdir()
        adapter = GeminiAdapter(temp_dir)
        hooks = {
            "AfterAgent": [{"matcher": "", "hooks": [{"type": "command", "command": "test.sh"}]}]
        }

        adapter.sync_hooks(temp_dir, hooks)

        settings_file = gemini_dir / "settings.json"
        assert not settings_file.exists()
