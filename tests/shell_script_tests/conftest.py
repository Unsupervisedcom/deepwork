"""Shared fixtures for shell script tests."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a basic git repo for testing."""
    repo = Repo.init(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return tmp_path


@pytest.fixture
def hooks_dir() -> Path:
    """Return the path to the main hooks directory (platform wrappers)."""
    return Path(__file__).parent.parent.parent / "src" / "deepwork" / "hooks"


@pytest.fixture
def src_dir() -> Path:
    """Return the path to the src directory for PYTHONPATH."""
    return Path(__file__).parent.parent.parent / "src"


@pytest.fixture
def jobs_scripts_dir() -> Path:
    """Return the path to the jobs scripts directory."""
    return (
        Path(__file__).parent.parent.parent / "src" / "deepwork" / "standard_jobs" / "deepwork_jobs"
    )


def run_shell_script(
    script_path: Path,
    cwd: Path,
    args: list[str] | None = None,
    hook_input: dict | None = None,
    env_extra: dict[str, str] | None = None,
) -> tuple[str, str, int]:
    """
    Run a shell script and return its output.

    Args:
        script_path: Path to the shell script
        cwd: Working directory to run the script in
        args: Optional list of arguments to pass to the script
        hook_input: Optional JSON input to pass via stdin
        env_extra: Optional extra environment variables

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")
    if env_extra:
        env.update(env_extra)

    cmd = ["bash", str(script_path)]
    if args:
        cmd.extend(args)

    stdin_data = json.dumps(hook_input) if hook_input else ""

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=stdin_data,
        env=env,
    )

    return result.stdout, result.stderr, result.returncode
