"""Tests that template examples and library jobs conform to the job schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from deepwork.jobs.schema import JOB_SCHEMA
from deepwork.utils.validation import validate_against_schema
from deepwork.utils.yaml_utils import load_yaml

# Paths relative to the repo root
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "src" / "deepwork" / "standard_jobs" / "deepwork_jobs" / "templates"
_LIBRARY_DIR = _REPO_ROOT / "library" / "jobs"


class TestTemplateSchemaCompliance:
    """Template example files must validate against the job schema."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.14.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.parametrize(
        "example_file",
        sorted(_TEMPLATES_DIR.glob("job.yml.example*")),
        ids=lambda p: p.name,
    )
    def test_template_example_matches_schema(self, example_file: Path) -> None:
        """Each job.yml.example file must validate against the job schema."""
        data = load_yaml(example_file)
        assert data is not None, f"{example_file.name} is empty"
        validate_against_schema(data, JOB_SCHEMA)


class TestLibraryJobSchemaCompliance:
    """All library jobs must validate against the job schema."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.14.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.parametrize(
        "job_yml",
        sorted(_LIBRARY_DIR.glob("*/job.yml")),
        ids=lambda p: p.parent.name,
    )
    def test_library_job_matches_schema(self, job_yml: Path) -> None:
        """Each library job.yml must validate against the job schema."""
        data = load_yaml(job_yml)
        assert data is not None, f"{job_yml} is empty"
        validate_against_schema(data, JOB_SCHEMA)
