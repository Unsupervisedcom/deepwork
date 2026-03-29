"""Tests for deepwork.jobs.issues module."""

from __future__ import annotations

from pathlib import Path

import yaml

from deepwork.jobs.issues import Issue, detect_issues, format_issues_for_agent


class TestDetectIssues:
    """Tests for detect_issues()."""

    def test_returns_empty_when_no_issues(self, tmp_path: Path) -> None:
        """No issues when all jobs parse successfully."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "good_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text(
            yaml.dump(
                {
                    "name": "good_job",
                    "summary": "A working job",
                    "step_arguments": [
                        {"name": "output", "description": "Output", "type": "file_path"}
                    ],
                    "workflows": {
                        "main": {
                            "summary": "Main workflow",
                            "steps": [
                                {
                                    "name": "step_one",
                                    "instructions": "Do the thing.",
                                    "outputs": {"output": {"required": True}},
                                }
                            ],
                        }
                    },
                }
            )
        )

        issues = detect_issues(tmp_path)
        assert issues == []

    def test_returns_empty_when_no_jobs(self, tmp_path: Path) -> None:
        """No issues when no job directories exist."""
        issues = detect_issues(tmp_path)
        assert issues == []

    def test_detects_schema_error(self, tmp_path: Path) -> None:
        """Detects a job.yml that doesn't conform to the schema."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "broken_job"
        job_dir.mkdir()
        # Missing required fields
        (job_dir / "job.yml").write_text("name: broken_job\n")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "error"
        assert issue.job_name == "broken_job"
        assert "broken_job" in issue.job_dir
        assert "/deepwork repair" in issue.suggestion

    def test_detects_multiple_issues(self, tmp_path: Path) -> None:
        """Detects issues across multiple broken jobs."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        for name in ["bad_one", "bad_two"]:
            job_dir = jobs_dir / name
            job_dir.mkdir()
            (job_dir / "job.yml").write_text(f"name: {name}\n")

        issues = detect_issues(tmp_path)
        assert len(issues) == 2
        names = {i.job_name for i in issues}
        assert names == {"bad_one", "bad_two"}

    def test_suggestion_mentions_repair(self, tmp_path: Path) -> None:
        """The suggestion for schema errors mentions /deepwork repair."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "bad_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("name: bad_job\n")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert "/deepwork repair" in issues[0].suggestion
        assert "job.yml" in issues[0].suggestion


class TestFormatIssuesForAgent:
    """Tests for format_issues_for_agent()."""

    def test_formats_single_issue(self) -> None:
        issues = [
            Issue(
                severity="error",
                job_name="broken",
                job_dir="/path/to/broken",
                message="Missing required field",
                suggestion="Fix it",
            )
        ]
        result = format_issues_for_agent(issues)
        assert "**broken**" in result
        assert "Missing required field" in result
        assert "Fix it" in result

    def test_formats_multiple_issues(self) -> None:
        issues = [
            Issue(
                severity="error",
                job_name="a",
                job_dir="/a",
                message="Error A",
                suggestion="Fix A",
            ),
            Issue(
                severity="error",
                job_name="b",
                job_dir="/b",
                message="Error B",
                suggestion="Fix B",
            ),
        ]
        result = format_issues_for_agent(issues)
        assert "**a**" in result
        assert "**b**" in result
