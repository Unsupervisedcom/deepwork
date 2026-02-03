"""Integration tests for the install command."""

from pathlib import Path

from click.testing import CliRunner

from deepwork.cli.main import cli
from deepwork.utils.yaml_utils import load_yaml


class TestInstallCommand:
    """Integration tests for 'deepwork install' command."""

    def test_install_with_claude(self, mock_claude_project: Path) -> None:
        """Test installing DeepWork in a Claude Code project."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "DeepWork Installation" in result.output
        assert "Git repository found" in result.output
        assert "Claude Code detected" in result.output
        assert "DeepWork installed successfully" in result.output

        # Verify directory structure
        deepwork_dir = mock_claude_project / ".deepwork"
        assert deepwork_dir.exists()
        assert (deepwork_dir / "jobs").exists()

        # Verify config.yml
        config_file = deepwork_dir / "config.yml"
        assert config_file.exists()
        config = load_yaml(config_file)
        assert config is not None
        assert "claude" in config["platforms"]

        # Verify MCP entry point skill was created (deepwork/SKILL.md)
        claude_dir = mock_claude_project / ".claude" / "skills"
        assert (claude_dir / "deepwork" / "SKILL.md").exists()

        # Verify deepwork skill content references MCP tools
        deepwork_skill = (claude_dir / "deepwork" / "SKILL.md").read_text()
        assert "deepwork" in deepwork_skill.lower()

    def test_install_with_auto_detect(self, mock_claude_project: Path) -> None:
        """Test installing with auto-detection."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--path", str(mock_claude_project)], catch_exceptions=False
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

    def test_install_defaults_to_claude_when_no_platform(self, mock_git_repo: Path) -> None:
        """Test that install defaults to Claude Code when no platform is detected."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--path", str(mock_git_repo)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "No AI platform detected, defaulting to Claude Code" in result.output
        assert "Created .claude/" in result.output
        assert "DeepWork installed successfully for Claude Code" in result.output

        # Verify .claude directory was created
        claude_dir = mock_git_repo / ".claude"
        assert claude_dir.exists()

        # Verify config.yml has Claude
        config_file = mock_git_repo / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "claude" in config["platforms"]

        # Verify MCP entry point skill was created for Claude
        skills_dir = claude_dir / "skills"
        assert (skills_dir / "deepwork" / "SKILL.md").exists()

    def test_install_with_multiple_platforms_auto_detect(
        self, mock_multi_platform_project: Path
    ) -> None:
        """Test installing with auto-detection when multiple platforms are present."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["install", "--path", str(mock_multi_platform_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Auto-detecting AI platforms" in result.output
        assert "Claude Code detected" in result.output
        assert "Gemini CLI detected" in result.output
        assert "DeepWork installed successfully for Claude Code, Gemini CLI" in result.output

        # Verify config.yml has both platforms
        config_file = mock_multi_platform_project / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "claude" in config["platforms"]
        assert "gemini" in config["platforms"]

        # Verify MCP entry point skill was created for Claude
        claude_dir = mock_multi_platform_project / ".claude" / "skills"
        assert (claude_dir / "deepwork" / "SKILL.md").exists()

        # Note: Gemini MCP skill template (skill-deepwork) is not yet implemented
        # so we don't assert on Gemini skill existence - the install will show
        # an error for Gemini skill generation but continue

    def test_install_with_specified_platform_when_missing(self, mock_git_repo: Path) -> None:
        """Test that install fails when specified platform is not present."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["install", "--platform", "claude", "--path", str(mock_git_repo)]
        )

        assert result.exit_code != 0
        assert "Claude Code not detected" in result.output
        assert ".claude/" in result.output

    def test_install_is_idempotent(self, mock_claude_project: Path) -> None:
        """Test that running install multiple times is safe."""
        runner = CliRunner()

        # First install
        result1 = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result1.exit_code == 0

        # Second install
        result2 = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result2.exit_code == 0

        # Verify files still exist and are valid
        deepwork_dir = mock_claude_project / ".deepwork"
        assert (deepwork_dir / "config.yml").exists()

        claude_dir = mock_claude_project / ".claude" / "skills"
        # MCP entry point skill
        assert (claude_dir / "deepwork" / "SKILL.md").exists()

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
