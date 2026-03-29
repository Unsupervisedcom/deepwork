"""Issue detection for DeepWork job definitions.

Standalone module that identifies problems with installed jobs.
Other agent implementations can import this independently of the MCP layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deepwork.jobs.discovery import load_all_jobs


@dataclass
class Issue:
    """A detected issue with a job definition."""

    severity: str  # "error" | "warning"
    job_name: str
    job_dir: str
    message: str
    suggestion: str


def detect_issues(project_root: Path) -> list[Issue]:
    """Detect issues with job definitions.

    Currently detects:
    - job.yml files that don't conform to the schema

    Returns empty list if all is well.
    """
    _, load_errors = load_all_jobs(project_root)
    issues: list[Issue] = []

    for e in load_errors:
        issues.append(
            Issue(
                severity="error",
                job_name=e.job_name,
                job_dir=e.job_dir,
                message=e.error,
                suggestion=(
                    f"The invalid file is {e.job_dir}/job.yml. "
                    f"If you edited that file this session, fix it directly. "
                    f"If you did not edit it, the project may need "
                    f"`/deepwork repair` to migrate legacy formats."
                ),
            )
        )

    return issues


def format_issues_for_agent(issues: list[Issue]) -> str:
    """Format issues into a string suitable for agent instructions."""
    parts: list[str] = []
    for issue in issues:
        parts.append(f"- **{issue.job_name}**: {issue.message}\n  {issue.suggestion}")
    return "\n".join(parts)
