"""Tests for agent adapters."""

import json
from pathlib import Path

import pytest

from deepwork.core.adapters import (
    AdapterError,
    AgentAdapter,
    ClaudeAdapter,
)


class TestAgentAdapterRegistry:
    """Tests for AgentAdapter registry functionality."""

    def test_get_all_returns_registered_adapters(self) -> None:
        """Test that get_all returns all registered adapters."""
        adapters = AgentAdapter.get_all()

        assert "claude" in adapters
        assert adapters["claude"] is ClaudeAdapter

    def test_get_returns_correct_adapter(self) -> None:
        """Test that get returns the correct adapter class."""
        assert AgentAdapter.get("claude") is ClaudeAdapter

    def test_get_raises_for_unknown_adapter(self) -> None:
        """Test that get raises AdapterError for unknown adapter."""
        with pytest.raises(AdapterError, match="Unknown adapter 'unknown'"):
            AgentAdapter.get("unknown")

    def test_list_names_returns_all_names(self) -> None:
        """Test that list_names returns all registered adapter names."""
        names = AgentAdapter.list_names()

        assert "claude" in names
        assert len(names) >= 1  # At least claude


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
