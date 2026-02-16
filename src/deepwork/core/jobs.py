"""Job folder discovery for DeepWork.

Resolves the list of directories to scan for job definitions.  The default
search path is:

1. ``<project_root>/.deepwork/jobs`` – project-local (user-created) jobs
2. ``<package>/standard_jobs``       – built-in standard jobs shipped with DeepWork

Additional directories can be appended via the ``DEEPWORK_ADDITIONAL_JOBS_FOLDERS``
environment variable, which accepts a **colon-delimited** list of absolute paths.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from deepwork.core.parser import JobDefinition, ParseError, parse_job_definition

logger = logging.getLogger("deepwork.core.jobs")


@dataclass
class JobLoadError:
    """A job that failed to load."""

    job_name: str
    job_dir: str
    error: str


# Environment variable for additional job folders (colon-delimited)
ENV_ADDITIONAL_JOBS_FOLDERS = "DEEPWORK_ADDITIONAL_JOBS_FOLDERS"

# Location of built-in standard jobs inside the package
_STANDARD_JOBS_DIR = Path(__file__).parent.parent / "standard_jobs"


def get_job_folders(project_root: Path) -> list[Path]:
    """Return the ordered list of directories to scan for job definitions.

    The order determines priority when the same job name appears in multiple
    folders – the first directory that contains a matching job wins.

    Returns:
        List of directory paths (may include non-existent paths which callers
        should skip).
    """
    folders: list[Path] = [
        project_root / ".deepwork" / "jobs",
        _STANDARD_JOBS_DIR,
    ]

    extra = os.environ.get(ENV_ADDITIONAL_JOBS_FOLDERS, "")
    if extra:
        for entry in extra.split(":"):
            entry = entry.strip()
            if entry:
                folders.append(Path(entry))

    return folders


def load_all_jobs(
    project_root: Path,
) -> tuple[list[JobDefinition], list[JobLoadError]]:
    """Load all job definitions from all configured job folders.

    Jobs are discovered from each folder returned by :func:`get_job_folders`.
    If two folders contain a job with the same directory name, the one from the
    earlier folder wins (project-local overrides standard, etc.).

    Returns:
        Tuple of (successfully parsed jobs, errors for jobs that failed to load).
    """
    seen_names: set[str] = set()
    jobs: list[JobDefinition] = []
    errors: list[JobLoadError] = []

    for folder in get_job_folders(project_root):
        if not folder.exists() or not folder.is_dir():
            continue

        for job_dir in sorted(folder.iterdir()):
            if not job_dir.is_dir() or not (job_dir / "job.yml").exists():
                continue

            if job_dir.name in seen_names:
                continue

            try:
                job = parse_job_definition(job_dir)
                jobs.append(job)
                seen_names.add(job_dir.name)
            except ParseError as e:
                logger.warning("Skipping invalid job '%s': %s", job_dir.name, e)
                errors.append(
                    JobLoadError(
                        job_name=job_dir.name,
                        job_dir=str(job_dir),
                        error=str(e),
                    )
                )

    return jobs, errors


def find_job_dir(project_root: Path, job_name: str) -> Path | None:
    """Find the directory for a specific job by name across all job folders.

    Returns the first matching directory, or ``None`` if not found.
    """
    for folder in get_job_folders(project_root):
        if not folder.exists() or not folder.is_dir():
            continue
        candidate = folder / job_name
        if candidate.is_dir() and (candidate / "job.yml").exists():
            return candidate
    return None
