"""Integration tests for the jobs command."""

import shutil
from pathlib import Path

from click.testing import CliRunner

from deepwork.cli.main import cli


class TestJobsCommand:
    """Integration tests for 'deepwork jobs' command."""

    def test_jobs_list_default(self) -> None:
        """Test listing jobs from default library."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["jobs", "list"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Available Jobs" in result.output
        assert "deepwork library/jobs (default)" in result.output
        # The commit job should always be in the library
        assert "commit" in result.output
        assert "To clone a job" in result.output

    def test_jobs_list_local_path(self, tmp_path: Path) -> None:
        """Test listing jobs from a local path."""
        runner = CliRunner()

        # Create a test jobs directory
        jobs_dir = tmp_path / "test_repo" / "library" / "jobs"
        jobs_dir.mkdir(parents=True)

        # Create a test job
        test_job_dir = jobs_dir / "test_job"
        test_job_dir.mkdir()
        (test_job_dir / "job.yml").write_text(
            """name: test_job
version: "1.0.0"
summary: "A test job for integration testing"
description: |
  This is a test job.

steps:
  - id: test_step
    name: "Test Step"
    description: "A test step"
    instructions_file: steps/test.md
    inputs: []
    outputs: []
    dependencies: []
    quality_criteria:
      - "Test passed"
"""
        )

        # Create steps directory
        (test_job_dir / "steps").mkdir()
        (test_job_dir / "steps" / "test.md").write_text("# Test Step\n\nTest instructions.")

        # List jobs from local path
        result = runner.invoke(
            cli,
            ["jobs", "list", str(tmp_path / "test_repo")],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Available Jobs" in result.output
        assert "test_job" in result.output
        assert "1.0.0" in result.output
        assert "A test job for integration testing" in result.output

    def test_jobs_list_nonexistent_path(self) -> None:
        """Test listing jobs from a nonexistent path."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["jobs", "list", "/nonexistent/path"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "Source not found" in result.output

    def test_jobs_clone_from_default(self, mock_claude_project: Path) -> None:
        """Test cloning a job from the default library."""
        runner = CliRunner()

        # Install DeepWork first
        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Clone the commit job
        result = runner.invoke(
            cli,
            ["jobs", "clone", "commit", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Cloning Job" in result.output
        assert "Using deepwork library/jobs (default)" in result.output
        assert "Found job 'commit'" in result.output
        assert "Validating job definition" in result.output
        assert "commit v1.0.0" in result.output
        assert "Copying job to project" in result.output
        assert "Job 'commit' cloned successfully" in result.output

        # Verify job was copied
        cloned_job_path = mock_claude_project / ".deepwork" / "jobs" / "commit"
        assert cloned_job_path.exists()
        assert (cloned_job_path / "job.yml").exists()
        assert (cloned_job_path / "steps").exists()

    def test_jobs_clone_from_local_path(self, mock_claude_project: Path, tmp_path: Path) -> None:
        """Test cloning a job from a local path."""
        runner = CliRunner()

        # Install DeepWork first
        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Create a test jobs directory
        jobs_dir = tmp_path / "test_repo" / "library" / "jobs"
        jobs_dir.mkdir(parents=True)

        # Create a test job
        test_job_dir = jobs_dir / "my_custom_job"
        test_job_dir.mkdir()
        (test_job_dir / "job.yml").write_text(
            """name: my_custom_job
version: "2.0.0"
summary: "A custom test job"
description: |
  This is a custom test job.

steps:
  - id: custom_step
    name: "Custom Step"
    description: "A custom step"
    instructions_file: steps/custom.md
    inputs: []
    outputs: []
    dependencies: []
    quality_criteria:
      - "Custom test passed"
"""
        )

        # Create steps directory
        (test_job_dir / "steps").mkdir()
        (test_job_dir / "steps" / "custom.md").write_text("# Custom Step\n\nCustom instructions.")

        # Clone the job from local path
        result = runner.invoke(
            cli,
            [
                "jobs",
                "clone",
                "my_custom_job",
                str(tmp_path / "test_repo"),
                "--path",
                str(mock_claude_project),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Cloning Job" in result.output
        assert "Found job 'my_custom_job'" in result.output
        assert "my_custom_job v2.0.0" in result.output
        assert "Job 'my_custom_job' cloned successfully" in result.output

        # Verify job was copied
        cloned_job_path = mock_claude_project / ".deepwork" / "jobs" / "my_custom_job"
        assert cloned_job_path.exists()
        assert (cloned_job_path / "job.yml").exists()
        assert (cloned_job_path / "steps").exists()
        assert (cloned_job_path / "steps" / "custom.md").exists()

    def test_jobs_clone_nonexistent_job(self, mock_claude_project: Path) -> None:
        """Test cloning a nonexistent job."""
        runner = CliRunner()

        # Install DeepWork first
        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Try to clone a nonexistent job
        result = runner.invoke(
            cli,
            ["jobs", "clone", "nonexistent_job", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "not found in source" in result.output

    def test_jobs_clone_overwrite_existing(self, mock_claude_project: Path) -> None:
        """Test cloning a job that already exists."""
        runner = CliRunner()

        # Install DeepWork first
        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Clone the commit job first time
        result = runner.invoke(
            cli,
            ["jobs", "clone", "commit", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Try to clone again (without confirming overwrite)
        result = runner.invoke(
            cli,
            ["jobs", "clone", "commit", "--path", str(mock_claude_project)],
            input="n\n",  # Say no to overwrite
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "already exists" in result.output
        assert "Clone cancelled" in result.output

    def test_jobs_clone_without_deepwork_installed(self, tmp_path: Path) -> None:
        """Test cloning a job without DeepWork installed."""
        runner = CliRunner()

        # Create an empty project directory without DeepWork
        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()

        # Try to clone a job
        result = runner.invoke(
            cli,
            ["jobs", "clone", "commit", "--path", str(project_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "DeepWork not initialized" in result.output
