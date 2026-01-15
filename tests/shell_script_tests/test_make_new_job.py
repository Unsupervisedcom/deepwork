"""Tests for make_new_job.sh utility script.

This script creates the directory structure for a new DeepWork job.
It should:
1. Validate job name format (lowercase, letters/numbers/underscores)
2. Create the job directory structure under .deepwork/jobs/
3. Create required subdirectories (steps/, hooks/, templates/)
4. Create AGENTS.md with guidance
5. Handle existing jobs gracefully (error)
6. Handle missing .deepwork directory by creating it
"""

from pathlib import Path

import pytest

from .conftest import run_shell_script


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a basic project directory."""
    return tmp_path


@pytest.fixture
def project_with_deepwork(tmp_path: Path) -> Path:
    """Create a project with existing .deepwork/jobs directory."""
    jobs_dir = tmp_path / ".deepwork" / "jobs"
    jobs_dir.mkdir(parents=True)
    return tmp_path


def run_make_new_job(
    script_path: Path,
    cwd: Path,
    job_name: str | None = None,
) -> tuple[str, str, int]:
    """Run the make_new_job.sh script."""
    args = [job_name] if job_name else None
    return run_shell_script(script_path, cwd, args=args, env_extra={"NO_COLOR": "1"})


class TestMakeNewJobUsage:
    """Tests for make_new_job.sh usage and help output."""

    def test_shows_usage_without_arguments(self, jobs_scripts_dir: Path, project_dir: Path) -> None:
        """Test that the script shows usage when called without arguments."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_dir)

        assert code == 1, "Should exit with error when no arguments"
        assert "Usage:" in stdout, "Should show usage information"
        assert "job_name" in stdout.lower(), "Should mention job_name argument"

    def test_shows_example_in_usage(self, jobs_scripts_dir: Path, project_dir: Path) -> None:
        """Test that the usage includes an example."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_dir)

        assert "Example:" in stdout, "Should show example usage"


class TestMakeNewJobNameValidation:
    """Tests for job name validation in make_new_job.sh."""

    def test_accepts_lowercase_name(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that lowercase names are accepted."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "valid_job")

        assert code == 0, f"Should accept lowercase name. stderr: {stderr}"

    def test_accepts_name_with_numbers(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that names with numbers are accepted."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "job123")

        assert code == 0, f"Should accept name with numbers. stderr: {stderr}"

    def test_accepts_name_with_underscores(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that names with underscores are accepted."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "my_new_job")

        assert code == 0, f"Should accept underscores. stderr: {stderr}"

    def test_rejects_uppercase_name(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that uppercase names are rejected."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "InvalidJob")

        assert code != 0, "Should reject uppercase name"
        # Check for error message in stdout (script uses echo)
        output = stdout + stderr
        assert "invalid" in output.lower() or "error" in output.lower(), (
            "Should show error for invalid name"
        )

    def test_rejects_name_starting_with_number(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that names starting with numbers are rejected."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "123job")

        assert code != 0, "Should reject name starting with number"

    def test_rejects_name_with_hyphens(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that names with hyphens are rejected."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "my-job")

        assert code != 0, "Should reject name with hyphens"

    def test_rejects_name_with_spaces(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that names with spaces are rejected."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        # This will be passed as two arguments by bash, causing an error
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "my job")

        # Either fails validation or treats "job" as separate (job is valid name)
        # The key is it shouldn't create "my job" as a directory name
        bad_dir = project_with_deepwork / ".deepwork" / "jobs" / "my job"
        assert not bad_dir.exists(), "Should not create directory with space in name"


class TestMakeNewJobDirectoryStructure:
    """Tests for directory structure creation in make_new_job.sh."""

    def test_creates_main_job_directory(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that the main job directory is created."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        job_dir = project_with_deepwork / ".deepwork" / "jobs" / "test_job"
        assert job_dir.exists(), "Job directory should be created"
        assert job_dir.is_dir(), "Job path should be a directory"

    def test_creates_steps_directory(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that steps/ subdirectory is created."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        steps_dir = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "steps"
        assert steps_dir.exists(), "steps/ directory should be created"
        assert steps_dir.is_dir(), "steps/ should be a directory"

    def test_creates_hooks_directory(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that hooks/ subdirectory is created."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        hooks_dir = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "hooks"
        assert hooks_dir.exists(), "hooks/ directory should be created"
        assert hooks_dir.is_dir(), "hooks/ should be a directory"

    def test_creates_templates_directory(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that templates/ subdirectory is created."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        templates_dir = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "templates"
        assert templates_dir.exists(), "templates/ directory should be created"
        assert templates_dir.is_dir(), "templates/ should be a directory"

    def test_creates_gitkeep_files(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that .gitkeep files are created in empty directories."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        job_dir = project_with_deepwork / ".deepwork" / "jobs" / "test_job"

        hooks_gitkeep = job_dir / "hooks" / ".gitkeep"
        templates_gitkeep = job_dir / "templates" / ".gitkeep"

        assert hooks_gitkeep.exists(), "hooks/.gitkeep should be created"
        assert templates_gitkeep.exists(), "templates/.gitkeep should be created"

    def test_creates_agents_md(self, jobs_scripts_dir: Path, project_with_deepwork: Path) -> None:
        """Test that AGENTS.md file is created."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        agents_md = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md should be created"

        content = agents_md.read_text()
        assert "Job Management" in content, "AGENTS.md should have job management content"
        assert "deepwork_jobs" in content, "AGENTS.md should reference deepwork_jobs"


