"""Integration tests for the port command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli
from deepwork.utils.job_location import JobScope, get_jobs_dir
from deepwork.utils.xdg import get_global_jobs_dir


class TestPortCommand:
    """Integration tests for 'deepwork port' command."""

    def test_port_help(self) -> None:
        """Test that port help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["port", "--help"])

        assert result.exit_code == 0
        assert "Port a DeepWork job between local and global scopes" in result.output

    def test_port_from_local_to_global(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test porting a job from local to global scope."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # Create a test job in local scope
        local_jobs_dir = mock_claude_project / ".deepwork" / "jobs"
        test_job_dir = local_jobs_dir / "test_job"
        test_job_dir.mkdir(parents=True)

        # Create minimal job.yml
        job_yml = test_job_dir / "job.yml"
        job_yml.write_text(
            """name: test_job
version: "1.0.0"
summary: "Test job for porting"
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
        steps_dir = test_job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Test step instructions")

        runner = CliRunner()

        # Run port command with input simulation
        # Input: 1 (local), 1 (first job), 2 (global destination)
        result = runner.invoke(
            cli,
            ["port", "--path", str(mock_claude_project)],
            input="1\n1\n2\n",
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "DeepWork Job Porting" in result.output
        assert "test_job" in result.output
        assert "Successfully ported" in result.output

        # Verify job was copied to global location
        global_jobs_dir = get_global_jobs_dir()
        global_test_job = global_jobs_dir / "test_job"
        assert global_test_job.exists()
        assert (global_test_job / "job.yml").exists()
        assert (global_test_job / "steps" / "step1.md").exists()

    def test_port_from_global_to_local(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test porting a job from global to local scope."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # Create a test job in global scope
        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)

        test_job_dir = global_jobs_dir / "global_test_job"
        test_job_dir.mkdir(parents=True)

        # Create minimal job.yml
        job_yml = test_job_dir / "job.yml"
        job_yml.write_text(
            """name: global_test_job
version: "1.0.0"
summary: "Global test job for porting"
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
        steps_dir = test_job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Global test step instructions")

        runner = CliRunner()

        # Run port command with input simulation
        # Input: 2 (global), 1 (first job), 1 (local destination)
        result = runner.invoke(
            cli,
            ["port", "--path", str(mock_claude_project)],
            input="2\n1\n1\n",
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "global_test_job" in result.output
        assert "Successfully ported" in result.output

        # Verify job was copied to local location
        local_jobs_dir = get_jobs_dir(mock_claude_project, JobScope.LOCAL)
        local_test_job = local_jobs_dir / "global_test_job"
        assert local_test_job.exists()
        assert (local_test_job / "job.yml").exists()
        assert (local_test_job / "steps" / "step1.md").exists()

    def test_port_overwrite_existing(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that port asks for confirmation when overwriting existing job."""
        # Set up temporary global directory
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        # Create test job in local scope
        local_jobs_dir = mock_claude_project / ".deepwork" / "jobs"
        test_job_dir = local_jobs_dir / "test_job"
        test_job_dir.mkdir(parents=True)

        job_yml = test_job_dir / "job.yml"
        job_yml.write_text(
            """name: test_job
version: "1.0.0"
summary: "Test job"
steps:
  - id: step1
    name: "Step 1"
    description: "Test step"
    instructions_file: steps/step1.md
    outputs:
      - output.txt
"""
        )

        (test_job_dir / "steps").mkdir()
        (test_job_dir / "steps" / "step1.md").write_text("# Original")

        # Create same job in global scope
        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)
        global_test_job = global_jobs_dir / "test_job"
        global_test_job.mkdir(parents=True)
        (global_test_job / "job.yml").write_text("name: test_job\nversion: 1.0.0")

        runner = CliRunner()

        # Run port command and decline overwrite
        # Input: 1 (local), 1 (first job), 2 (global), n (don't overwrite)
        result = runner.invoke(
            cli,
            ["port", "--path", str(mock_claude_project)],
            input="1\n1\n2\nn\n",
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "already exists" in result.output
        assert "Porting cancelled" in result.output

    def test_port_with_no_jobs_in_source(
        self, mock_claude_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that port fails gracefully when no jobs exist in source."""
        # Set up temporary global directory with no jobs
        global_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_config))

        global_jobs_dir = get_global_jobs_dir()
        global_jobs_dir.mkdir(parents=True, exist_ok=True)

        runner = CliRunner()

        # Try to port from empty global directory
        # Input: 2 (global)
        result = runner.invoke(
            cli, ["port", "--path", str(mock_claude_project)], input="2\n"
        )

        assert result.exit_code != 0
        assert "No jobs found" in result.output
