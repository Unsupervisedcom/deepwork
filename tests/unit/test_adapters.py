"""Tests for agent adapters."""

import json
from pathlib import Path

import pytest

from deepwork.core.adapters import (
    AdapterError,
    AgentAdapter,
    ClaudeAdapter,
    CommandLifecycleHook,
    GeminiAdapter,
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
        assert ClaudeAdapter.commands_dir == "commands"

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

    def test_get_commands_dir(self, temp_dir: Path) -> None:
        """Test get_commands_dir."""
        adapter = ClaudeAdapter(temp_dir)

        result = adapter.get_commands_dir()

        assert result == temp_dir / ".claude" / "commands"

    def test_get_commands_dir_with_explicit_root(self, temp_dir: Path) -> None:
        """Test get_commands_dir with explicit project root."""
        adapter = ClaudeAdapter()

        result = adapter.get_commands_dir(temp_dir)

        assert result == temp_dir / ".claude" / "commands"

    def test_get_commands_dir_raises_without_root(self) -> None:
        """Test get_commands_dir raises when no project root specified."""
        adapter = ClaudeAdapter()

        with pytest.raises(AdapterError, match="No project root specified"):
            adapter.get_commands_dir()

    def test_get_command_filename(self) -> None:
        """Test get_command_filename."""
        adapter = ClaudeAdapter()

        result = adapter.get_command_filename("my_job", "step_one")

        assert result == "my_job.step_one.md"

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


class TestGeminiAdapter:
    """Tests for GeminiAdapter."""

    def test_class_attributes(self) -> None:
        """Test Gemini adapter class attributes."""
        assert GeminiAdapter.name == "gemini"
        assert GeminiAdapter.display_name == "Gemini CLI"
        assert GeminiAdapter.config_dir == ".gemini"
        assert GeminiAdapter.commands_dir == "commands"
        assert GeminiAdapter.command_template == "command-job-step.toml.jinja"

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

    def test_get_commands_dir(self, temp_dir: Path) -> None:
        """Test get_commands_dir."""
        adapter = GeminiAdapter(temp_dir)

        result = adapter.get_commands_dir()

        assert result == temp_dir / ".gemini" / "commands"

    def test_get_commands_dir_with_explicit_root(self, temp_dir: Path) -> None:
        """Test get_commands_dir with explicit project root."""
        adapter = GeminiAdapter()

        result = adapter.get_commands_dir(temp_dir)

        assert result == temp_dir / ".gemini" / "commands"

    def test_get_commands_dir_raises_without_root(self) -> None:
        """Test get_commands_dir raises when no project root specified."""
        adapter = GeminiAdapter()

        with pytest.raises(AdapterError, match="No project root specified"):
            adapter.get_commands_dir()

    def test_get_command_filename(self) -> None:
        """Test get_command_filename returns TOML with subdirectory."""
        adapter = GeminiAdapter()

        result = adapter.get_command_filename("my_job", "step_one")

        # Gemini uses subdirectories for namespacing (colon becomes path)
        assert result == "my_job/step_one.toml"

    def test_get_command_filename_with_underscores(self) -> None:
        """Test get_command_filename with underscores in names."""
        adapter = GeminiAdapter()

        result = adapter.get_command_filename("competitive_research", "identify_competitors")

        assert result == "competitive_research/identify_competitors.toml"

    def test_hook_name_mapping_is_empty(self) -> None:
        """Test that Gemini has no command-level hooks."""
        assert GeminiAdapter.hook_name_mapping == {}

    def test_supports_hook_returns_false_for_all_hooks(self) -> None:
        """Test that Gemini doesn't support any command-level hooks."""
        adapter = GeminiAdapter()

        for hook in CommandLifecycleHook:
            assert adapter.supports_hook(hook) is False

    def test_get_platform_hook_name_returns_none(self) -> None:
        """Test that get_platform_hook_name returns None for all hooks."""
        adapter = GeminiAdapter()

        for hook in CommandLifecycleHook:
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
