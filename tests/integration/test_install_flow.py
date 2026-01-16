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

        # Verify core commands were created
        claude_dir = mock_claude_project / ".claude" / "commands"
        # Meta-command
        assert (claude_dir / "deepwork_jobs.md").exists()
        # Hidden step command (underscore prefix)
        assert (claude_dir / "_deepwork_jobs.define.md").exists()
        # Exposed step command (no underscore - learn has exposed: true)
        assert (claude_dir / "deepwork_jobs.learn.md").exists()

        # Verify meta-command content
        meta_command = (claude_dir / "deepwork_jobs.md").read_text()
        assert "# deepwork_jobs" in meta_command
        assert "Available Steps" in meta_command

        # Verify hidden step command content
        define_command = (claude_dir / "_deepwork_jobs.define.md").read_text()
        assert "# deepwork_jobs.define" in define_command
        assert "Define Job Specification" in define_command

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

    def test_install_fails_without_platform(self, mock_git_repo: Path) -> None:
        """Test that install fails when no platform is detected."""
        runner = CliRunner()

        result = runner.invoke(cli, ["install", "--path", str(mock_git_repo)])

        assert result.exit_code != 0
        assert "No AI platform detected" in result.output

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

        # Verify commands were created for both platforms
        claude_dir = mock_multi_platform_project / ".claude" / "commands"
        # Meta-command and hidden step commands
        assert (claude_dir / "deepwork_jobs.md").exists()
        assert (claude_dir / "_deepwork_jobs.define.md").exists()

        # Gemini uses job_name/step_id.toml structure
        gemini_dir = mock_multi_platform_project / ".gemini" / "commands"
        # Meta-command (index.toml) and hidden step commands
        assert (gemini_dir / "deepwork_jobs" / "index.toml").exists()
        assert (gemini_dir / "deepwork_jobs" / "_define.toml").exists()

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

        claude_dir = mock_claude_project / ".claude" / "commands"
        # Meta-command and step commands
        assert (claude_dir / "deepwork_jobs.md").exists()
        assert (claude_dir / "_deepwork_jobs.define.md").exists()
        assert (claude_dir / "deepwork_jobs.learn.md").exists()

    def test_install_creates_rules_directory(self, mock_claude_project: Path) -> None:
        """Test that install creates the v2 rules directory with example templates."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert ".deepwork/rules/ with example templates" in result.output

        # Verify rules directory was created
        rules_dir = mock_claude_project / ".deepwork" / "rules"
        assert rules_dir.exists()

        # Verify README was created
        readme_file = rules_dir / "README.md"
        assert readme_file.exists()
        content = readme_file.read_text()
        assert "DeepWork Rules" in content
        assert "YAML frontmatter" in content

        # Verify example templates were copied
        example_files = list(rules_dir.glob("*.md.example"))
        assert len(example_files) >= 1  # At least one example template

    def test_install_preserves_existing_rules_directory(self, mock_claude_project: Path) -> None:
        """Test that install doesn't overwrite existing rules directory."""
        runner = CliRunner()

        # Create a custom rules directory before install
        rules_dir = mock_claude_project / ".deepwork" / "rules"
        rules_dir.mkdir(parents=True)
        custom_rule = rules_dir / "my-custom-rule.md"
        custom_content = """---
name: My Custom Rule
trigger: "src/**/*"
---
Custom instructions here.
"""
        custom_rule.write_text(custom_content)

        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert ".deepwork/rules/ already exists" in result.output

        # Verify original content is preserved
        assert custom_rule.read_text() == custom_content


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
