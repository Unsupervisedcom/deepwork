"""Tests for MCP server startup instructions and issue appending."""

from __future__ import annotations

from pathlib import Path

import yaml

from deepwork.jobs.issues import Issue
from deepwork.jobs.mcp.server import _STATIC_INSTRUCTIONS, _build_startup_instructions


class TestBuildStartupInstructions:
    """Tests for _build_startup_instructions()."""

    def test_includes_static_instructions_always(self, tmp_path: Path) -> None:
        """Static server instructions are always included."""
        result = _build_startup_instructions(tmp_path, issues=[])
        assert "DeepWork Workflow Server" in result
        assert "session_id" in result

    def test_with_issues_shows_warning(self, tmp_path: Path) -> None:
        """When issues exist, shows IMPORTANT warning and issue details."""
        issues = [
            Issue(
                severity="error",
                job_name="broken",
                job_dir="/path/broken",
                message="Schema validation failed",
                suggestion="Run `/deepwork repair`",
            )
        ]
        result = _build_startup_instructions(tmp_path, issues)
        assert "IMPORTANT: ISSUE DETECTED" in result
        assert "broken" in result
        assert "Schema validation failed" in result
        assert "/deepwork repair" in result

    def test_without_issues_lists_workflows(self, tmp_path: Path) -> None:
        """When no issues, lists available workflows."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "my_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text(
            yaml.dump(
                {
                    "name": "my_job",
                    "summary": "Test job",
                    "step_arguments": [
                        {"name": "out", "description": "Output", "type": "file_path"}
                    ],
                    "workflows": {
                        "main": {
                            "summary": "Main workflow does stuff",
                            "steps": [
                                {
                                    "name": "step_one",
                                    "instructions": "Do it.",
                                    "outputs": {"out": {"required": True}},
                                }
                            ],
                        }
                    },
                }
            )
        )

        result = _build_startup_instructions(tmp_path, issues=[])
        assert "Available Workflows" in result
        assert "my_job/main" in result
        assert "Main workflow does stuff" in result
        assert "/deepwork" in result

    def test_without_issues_always_includes_workflows(self, tmp_path: Path) -> None:
        """When no issues, standard jobs are always discovered so workflows are listed."""
        result = _build_startup_instructions(tmp_path, issues=[])
        # Standard jobs (deepwork_jobs, deepwork_reviews) are always present
        assert "Available Workflows" in result
        assert "deepwork_jobs" in result

    def test_issues_take_priority_over_workflows(self, tmp_path: Path) -> None:
        """When issues exist, workflows are NOT listed — issue warning only."""
        issues = [
            Issue(
                severity="error",
                job_name="broken",
                job_dir="/path/broken",
                message="Bad schema",
                suggestion="Fix it",
            )
        ]
        result = _build_startup_instructions(tmp_path, issues)
        assert "ISSUE DETECTED" in result
        assert "Available Workflows" not in result
