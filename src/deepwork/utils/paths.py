"""Utilities for managing local and global job paths."""

from pathlib import Path


def get_global_deepwork_dir() -> Path:
    """
    Get the global DeepWork directory path.

    Returns:
        Path to ~/.deepwork directory
    """
    return Path.home() / ".deepwork"


def get_global_jobs_dir() -> Path:
    """
    Get the global jobs directory path.

    Returns:
        Path to ~/.deepwork/jobs directory
    """
    return get_global_deepwork_dir() / "jobs"


def get_local_deepwork_dir(project_path: Path) -> Path:
    """
    Get the local DeepWork directory path for a project.

    Args:
        project_path: Path to project root

    Returns:
        Path to .deepwork directory in project
    """
    return project_path / ".deepwork"


def get_local_jobs_dir(project_path: Path) -> Path:
    """
    Get the local jobs directory path for a project.

    Args:
        project_path: Path to project root

    Returns:
        Path to .deepwork/jobs directory in project
    """
    return get_local_deepwork_dir(project_path) / "jobs"


def discover_all_jobs_dirs(project_path: Path) -> list[tuple[Path, str]]:
    """
    Discover all job directories from both local and global locations.

    Args:
        project_path: Path to project root

    Returns:
        List of tuples (job_dir_path, location_type) where location_type is "local" or "global"
    """
    job_dirs: list[tuple[Path, str]] = []

    # Check local jobs
    local_jobs = get_local_jobs_dir(project_path)
    if local_jobs.exists():
        for job_dir in local_jobs.iterdir():
            if job_dir.is_dir() and (job_dir / "job.yml").exists():
                job_dirs.append((job_dir, "local"))

    # Check global jobs
    global_jobs = get_global_jobs_dir()
    if global_jobs.exists():
        for job_dir in global_jobs.iterdir():
            if job_dir.is_dir() and (job_dir / "job.yml").exists():
                job_dirs.append((job_dir, "global"))

    return job_dirs


def is_job_global(job_path: Path) -> bool:
    """
    Check if a job is in the global location.

    Args:
        job_path: Path to job directory

    Returns:
        True if job is in global location, False otherwise
    """
    global_jobs = get_global_jobs_dir()
    try:
        job_path.relative_to(global_jobs)
        return True
    except ValueError:
        return False


def ensure_global_jobs_dir() -> Path:
    """
    Ensure the global jobs directory exists.

    Returns:
        Path to global jobs directory
    """
    global_jobs = get_global_jobs_dir()
    global_jobs.mkdir(parents=True, exist_ok=True)
    return global_jobs