class TestMakeNewJobAgentsMdContent:
    """Tests for AGENTS.md content in make_new_job.sh."""

    def test_agents_md_contains_slash_commands(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that AGENTS.md lists recommended slash commands."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        agents_md = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "AGENTS.md"
        content = agents_md.read_text()

        assert "/deepwork_jobs.define" in content, "Should mention define command"
        assert "/deepwork_jobs.implement" in content, "Should mention implement command"
        assert "/deepwork_jobs.learn" in content, "Should mention learn command"

    def test_agents_md_contains_directory_structure(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that AGENTS.md documents the directory structure."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "test_job")

        agents_md = project_with_deepwork / ".deepwork" / "jobs" / "test_job" / "AGENTS.md"
        content = agents_md.read_text()

        assert "job.yml" in content, "Should mention job.yml"
        assert "steps/" in content, "Should document steps directory"
        assert "hooks/" in content, "Should document hooks directory"
        assert "templates/" in content, "Should document templates directory"


class TestMakeNewJobErrorHandling:
    """Tests for error handling in make_new_job.sh."""

    def test_fails_if_job_already_exists(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that creating a job that already exists fails."""
        # First create the job
        script_path = jobs_scripts_dir / "make_new_job.sh"
        run_make_new_job(script_path, project_with_deepwork, "existing_job")

        # Try to create it again
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "existing_job")

        assert code != 0, "Should fail when job already exists"
        output = stdout + stderr
        assert "exist" in output.lower() or "error" in output.lower(), (
            "Should mention that job exists"
        )

    def test_creates_deepwork_directory_if_missing(
        self, jobs_scripts_dir: Path, project_dir: Path
    ) -> None:
        """Test that .deepwork/jobs is created if it doesn't exist."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_dir, "new_job")

        assert code == 0, f"Should succeed even without .deepwork. stderr: {stderr}"

        job_dir = project_dir / ".deepwork" / "jobs" / "new_job"
        assert job_dir.exists(), "Should create .deepwork/jobs/new_job"


class TestMakeNewJobOutput:
    """Tests for output messages in make_new_job.sh."""

    def test_shows_success_message(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that success message is shown."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "new_job")

        assert code == 0, f"Should succeed. stderr: {stderr}"
        # Check for informational output
        assert "new_job" in stdout, "Output should mention job name"

    def test_shows_next_steps(self, jobs_scripts_dir: Path, project_with_deepwork: Path) -> None:
        """Test that next steps are shown after creation."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "new_job")

        assert code == 0, f"Should succeed. stderr: {stderr}"
        # Should mention what to do next
        assert "next" in stdout.lower() or "step" in stdout.lower(), "Should show next steps"

    def test_shows_directory_structure_created(
        self, jobs_scripts_dir: Path, project_with_deepwork: Path
    ) -> None:
        """Test that created directory structure is shown."""
        script_path = jobs_scripts_dir / "make_new_job.sh"
        stdout, stderr, code = run_make_new_job(script_path, project_with_deepwork, "new_job")

        assert code == 0, f"Should succeed. stderr: {stderr}"
        # Should show what was created
        assert "AGENTS.md" in stdout or "steps" in stdout, "Should show created structure"
