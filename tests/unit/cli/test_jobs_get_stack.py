"""Tests for the `deepwork jobs get-stack` CLI command -- validates DW-REQ-005.4."""

from __future__ import annotations

import json
from pathlib import Path

import click
from click.testing import CliRunner

from deepwork.cli.jobs import get_stack, jobs
from deepwork.cli.main import cli


def _create_session_file(
    sessions_dir: Path,
    session_id: str,
    job_name: str = "test_job",
    workflow_name: str = "main",
    status: str = "active",
    current_step_id: str = "step1",
    goal: str = "Test goal",
    instance_id: str | None = None,
    step_progress: dict | None = None,
) -> Path:
    """Create a session JSON file for testing."""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "job_name": job_name,
        "workflow_name": workflow_name,
        "instance_id": instance_id,
        "goal": goal,
        "current_step_id": current_step_id,
        "current_entry_index": 0,
        "step_progress": step_progress or {},
        "started_at": "2026-01-15T10:00:00+00:00",
        "completed_at": None,
        "status": status,
        "abort_reason": None,
    }
    path = sessions_dir / f"session_{session_id}.json"
    path.write_text(json.dumps(data))
    return path


def _create_minimal_job(parent: Path, job_name: str, steps: list[str] | None = None) -> Path:
    """Create a minimal valid job directory for testing."""
    if steps is None:
        steps = ["step1"]

    job_dir = parent / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    steps_dir = job_dir / "steps"
    steps_dir.mkdir(exist_ok=True)

    step_defs = []
    workflow_steps = []
    for step_id in steps:
        (steps_dir / f"{step_id}.md").write_text(f"# {step_id}\n\nInstructions for {step_id}.")
        step_defs.append(
            f"""  - id: {step_id}
    name: {step_id.replace("_", " ").title()}
    description: {step_id} description
    instructions_file: steps/{step_id}.md
    outputs: {{}}
    reviews: []"""
        )
        workflow_steps.append(f"      - {step_id}")

    (job_dir / "job.yml").write_text(
        f"""name: {job_name}
version: "1.0.0"
summary: Test job {job_name}
common_job_info_provided_to_all_steps_at_runtime: Common info for {job_name}

steps:
{chr(10).join(step_defs)}

workflows:
  - name: main
    summary: Main workflow
    steps:
{chr(10).join(workflow_steps)}
"""
    )
    return job_dir


class TestJobsCommandStructure:
    """Tests for the structural requirements of the jobs CLI command."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_jobs_is_click_group(self) -> None:
        """The jobs command must be a Click group command."""
        assert isinstance(jobs, click.Group)

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_get_stack_is_subcommand_of_jobs(self) -> None:
        """The jobs group must provide a get-stack subcommand."""
        assert "get-stack" in jobs.commands

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_get_stack_has_path_option(self) -> None:
        """The get-stack subcommand must accept a --path option with default '.'."""
        cmd = jobs.commands["get-stack"]
        param_names = [p.name for p in cmd.params]
        assert "path" in param_names
        path_param = next(p for p in cmd.params if p.name == "path")
        assert path_param.default == "."

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_jobs_registered_as_cli_subcommand(self) -> None:
        """The jobs command must be registered as a subcommand of the main CLI."""
        assert "jobs" in cli.commands


class TestGetStackNoSessions:
    """Tests when no sessions exist."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.11).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_deepwork_dir(self, tmp_path: Path) -> None:
        """No .deepwork/tmp/ directory -> empty list."""
        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {"active_sessions": []}

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.11).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_empty_sessions_dir(self, tmp_path: Path) -> None:
        """Empty .deepwork/tmp/ directory -> empty list."""
        (tmp_path / ".deepwork" / "tmp").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {"active_sessions": []}


