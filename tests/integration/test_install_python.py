"""Integration tests for Python environment installation."""

from pathlib import Path

from click.testing import CliRunner

from deepwork.cli.main import cli
from deepwork.utils.yaml_utils import load_yaml


class TestInstallPythonEnvironment:
    """Integration tests for Python environment setup during install."""

    def test_install_with_uv_manager(self, mock_claude_project: Path) -> None:
        """Test installing with uv Python manager."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "uv"
            ],
            catch_exceptions=False,
        )

        # Note: This might fail if uv isn't available, but we can still check config
        # Verify config.yml has python section
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        assert config_file.exists()
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "uv"
        assert config["python"]["version"] == "3.11"
        assert config["python"]["venv_path"] == ".venv"

    def test_install_with_system_python_manager(self, mock_claude_project: Path) -> None:
        """Test installing with system Python manager."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "system"
            ],
            catch_exceptions=False,
        )

        # Verify config.yml has python section
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        assert config_file.exists()
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "system"

    def test_install_with_skip_python(self, mock_claude_project: Path) -> None:
        """Test installing with Python setup skipped."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "skip"
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        
        # Verify config.yml has python section with skip
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        assert config_file.exists()
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "skip"

    def test_install_detects_existing_venv(self, mock_claude_project: Path) -> None:
        """Test that install detects existing virtual environment."""
        # Create a mock existing venv
        venv_dir = mock_claude_project / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python").touch()

        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
            ],
            input="3\n",  # Choose skip when prompted
            catch_exceptions=False,
        )

        # Should detect the existing venv
        assert "Found existing virtual environment" in result.output

        # Verify config shows skip (since we have existing venv)
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        # Should use skip since existing venv was detected
        assert config["python"]["manager"] == "skip"

    def test_install_interactive_prompt_uv(self, mock_claude_project: Path) -> None:
        """Test interactive Python setup prompt choosing uv."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
            ],
            input="1\n",  # Choose uv
            catch_exceptions=False,
        )

        # Should show the prompt
        assert "Python Environment Setup" in result.output
        assert "uv (Recommended)" in result.output

        # Verify config
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "uv"

    def test_install_interactive_prompt_system(self, mock_claude_project: Path) -> None:
        """Test interactive Python setup prompt choosing system Python."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
            ],
            input="2\n",  # Choose system Python
            catch_exceptions=False,
        )

        # Should show the prompt
        assert "Python Environment Setup" in result.output
        assert "System Python" in result.output

        # Verify config
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "system"

    def test_install_interactive_prompt_skip(self, mock_claude_project: Path) -> None:
        """Test interactive Python setup prompt choosing skip."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
            ],
            input="3\n",  # Choose skip
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        # Verify config
        config_file = mock_claude_project / ".deepwork" / "config.yml"
        config = load_yaml(config_file)
        assert config is not None
        assert "python" in config
        assert config["python"]["manager"] == "skip"

    def test_install_creates_gitignore_with_venv(self, mock_claude_project: Path) -> None:
        """Test that install creates .gitignore with .venv entry."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "uv"
            ],
            catch_exceptions=False,
        )

        # Verify .gitignore was created
        gitignore_path = mock_claude_project / ".gitignore"
        assert gitignore_path.exists()
        
        # Verify .venv is in .gitignore
        gitignore_content = gitignore_path.read_text()
        assert ".venv" in gitignore_content

    def test_install_appends_to_existing_gitignore(self, mock_claude_project: Path) -> None:
        """Test that install appends .venv to existing .gitignore."""
        # Create existing .gitignore
        gitignore_path = mock_claude_project / ".gitignore"
        original_content = "*.pyc\n__pycache__/\n"
        gitignore_path.write_text(original_content)

        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "uv"
            ],
            catch_exceptions=False,
        )

        # Verify original content is preserved
        gitignore_content = gitignore_path.read_text()
        assert "*.pyc" in gitignore_content
        assert "__pycache__/" in gitignore_content
        
        # Verify .venv was added
        assert ".venv" in gitignore_content

    def test_install_does_not_duplicate_venv_in_gitignore(self, mock_claude_project: Path) -> None:
        """Test that install doesn't duplicate .venv if already in .gitignore."""
        # Create .gitignore with .venv already present
        gitignore_path = mock_claude_project / ".gitignore"
        gitignore_path.write_text(".venv\n")

        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "install",
                "--platform", "claude",
                "--path", str(mock_claude_project),
                "--python-manager", "uv"
            ],
            catch_exceptions=False,
        )

        # Verify .venv appears only once
        gitignore_content = gitignore_path.read_text()
        assert gitignore_content.count(".venv") == 1
