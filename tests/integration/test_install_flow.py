"""Integration tests for the install command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli
from deepwork.core.registry import JobRegistry
from deepwork.utils.yaml_utils import load_yaml


class TestInstallCommand:
    """Integration tests for 'deepwork install' command."""

    def test_install_with_claude(self, mock_claude_project: Path) -> None:
        """Test installing DeepWork in a Claude Code project."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "DeepWork Installation" in result.output
        assert "Git repository found" in result.output
        assert "Claude Code detected" in result.output
        assert "Installation Complete" in result.output

        # Verify directory structure
        deepwork_dir = mock_claude_project / ".deepwork"
        assert deepwork_dir.exists()
        assert (deepwork_dir / "jobs").exists()

        # Verify config.yml
        config_file = deepwork_dir / "config.yml"
        assert config_file.exists()
        config = load_yaml(config_file)
        assert config is not None
        assert config["platform"] == "claude"
        assert config["version"] == "1.0.0"
        assert "installed" in config

        # Verify registry.yml
        registry_file = deepwork_dir / "registry.yml"
        assert registry_file.exists()

        # Verify core skills were created
        claude_dir = mock_claude_project / ".claude"
        assert (claude_dir / "skill-deepwork.define.md").exists()
        assert (claude_dir / "skill-deepwork.refine.md").exists()

        # Verify skill content
        define_skill = (claude_dir / "skill-deepwork.define.md").read_text()
        assert "Name: deepwork.define" in define_skill
        assert "Interactive job definition wizard" in define_skill

    def test_install_with_auto_detect(self, mock_claude_project: Path) -> None:
        """Test installing with auto-detection."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--path", str(mock_claude_project)],
            catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "Auto-detecting AI platform" in result.output
        assert "Claude Code detected" in result.output

    def test_install_fails_without_git(self, temp_dir: Path) -> None:
        """Test that install fails in non-Git directory."""
        runner = CliRunner()

        result = runner.invoke(cli, ["install", "--platform", "claude", "--path", str(temp_dir)])

        assert result.exit_code != 0
        assert "Not a Git repository" in result.output

    def test_install_fails_without_platform(self, mock_git_repo: Path) -> None:
        """Test that install fails when no platform is detected."""
        runner = CliRunner()

        result = runner.invoke(cli, ["install", "--path", str(mock_git_repo)])

        assert result.exit_code != 0
        assert "No AI platform detected" in result.output

    def test_install_fails_with_multiple_platforms(self, temp_dir: Path) -> None:
        """Test that install fails when multiple platforms detected without explicit choice."""
        from git import Repo

        # Create git repo with multiple platforms
        repo = Repo.init(temp_dir)
        (temp_dir / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create both Claude and Gemini directories
        (temp_dir / ".claude").mkdir()
        (temp_dir / ".gemini").mkdir()

        runner = CliRunner()

        result = runner.invoke(cli, ["install", "--path", str(temp_dir)])

        assert result.exit_code != 0
        assert "Multiple AI platforms detected" in result.output

    def test_install_with_specified_platform_when_missing(
        self, mock_git_repo: Path
    ) -> None:
        """Test that install fails when specified platform is not present."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_git_repo)]
        )

        assert result.exit_code != 0
        assert "Claude Code not detected" in result.output
        assert ".claude/" in result.output

    def test_install_creates_empty_registry(self, mock_claude_project: Path) -> None:
        """Test that install creates an empty job registry."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False
        )

        assert result.exit_code == 0

        # Check registry is created and empty
        deepwork_dir = mock_claude_project / ".deepwork"
        registry = JobRegistry(deepwork_dir)
        jobs = registry.list_jobs()

        assert jobs == []

    def test_install_is_idempotent(self, mock_claude_project: Path) -> None:
        """Test that running install multiple times is safe."""
        runner = CliRunner()

        # First install
        result1 = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False
        )
        assert result1.exit_code == 0

        # Second install
        result2 = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False
        )
        assert result2.exit_code == 0

        # Verify files still exist and are valid
        deepwork_dir = mock_claude_project / ".deepwork"
        assert (deepwork_dir / "config.yml").exists()
        assert (deepwork_dir / "registry.yml").exists()

        claude_dir = mock_claude_project / ".claude"
        assert (claude_dir / "skill-deepwork.define.md").exists()
        assert (claude_dir / "skill-deepwork.refine.md").exists()


class TestCLIEntryPoint:
    """Tests for CLI entry point."""

    def test_cli_version(self) -> None:
        """Test that --version works."""
        runner = CliRunner()

        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_help(self) -> None:
        """Test that --help works."""
        runner = CliRunner()

        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "DeepWork" in result.output
        assert "install" in result.output

    def test_install_help(self) -> None:
        """Test that install --help works."""
        runner = CliRunner()

        result = runner.invoke(cli, ["install", "--help"])

        assert result.exit_code == 0
        assert "Install DeepWork" in result.output
        assert "--platform" in result.output
