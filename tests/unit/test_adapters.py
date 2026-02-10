"""Tests for adapter MCP server registration."""

import json
from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with .claude dir."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return tmp_path


class TestClaudeAdapterMCPRegistration:
    """Tests for ClaudeAdapter.register_mcp_server."""

    def test_register_creates_mcp_json(self, project_root: Path) -> None:
        """Test that register_mcp_server creates .mcp.json."""
        adapter = ClaudeAdapter(project_root=project_root)
        result = adapter.register_mcp_server(project_root)

        assert result is True
        assert (project_root / ".mcp.json").exists()

    def test_register_includes_external_runner_claude(self, project_root: Path) -> None:
        """Test that .mcp.json args include --external-runner claude."""
        adapter = ClaudeAdapter(project_root=project_root)
        adapter.register_mcp_server(project_root)

        config = json.loads((project_root / ".mcp.json").read_text())
        args = config["mcpServers"]["deepwork"]["args"]

        assert "--external-runner" in args
        idx = args.index("--external-runner")
        assert args[idx + 1] == "claude"

    def test_register_full_args(self, project_root: Path) -> None:
        """Test the complete args list in .mcp.json."""
        adapter = ClaudeAdapter(project_root=project_root)
        adapter.register_mcp_server(project_root)

        config = json.loads((project_root / ".mcp.json").read_text())
        args = config["mcpServers"]["deepwork"]["args"]

        assert args == ["serve", "--path", ".", "--external-runner", "claude"]

    def test_register_command_is_deepwork(self, project_root: Path) -> None:
        """Test that the command in .mcp.json is 'deepwork'."""
        adapter = ClaudeAdapter(project_root=project_root)
        adapter.register_mcp_server(project_root)

        config = json.loads((project_root / ".mcp.json").read_text())
        assert config["mcpServers"]["deepwork"]["command"] == "deepwork"

    def test_register_is_idempotent(self, project_root: Path) -> None:
        """Test that registering twice with same config returns False."""
        adapter = ClaudeAdapter(project_root=project_root)

        assert adapter.register_mcp_server(project_root) is True
        assert adapter.register_mcp_server(project_root) is False

    def test_register_updates_old_config(self, project_root: Path) -> None:
        """Test that registering updates an existing .mcp.json with old args."""
        # Write an old-style config without --external-runner
        old_config = {
            "mcpServers": {
                "deepwork": {
                    "command": "deepwork",
                    "args": ["serve", "--path", "."],
                }
            }
        }
        (project_root / ".mcp.json").write_text(json.dumps(old_config))

        adapter = ClaudeAdapter(project_root=project_root)
        result = adapter.register_mcp_server(project_root)

        # Should detect the difference and update
        assert result is True
        config = json.loads((project_root / ".mcp.json").read_text())
        assert config["mcpServers"]["deepwork"]["args"] == [
            "serve", "--path", ".", "--external-runner", "claude"
        ]

    def test_register_preserves_other_servers(self, project_root: Path) -> None:
        """Test that registering deepwork preserves other MCP servers."""
        existing_config = {
            "mcpServers": {
                "other_server": {
                    "command": "other",
                    "args": ["--flag"],
                }
            }
        }
        (project_root / ".mcp.json").write_text(json.dumps(existing_config))

        adapter = ClaudeAdapter(project_root=project_root)
        adapter.register_mcp_server(project_root)

        config = json.loads((project_root / ".mcp.json").read_text())
        assert "other_server" in config["mcpServers"]
        assert config["mcpServers"]["other_server"]["command"] == "other"
        assert "deepwork" in config["mcpServers"]
