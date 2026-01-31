"""XDG Base Directory utilities for global job storage."""

import os
from pathlib import Path


def get_xdg_config_home() -> Path:
    """
    Get the XDG config home directory.

    Returns the value of $XDG_CONFIG_HOME if set, otherwise defaults to
    ~/.config according to XDG Base Directory specification.

    Returns:
        Path to the XDG config home directory
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config)
    return Path.home() / ".config"


def get_global_jobs_dir() -> Path:
    """
    Get the global jobs directory for DeepWork.

    Global jobs are stored in $XDG_CONFIG_HOME/deepwork/jobs/
    (typically ~/.config/deepwork/jobs/)

    Returns:
        Path to the global jobs directory
    """
    return get_xdg_config_home() / "deepwork" / "jobs"


def ensure_global_jobs_dir() -> Path:
    """
    Ensure the global jobs directory exists.

    Creates the directory if it doesn't exist and returns its path.

    Returns:
        Path to the global jobs directory
    """
    global_jobs_dir = get_global_jobs_dir()
    global_jobs_dir.mkdir(parents=True, exist_ok=True)
    return global_jobs_dir
