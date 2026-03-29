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

    def test_handles_binary_content(self, tmp_path: Path) -> None:
        """Binary/non-UTF-8 job.yml is detected as an issue, not a crash."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "binary_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_bytes(b"\x00\x01\x02\xff\xfe")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "binary_job"
        assert issues[0].severity == "error"

    def test_handles_empty_job_yml(self, tmp_path: Path) -> None:
        """Empty job.yml is detected as an issue."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "empty_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "empty_job"

    def test_handles_malformed_yaml(self, tmp_path: Path) -> None:
        """Malformed YAML (unclosed braces) is detected as an issue."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "malformed"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("{{{{not valid yaml")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "malformed"

    def test_handles_non_dict_yaml(self, tmp_path: Path) -> None:
        """YAML that parses to a list instead of dict is detected as an issue."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "list_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("- item1\n- item2\n")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "list_job"

    def test_handles_latin1_encoded_file(self, tmp_path: Path) -> None:
        """Latin-1 encoded file with non-UTF-8 bytes is detected as an issue."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)
        job_dir = jobs_dir / "latin1_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_bytes("name: caf\xe9\n".encode("latin-1"))

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "latin1_job"

    def test_good_and_bad_jobs_together(self, tmp_path: Path) -> None:
        """Good jobs are not reported; only bad ones produce issues."""
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        jobs_dir.mkdir(parents=True)

        # Good job
        good = jobs_dir / "good_job"
        good.mkdir()
        (good / "job.yml").write_text(
            yaml.dump(
                {
                    "name": "good_job",
                    "summary": "Works",
                    "step_arguments": [
                        {"name": "out", "description": "Out", "type": "file_path"}
                    ],
                    "workflows": {
                        "main": {
                            "summary": "Main",
                            "steps": [
                                {
                                    "name": "do_it",
                                    "instructions": "Do it.",
                                    "outputs": {"out": {"required": True}},
                                }
                            ],
                        }
                    },
                }
            )
        )

        # Binary-corrupted job
        bad = jobs_dir / "corrupted"
        bad.mkdir()
        (bad / "job.yml").write_bytes(b"\xff\xfe\x00\x01")

        issues = detect_issues(tmp_path)
        assert len(issues) == 1
        assert issues[0].job_name == "corrupted"


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
