"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from git import Repo


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Disable coverage fail-under when running a subset of tests.

    ## How coverage enforcement works in this project

    Coverage is configured in three places that interact:

    1. **pyproject.toml [tool.pytest.ini_options].addopts** — sets
       ``--cov=deepwork --cov-branch --cov-report=term-missing --cov-fail-under=98``.
       These flags are injected into every pytest invocation via addopts.

    2. **pyproject.toml [tool.coverage.report]** — configures coverage.py's
       report format (precision, show_missing, skip_covered). The ``fail_under``
       setting is intentionally NOT set here; it is only controlled via the
       pytest-cov ``--cov-fail-under`` flag so that this hook can override it.

    3. **This hook (tests/conftest.py)** — detects targeted runs (e.g.
       ``pytest tests/unit/test_git.py``) and disables the fail-under threshold
       so that running a subset of tests still shows the coverage report but
       doesn't fail because only a fraction of the codebase was exercised.

    ### Why we need to set BOTH config.option AND cov.options

    pytest-cov creates its ``CovPlugin`` during ``pytest_load_initial_conftests``
    (very early, before conftest ``pytest_configure`` hooks run). The plugin
    stores ``self.options = early_config.known_args_namespace``, which SHOULD
    be the same object as ``config.option`` — but in practice, overriding
    ``config.option.cov_fail_under`` alone does not reliably propagate to the
    plugin's copy. Directly setting ``cov.options.cov_fail_under`` on the
    registered ``_cov`` plugin ensures the value is updated where pytest-cov
    reads it during ``pytest_terminal_summary`` (the "Required test coverage"
    message) and ``pytest_sessionfinish`` (the "Coverage failure" exit code).
    """
    testpaths = config.getini("testpaths")
    is_targeted = config.args != testpaths or config.option.keyword
    if is_targeted:
        config.option.cov_fail_under = 0
        cov = config.pluginmanager.get_plugin("_cov")
        if cov:
            cov.options.cov_fail_under = 0


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


@pytest.fixture
def without_standard_schemas() -> Iterator[None]:
    """Patch out built-in standard schemas so tests only see schemas they create.

    Use this in any test that needs a clean schema environment without the
    standard schemas shipped with DeepWork interfering with assertions.
    """
    with patch(
        "deepwork.deepschema.discovery._STANDARD_SCHEMAS_DIR",
        Path("/nonexistent/no_standard_schemas"),
    ):
        yield
