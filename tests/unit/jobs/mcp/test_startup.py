"""Tests for MCP server startup instructions and issue appending.

Validates requirements: JOBS-REQ-001.10, JOBS-REQ-001.11.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from deepwork.jobs.issues import Issue
from deepwork.jobs.mcp.server import _build_startup_instructions


class TestBuildStartupInstructions:
    """Tests for _build_startup_instructions()."""

    @pytest.fixture(autouse=True)
    def _isolate_job_discovery(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Remove DEEPWORK_ADDITIONAL_JOBS_FOLDERS so only standard jobs are discovered."""
        monkeypatch.delenv("DEEPWORK_ADDITIONAL_JOBS_FOLDERS", raising=False)

    def test_includes_static_instructions_always(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.2).
        """Static server instructions are always included."""
        result = _build_startup_instructions(tmp_path, issues=[])
        assert "DeepWork Workflow Server" in result
        assert "session_id" in result

    def test_with_issues_shows_warning(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.3).
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.4).
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
        assert "my_job" in result
        assert "main" in result

    def test_without_issues_always_includes_workflows(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.4).
        """When no issues, standard jobs are always discovered so workflows are listed."""
        result = _build_startup_instructions(tmp_path, issues=[])
        assert "Available Workflows" in result
        assert "deepwork_jobs" in result

    def test_issues_take_priority_over_workflows(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.5).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_instructions_under_2kb_without_issues(self, tmp_path: Path) -> None:
        """Instructions MUST NOT exceed 2048 bytes to avoid client truncation."""
        result = _build_startup_instructions(tmp_path, issues=[])
        assert len(result) <= 2048, f"Instructions are {len(result)} bytes, max 2048"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_instructions_under_2kb_with_issues(self, tmp_path: Path) -> None:
        """Instructions with issues MUST NOT exceed 2048 bytes."""
        issues = [
            Issue(
                severity="error",
                job_name="broken_job",
                job_dir="/path/to/broken_job",
                message="Job definition validation failed: Validation error at root: "
                "'step_arguments' is a required property",
                suggestion="The invalid file is /path/to/broken_job/job.yml. "
                "If you edited that file this session, fix it directly. "
                "If you did not edit it, the project may need "
                "`/deepwork repair` to migrate legacy formats.",
            )
        ]
        result = _build_startup_instructions(tmp_path, issues)
        assert len(result) <= 2048, f"Instructions are {len(result)} bytes, max 2048"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.10.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_dynamic_content_before_static(self, tmp_path: Path) -> None:
        """Dynamic content (issues/workflows) MUST appear before static instructions."""
        # With issues
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
        issue_pos = result.find("ISSUE DETECTED")
        static_pos = result.find("DeepWork Workflow Server")
        assert issue_pos < static_pos, "Issue warning must appear before static instructions"

        # With workflows
        result_wf = _build_startup_instructions(tmp_path, issues=[])
        wf_pos = result_wf.find("Available Workflows")
        static_pos_wf = result_wf.find("DeepWork Workflow Server")
        assert wf_pos < static_pos_wf, "Workflow list must appear before static instructions"
