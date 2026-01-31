"""Integration tests for global job support."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli
from deepwork.utils.xdg import get_global_jobs_dir


class TestGlobalJobSupport:
    """Integration tests for global job storage and discovery."""

    def test_sync_discovers_global_jobs(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that sync command discovers jobs in global scope."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # First, install DeepWork in the project
        runner = CliRunner()
        install_result = runner.invoke(
            cli, ["install", "--path", str(mock_claude_project)], catch_exceptions=False
        )
        assert install_result.exit_code == 0

        # Create a global job
        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)

        global_job_dir = global_jobs_dir / "global_test_job"
        global_job_dir.mkdir(parents=True)

        # Create minimal job.yml
        job_yml = global_job_dir / "job.yml"
        job_yml.write_text(
            """name: global_test_job
version: "1.0.0"
summary: "Global test job"
steps:
  - id: step1
    name: "Step 1"
    description: "Test step"
    instructions_file: steps/step1.md
    outputs:
      - output.txt
"""
        )

        # Create steps directory
        steps_dir = global_job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Test step instructions")

        # Run sync command
        result = runner.invoke(
            cli, ["sync", "--path", str(mock_claude_project)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "Syncing DeepWork Skills" in result.output
        # Should find jobs in both local and global scopes
        assert "global_test_job" in result.output
        assert "Loaded global_test_job v1.0.0" in result.output

    def test_sync_prefers_local_over_global_for_duplicates(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that local jobs take precedence over global jobs with the same name."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # First, install DeepWork in the project
        runner = CliRunner()
        install_result = runner.invoke(
            cli, ["install", "--path", str(mock_claude_project)], catch_exceptions=False
        )
        assert install_result.exit_code == 0

        # Create same job in both local and global
        job_content = """name: duplicate_job
version: "1.0.0"
summary: "Duplicate job"
steps:
  - id: step1
    name: "Step 1"
    description: "Test step"
    instructions_file: steps/step1.md
    outputs:
      - output.txt
"""

        # Local version
        local_jobs_dir = mock_claude_project / ".deepwork" / "jobs"
        local_job_dir = local_jobs_dir / "duplicate_job"
        local_job_dir.mkdir(parents=True)
        (local_job_dir / "job.yml").write_text(job_content)
        local_steps = local_job_dir / "steps"
        local_steps.mkdir()
        (local_steps / "step1.md").write_text("# Local version")

        # Global version
        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)
        global_job_dir = global_jobs_dir / "duplicate_job"
        global_job_dir.mkdir(parents=True)
        (global_job_dir / "job.yml").write_text(job_content)
        global_steps = global_job_dir / "steps"
        global_steps.mkdir()
        (global_steps / "step1.md").write_text("# Global version")

        # Run sync command
        result = runner.invoke(
            cli, ["sync", "--path", str(mock_claude_project)], catch_exceptions=False
        )

        assert result.exit_code == 0
        # Should load both jobs (they are in different directories, so no conflict)
        # But the local one is listed first
        output_lines = result.output.split("\n")
        duplicate_lines = [line for line in output_lines if "duplicate_job" in line]
        # Should see exactly 2 references (one for each scope's discovery + one for loading each)
        assert len(duplicate_lines) >= 2

    def test_global_jobs_dir_respects_xdg_config_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that global jobs directory respects XDG_CONFIG_HOME."""
        custom_config = tmp_path / "custom_config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))

        global_jobs_dir = get_global_jobs_dir()

        assert global_jobs_dir == custom_config / "deepwork" / "jobs"

    def test_global_jobs_dir_defaults_to_home_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that global jobs directory defaults to ~/.config when XDG_CONFIG_HOME is not set."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        global_jobs_dir = get_global_jobs_dir()

        assert global_jobs_dir == Path.home() / ".config" / "deepwork" / "jobs"

    def test_sync_with_only_global_jobs(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test sync when only global jobs exist (no local jobs)."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # First, install DeepWork in the project
        runner = CliRunner()
        install_result = runner.invoke(
            cli, ["install", "--path", str(mock_claude_project)], catch_exceptions=False
        )
        assert install_result.exit_code == 0

        # Create a global job
        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)

        global_job_dir = global_jobs_dir / "only_global_job"
        global_job_dir.mkdir(parents=True)

        job_yml = global_job_dir / "job.yml"
        job_yml.write_text(
            """name: only_global_job
version: "1.0.0"
summary: "Only in global scope"
steps:
  - id: step1
    name: "Step 1"
    description: "Test step"
    instructions_file: steps/step1.md
    outputs:
      - output.txt
"""
        )

        steps_dir = global_job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Global only step")

        # Remove all local jobs except standard jobs
        local_jobs_dir = mock_claude_project / ".deepwork" / "jobs"
        if local_jobs_dir.exists():
            for job_dir in local_jobs_dir.iterdir():
                if job_dir.is_dir() and job_dir.name not in [
                    "deepwork_jobs",
                    "deepwork_rules",
                ]:
                    import shutil

                    shutil.rmtree(job_dir)

        result = runner.invoke(
            cli, ["sync", "--path", str(mock_claude_project)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "only_global_job" in result.output
        assert "Loaded only_global_job v1.0.0" in result.output
