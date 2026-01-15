"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_git_repo(temp_dir: Path) -> Path:
    """Create a mock Git repository for testing."""
    repo = Repo.init(temp_dir)
    # Create initial commit to have a valid Git repo
    (temp_dir / "README.md").write_text("# Test Repository\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    return temp_dir


@pytest.fixture
def mock_claude_project(mock_git_repo: Path) -> Path:
    """Create a mock project with Claude Code setup."""
    claude_dir = mock_git_repo / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "settings.json").write_text('{"version": "1.0"}')
    return mock_git_repo


@pytest.fixture
def mock_gemini_project(mock_git_repo: Path) -> Path:
    """Create a mock project with Gemini CLI setup."""
    gemini_dir = mock_git_repo / ".gemini"
    gemini_dir.mkdir(exist_ok=True)
    return mock_git_repo


@pytest.fixture
def mock_multi_platform_project(mock_git_repo: Path) -> Path:
    """Create a mock project with multiple AI platforms setup."""
    claude_dir = mock_git_repo / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "settings.json").write_text('{"version": "1.0"}')

    gemini_dir = mock_git_repo / ".gemini"
    gemini_dir.mkdir(exist_ok=True)
    return mock_git_repo


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_job_fixture(fixtures_dir: Path) -> Path:
    """Return the path to the simple job fixture."""
    return fixtures_dir / "jobs" / "simple_job" / "job.yml"


@pytest.fixture
def complex_job_fixture(fixtures_dir: Path) -> Path:
    """Return the path to the complex job fixture."""
    return fixtures_dir / "jobs" / "complex_job" / "job.yml"


@pytest.fixture
def invalid_job_fixture(fixtures_dir: Path) -> Path:
    """Return the path to the invalid job fixture."""
    return fixtures_dir / "jobs" / "invalid_job" / "job.yml"