class TestGetStackActiveSessions:
    """Tests for active sessions with loadable jobs."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.4, DW-REQ-005.4.6, DW-REQ-005.4.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_single_active_session_with_job(self, tmp_path: Path) -> None:
        """Active session with matching job -> includes common_job_info and step instructions."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(sessions_dir, "abc12345", job_name="my_job")
        _create_minimal_job(tmp_path / ".deepwork" / "jobs", "my_job")

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert len(data["active_sessions"]) == 1

        session = data["active_sessions"][0]
        assert session["session_id"] == "abc12345"
        assert session["job_name"] == "my_job"
        assert session["workflow_name"] == "main"
        assert session["goal"] == "Test goal"
        assert session["current_step_id"] == "step1"
        assert session["common_job_info"] == "Common info for my_job"
        assert "Instructions for step1" in session["current_step_instructions"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_session_with_instance_id(self, tmp_path: Path) -> None:
        """Session with instance_id is included in output."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(sessions_dir, "def67890", job_name="my_job", instance_id="acme")
        _create_minimal_job(tmp_path / ".deepwork" / "jobs", "my_job")

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        session = data["active_sessions"][0]
        assert session["instance_id"] == "acme"

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_completed_steps_extracted(self, tmp_path: Path) -> None:
        """Completed steps are extracted from step_progress."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(
            sessions_dir,
            "abc12345",
            job_name="my_job",
            current_step_id="step2",
            step_progress={
                "step1": {
                    "step_id": "step1",
                    "started_at": "2026-01-15T10:00:00+00:00",
                    "completed_at": "2026-01-15T10:05:00+00:00",
                    "outputs": {},
                    "notes": None,
                    "quality_attempts": 0,
                },
                "step2": {
                    "step_id": "step2",
                    "started_at": "2026-01-15T10:06:00+00:00",
                    "completed_at": None,
                    "outputs": {},
                    "notes": None,
                    "quality_attempts": 0,
                },
            },
        )
        _create_minimal_job(tmp_path / ".deepwork" / "jobs", "my_job", steps=["step1", "step2"])

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        session = data["active_sessions"][0]
        assert "step1" in session["completed_steps"]
        assert "step2" not in session["completed_steps"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_step_position_included(self, tmp_path: Path) -> None:
        """Step position (step N of M) is included when job is loadable."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(
            sessions_dir,
            "abc12345",
            job_name="my_job",
            current_step_id="step2",
        )
        _create_minimal_job(
            tmp_path / ".deepwork" / "jobs", "my_job", steps=["step1", "step2", "step3"]
        )

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        session = data["active_sessions"][0]
        assert session["step_number"] == 2
        assert session["total_steps"] == 3


class TestGetStackMixedStatuses:
    """Tests with mixed session statuses."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_only_active_returned(self, tmp_path: Path) -> None:
        """Only active sessions are returned, completed and aborted are filtered out."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(sessions_dir, "active01", status="active")
        _create_session_file(sessions_dir, "done0001", status="completed")
        _create_session_file(sessions_dir, "abort001", status="aborted")

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert len(data["active_sessions"]) == 1
        assert data["active_sessions"][0]["session_id"] == "active01"


class TestGetStackJobNotFound:
    """Tests when job definition cannot be loaded."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_session_without_job_has_null_fields(self, tmp_path: Path) -> None:
        """Session with no matching job dir -> null common_job_info and instructions."""
        sessions_dir = tmp_path / ".deepwork" / "tmp"
        _create_session_file(sessions_dir, "abc12345", job_name="nonexistent_job")

        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert len(data["active_sessions"]) == 1
        session = data["active_sessions"][0]
        assert session["common_job_info"] is None
        assert session["current_step_instructions"] is None
        # Basic fields still populated from session file
        assert session["session_id"] == "abc12345"
        assert session["job_name"] == "nonexistent_job"


class TestGetStackJsonOutput:
    """Tests for valid JSON output."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        """Output is always valid JSON even with no sessions."""
        runner = CliRunner()
        result = runner.invoke(get_stack, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "active_sessions" in data
        assert isinstance(data["active_sessions"], list)
