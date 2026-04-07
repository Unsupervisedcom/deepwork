"""Tests for session job registration and retrieval MCP tools.

Validates requirements: JOBS-REQ-013, JOBS-REQ-013.1, JOBS-REQ-013.2, JOBS-REQ-013.3,
JOBS-REQ-013.4, JOBS-REQ-013.5.
"""

from pathlib import Path

import pytest

from deepwork.jobs.mcp.schemas import (
    FinishedStepInput,
    GetSessionJobInput,
    RegisterSessionJobInput,
    StartWorkflowInput,
)
from deepwork.jobs.mcp.state import StateManager
from deepwork.jobs.mcp.tools import ToolError, WorkflowTools

SESSION_ID = "test-session"

VALID_JOB_YAML = """\
name: my_plan
summary: "A test plan job"

step_arguments:
  - name: result
    description: "The result"
    type: string

workflows:
  main:
    summary: "Execute the plan"
    steps:
      - name: do_work
        instructions: |
          Do the work.
        outputs:
          result:
            required: true
"""

INVALID_JOB_YAML = """\
name: my_plan
summary: "Missing step_arguments and workflows"
"""

BAD_YAML = "{{{{not valid yaml"


@pytest.fixture(autouse=True)
def _isolate_job_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from picking up real standard_jobs."""
    monkeypatch.setattr(
        "deepwork.jobs.discovery.get_job_folders",
        lambda project_root: [project_root / ".deepwork" / "jobs"],
    )


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()
    (deepwork_dir / "jobs").mkdir()
    return tmp_path


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    return StateManager(project_root, platform="test")


@pytest.fixture
def tools(project_root: Path, state_manager: StateManager) -> WorkflowTools:
    return WorkflowTools(project_root, state_manager)


class TestRegisterSessionJob:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.1.1, JOBS-REQ-013.1.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_register_valid_job(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        result = await tools.register_session_job(inp)
        assert result["status"] == "registered"
        assert result["job_name"] == "my_plan"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.1.4, JOBS-REQ-013.1.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_register_invalid_yaml_syntax(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="bad",
            job_definition_yaml=BAD_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="Invalid YAML syntax"):
            await tools.register_session_job(inp)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.1.6, JOBS-REQ-013.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_register_invalid_schema(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=INVALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="validation failed"):
            await tools.register_session_job(inp)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.1.2, JOBS-REQ-013.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_register_invalid_job_name(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="Bad-Name",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="Invalid job name"):
            await tools.register_session_job(inp)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.1.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_register_overwrites(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        await tools.register_session_job(inp)

        updated_yaml = VALID_JOB_YAML.replace("A test plan job", "Updated plan")
        inp2 = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=updated_yaml,
            session_id=SESSION_ID,
        )
        result = await tools.register_session_job(inp2)
        assert result["status"] == "registered"

        # Verify overwritten content
        get_inp = GetSessionJobInput(job_name="my_plan", session_id=SESSION_ID)
        get_result = await tools.get_session_job(get_inp)
        assert "Updated plan" in get_result["job_definition_yaml"]


class TestGetSessionJob:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.3.1, JOBS-REQ-013.3.2, JOBS-REQ-013.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_get_registered_job(self, tools: WorkflowTools) -> None:
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        await tools.register_session_job(reg_inp)

        get_inp = GetSessionJobInput(job_name="my_plan", session_id=SESSION_ID)
        result = await tools.get_session_job(get_inp)
        assert result["job_name"] == "my_plan"
        assert "my_plan" in result["job_definition_yaml"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, tools: WorkflowTools) -> None:
        get_inp = GetSessionJobInput(job_name="nonexistent", session_id=SESSION_ID)
        with pytest.raises(ToolError, match="not found"):
            await tools.get_session_job(get_inp)


class TestSessionJobDiscovery:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_start_workflow_finds_session_job(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Session jobs should be discoverable by start_workflow."""
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        await tools.register_session_job(reg_inp)

        start_inp = StartWorkflowInput(
            goal="Execute the plan",
            job_name="my_plan",
            workflow_name="main",
            session_id=SESSION_ID,
        )
        response = await tools.start_workflow(start_inp)
        assert response.begin_step.step_id == "do_work"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_session_job_isolated_by_session_id(self, tools: WorkflowTools) -> None:
        """A session job registered under one session_id should not be found by another."""
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id="session-a",
        )
        await tools.register_session_job(reg_inp)

        start_inp = StartWorkflowInput(
            goal="Execute the plan",
            job_name="my_plan",
            workflow_name="main",
            session_id="session-b",
        )
        with pytest.raises(ToolError, match="Job not found"):
            await tools.start_workflow(start_inp)


class TestSessionJobStoragePath:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_storage_path_matches_spec(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Session job stored at .deepwork/tmp/sessions/<platform>/session-<id>/jobs/<name>/job.yml."""
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        result = await tools.register_session_job(reg_inp)

        expected = (
            project_root
            / ".deepwork"
            / "tmp"
            / "sessions"
            / "test"
            / f"session-{SESSION_ID}"
            / "jobs"
            / "my_plan"
        )
        assert Path(result["job_dir"]) == expected
        assert (expected / "job.yml").exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_session_job_takes_priority(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Session jobs take priority over project-local jobs with the same name."""
        # Create a project-local job with same name
        local_job_dir = project_root / ".deepwork" / "jobs" / "my_plan"
        local_job_dir.mkdir(parents=True)
        local_yaml = VALID_JOB_YAML.replace("A test plan job", "Local version")
        (local_job_dir / "job.yml").write_text(local_yaml, encoding="utf-8")

        # Register a session job with the same name
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        await tools.register_session_job(reg_inp)

        # start_workflow should find the session job, not the local one
        start_inp = StartWorkflowInput(
            goal="Execute",
            job_name="my_plan",
            workflow_name="main",
            session_id=SESSION_ID,
        )
        response = await tools.start_workflow(start_inp)
        assert response.begin_step.step_id == "do_work"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-013.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @pytest.mark.asyncio
    async def test_finished_step_resolves_session_job(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """finished_step resolves jobs from session directories."""
        reg_inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        await tools.register_session_job(reg_inp)

        # Start the workflow
        start_inp = StartWorkflowInput(
            goal="Execute",
            job_name="my_plan",
            workflow_name="main",
            session_id=SESSION_ID,
        )
        await tools.start_workflow(start_inp)

        # finished_step should resolve the session job
        finish_inp = FinishedStepInput(
            session_id=SESSION_ID,
            outputs={"result": "done"},
        )
        result = await tools.finished_step(finish_inp)
        assert result.status == "workflow_complete"
