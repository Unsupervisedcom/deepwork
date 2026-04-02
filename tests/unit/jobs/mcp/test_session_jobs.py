"""Tests for session job registration and retrieval MCP tools."""

from pathlib import Path

import pytest

from deepwork.jobs.mcp.schemas import (
    GetSessionJobInput,
    RegisterSessionJobInput,
    StartWorkflowInput,
    StepStatus,
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
    @pytest.mark.anyio
    async def test_register_valid_job(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        result = await tools.register_session_job(inp)
        assert result["status"] == "registered"
        assert result["job_name"] == "my_plan"

    @pytest.mark.anyio
    async def test_register_invalid_yaml_syntax(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="bad",
            job_definition_yaml=BAD_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="Invalid YAML syntax"):
            await tools.register_session_job(inp)

    @pytest.mark.anyio
    async def test_register_invalid_schema(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="my_plan",
            job_definition_yaml=INVALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="validation failed"):
            await tools.register_session_job(inp)

    @pytest.mark.anyio
    async def test_register_invalid_job_name(self, tools: WorkflowTools) -> None:
        inp = RegisterSessionJobInput(
            job_name="Bad-Name",
            job_definition_yaml=VALID_JOB_YAML,
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="Invalid job name"):
            await tools.register_session_job(inp)

    @pytest.mark.anyio
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
    @pytest.mark.anyio
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

    @pytest.mark.anyio
    async def test_get_nonexistent_job(self, tools: WorkflowTools) -> None:
        get_inp = GetSessionJobInput(job_name="nonexistent", session_id=SESSION_ID)
        with pytest.raises(ToolError, match="not found"):
            await tools.get_session_job(get_inp)


class TestSessionJobDiscovery:
    @pytest.mark.anyio
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

    @pytest.mark.anyio
    async def test_session_job_isolated_by_session_id(
        self, tools: WorkflowTools
    ) -> None:
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
