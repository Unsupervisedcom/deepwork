"""Tests for the deepplan standard job definition and integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from deepwork.jobs.parser import parse_job_definition
from deepwork.jobs.schema import JOB_SCHEMA
from deepwork.utils.validation import validate_against_schema
from deepwork.utils.yaml_utils import load_yaml

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEEPPLAN_DIR = _REPO_ROOT / "src" / "deepwork" / "standard_jobs" / "deepplan"
_STARTUP_HOOK = _REPO_ROOT / "plugins" / "claude" / "hooks" / "startup_context.sh"


class TestDeepplanJobDefinition:
    """Validate the deepplan standard job definition."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_job_location(self) -> None:
        """deepplan job exists at src/deepwork/standard_jobs/deepplan/."""
        assert _DEEPPLAN_DIR.is_dir()
        assert (_DEEPPLAN_DIR / "job.yml").is_file()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.1.3, JOBS-REQ-014.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_job_parses_successfully(self) -> None:
        """deepplan job.yml passes parse_job_definition and has correct name."""
        job = parse_job_definition(_DEEPPLAN_DIR)
        assert job.name == "deepplan"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_job_validates_against_schema(self) -> None:
        """deepplan job.yml validates against the job schema."""
        data = load_yaml(_DEEPPLAN_DIR / "job.yml")
        assert data is not None
        validate_against_schema(data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.2.1, JOBS-REQ-014.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_workflow_structure(self) -> None:
        """create_deep_plan workflow has exactly 5 steps in correct order."""
        job = parse_job_definition(_DEEPPLAN_DIR)
        assert "create_deep_plan" in job.workflows
        workflow = job.workflows["create_deep_plan"]
        step_names = [s.name for s in workflow.steps]
        assert step_names == [
            "initial_understanding",
            "design_alternatives",
            "review_and_synthesize",
            "enrich_the_plan",
            "present_plan",
        ]

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_common_job_info(self) -> None:
        """Workflow defines common_job_info superseding default planning."""
        job = parse_job_definition(_DEEPPLAN_DIR)
        workflow = job.workflows["create_deep_plan"]
        assert workflow.common_job_info is not None
        assert "supersede" in workflow.common_job_info.lower()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_post_workflow_instructions(self) -> None:
        """Workflow defines post_workflow_instructions for starting session job."""
        job = parse_job_definition(_DEEPPLAN_DIR)
        workflow = job.workflows["create_deep_plan"]
        assert workflow.post_workflow_instructions is not None
        assert "start_workflow" in workflow.post_workflow_instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.3.1, JOBS-REQ-014.3.2, JOBS-REQ-014.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_required_step_arguments(self) -> None:
        """Job defines required step arguments with correct types."""
        job = parse_job_definition(_DEEPPLAN_DIR)
        args_by_name = {a.name: a for a in job.step_arguments}
        assert "original_user_request" in args_by_name
        assert args_by_name["original_user_request"].type == "string"
        assert "draft_plan_file" in args_by_name
        assert args_by_name["draft_plan_file"].type == "file_path"
        assert "session_job_name" in args_by_name
        assert args_by_name["session_job_name"].type == "string"


class TestDeepplanStartupHook:
    """Validate the startup context hook injects DeepPlan trigger."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-014.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_startup_hook_contains_deepplan_trigger(self) -> None:
        """startup_context.sh injects an instruction to start create_deep_plan."""
        content = _STARTUP_HOOK.read_text(encoding="utf-8")
        assert "create_deep_plan" in content
        assert "deepplan" in content
        assert "start_workflow" in content

    @pytest.mark.skipif(
        not _STARTUP_HOOK.exists(),
        reason="startup_context.sh not found",
    )
    def test_startup_hook_is_executable(self) -> None:
        """startup_context.sh has execute permission."""
        import os

        assert os.access(_STARTUP_HOOK, os.X_OK)
