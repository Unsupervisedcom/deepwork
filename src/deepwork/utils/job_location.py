"""Job location and discovery utilities."""

from enum import Enum
from pathlib import Path

from deepwork.utils.xdg import get_global_jobs_dir


class JobScope(Enum):
    """Scope for job installation."""

    LOCAL = "local"
    GLOBAL = "global"


def get_jobs_dir(project_path: Path, scope: JobScope) -> Path:
    """
    Get the jobs directory for the specified scope.

    Args:
        project_path: Path to the project root (used for LOCAL scope)
        scope: JobScope indicating where jobs should be stored

    Returns:
        Path to the jobs directory
    """
    if scope == JobScope.LOCAL:
        return project_path / ".deepwork" / "jobs"
    else:  # JobScope.GLOBAL
        return get_global_jobs_dir()


def discover_all_jobs_dirs(project_path: Path) -> list[tuple[JobScope, Path]]:
    """
    Discover all available job directories (both local and global).

    Returns a list of tuples (scope, path) for all job directories that exist.
    Local jobs are listed first, followed by global jobs.

    Args:
        project_path: Path to the project root

    Returns:
        List of (JobScope, Path) tuples for existing job directories
    """
    result: list[tuple[JobScope, Path]] = []

    # Check local jobs first
    local_jobs_dir = get_jobs_dir(project_path, JobScope.LOCAL)
    if local_jobs_dir.exists():
        result.append((JobScope.LOCAL, local_jobs_dir))

    # Check global jobs
    global_jobs_dir = get_jobs_dir(project_path, JobScope.GLOBAL)
    if global_jobs_dir.exists():
        result.append((JobScope.GLOBAL, global_jobs_dir))

    return result


def find_job(job_name: str, project_path: Path) -> tuple[JobScope, Path] | None:
    """
    Find a job by name, searching local first, then global.

    Args:
        job_name: Name of the job to find
        project_path: Path to the project root

    Returns:
        Tuple of (scope, job_path) if found, None otherwise
    """
    for scope, jobs_dir in discover_all_jobs_dirs(project_path):
        job_path = jobs_dir / job_name
        if job_path.exists() and (job_path / "job.yml").exists():
            return (scope, job_path)

    return None
