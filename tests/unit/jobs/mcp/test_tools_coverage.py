"""Additional tests for MCP workflow tools to cover edge cases and error paths.

Validates requirements: JOBS-REQ-001.8, JOBS-REQ-001.9, JOBS-REQ-010.3.1, JOBS-REQ-010.3.2,
JOBS-REQ-010.12.1, JOBS-REQ-010.12.3.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from deepwork.jobs.mcp.schemas import (
    FinishedStepInput,
    GoToStepInput,
    StartWorkflowInput,
    StartWorkflowResponse,
)
from deepwork.jobs.mcp.state import StateError, StateManager
from deepwork.jobs.mcp.tools import ToolError, WorkflowTools

SESSION_ID = "test-session-cov"


@pytest.fixture(autouse=True)
def _isolate_job_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from picking up real standard_jobs from the package."""
    monkeypatch.setattr(
        "deepwork.jobs.discovery.get_job_folders",
        lambda project_root: [project_root / ".deepwork" / "jobs"],
    )


def _create_job_dir(project_root: Path, job_yml: str, job_name: str = "test_job") -> None:
    """Helper to create a job directory with given YAML."""
    jobs_dir = project_root / ".deepwork" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_dir = jobs_dir / job_name
    job_dir.mkdir(exist_ok=True)
    (job_dir / "job.yml").write_text(job_yml)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()
    jobs_dir = deepwork_dir / "jobs"
    jobs_dir.mkdir()

    job_dir = jobs_dir / "test_job"
    job_dir.mkdir()

    job_yml = """\
name: test_job
summary: A test job

step_arguments:
  - name: output1
    description: "First output file"
    type: file_path
  - name: output2
    description: "Second output file"
    type: file_path
  - name: string_output
    description: "A string output"
    type: string
  - name: input1
    description: "An input value"
    type: string

workflows:
  main:
    summary: "Main workflow"
    common_job_info_provided_to_all_steps_at_runtime: |
      This is a test job
    post_workflow_instructions: |
      Create a PR.
    steps:
      - name: step1
        instructions: |
          Do the first step.
        inputs:
          input1:
            required: true
        outputs:
          output1:
            required: true
      - name: step2
        instructions: |
          Do the second step.
        inputs:
          output1:
            required: true
        outputs:
          output2:
            required: true
  single_step:
    summary: "Single step workflow"
    steps:
      - name: only_step
        instructions: |
          The only step.
        outputs:
          string_output:
            required: true
  delegated:
    summary: "A workflow for sub-agents"
    agent: "research"
    steps:
      - name: research_step
        instructions: |
          Do some research.
        outputs:
          string_output:
            required: true
  with_sub_workflow:
    summary: "Workflow with a sub-workflow step"
    steps:
      - name: delegate_step
        sub_workflow:
          workflow_name: single_step
        outputs:
          string_output:
            required: true
  cross_job_sub:
    summary: "Workflow referencing another job's workflow"
    steps:
      - name: cross_step
        sub_workflow:
          workflow_name: single_step
          workflow_job: other_job
        outputs:
          string_output:
            required: true
"""
    (job_dir / "job.yml").write_text(job_yml)

    return tmp_path


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    return StateManager(project_root, platform="test")


@pytest.fixture
def tools(project_root: Path, state_manager: StateManager) -> WorkflowTools:
    return WorkflowTools(project_root, state_manager)


# =========================================================================
# Helpers
# =========================================================================


async def _start_workflow(
    tools: WorkflowTools,
    workflow_name: str = "main",
    session_id: str = SESSION_ID,
    goal: str = "Test goal",
    inputs: dict | None = None,
) -> StartWorkflowResponse:
    inp = StartWorkflowInput(
        goal=goal,
        job_name="test_job",
        workflow_name=workflow_name,
        session_id=session_id,
        inputs=inputs,
    )
    return await tools.start_workflow(inp)


# =========================================================================
# TestStatusWriterIntegration
# =========================================================================


class TestStatusWriterIntegration:
    """Tests for _write_session_status and _write_manifest error handling."""

    async def test_write_session_status_swallows_exception(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """_write_session_status logs and swallows exceptions."""
        mock_writer = MagicMock()
        mock_writer.write_session_status.side_effect = RuntimeError("status write failed")

        tools = WorkflowTools(project_root, state_manager, status_writer=mock_writer)
        # Should not raise
        tools._write_session_status(SESSION_ID)
        mock_writer.write_session_status.assert_called_once()

    def test_write_manifest_swallows_exception(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """_write_manifest logs and swallows exceptions."""
        mock_writer = MagicMock()
        mock_writer.write_manifest.side_effect = RuntimeError("manifest write failed")

        tools = WorkflowTools(project_root, state_manager, status_writer=mock_writer)
        # Should not raise
        tools._write_manifest()
        mock_writer.write_manifest.assert_called_once()

    async def test_get_workflows_writes_manifest(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """get_workflows calls write_manifest on status_writer."""
        mock_writer = MagicMock()
        tools = WorkflowTools(project_root, state_manager, status_writer=mock_writer)

        tools.get_workflows()
        mock_writer.write_manifest.assert_called_once()

    async def test_get_workflows_handles_manifest_failure(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """get_workflows continues if write_manifest fails."""
        mock_writer = MagicMock()
        mock_writer.write_manifest.side_effect = RuntimeError("fail")

        tools = WorkflowTools(project_root, state_manager, status_writer=mock_writer)
        # Should not raise, returns valid response
        resp = tools.get_workflows()
        assert len(resp.jobs) == 1


# =========================================================================
# TestGetJobParsing
# =========================================================================


class TestGetJobParsing:
    """Tests for _get_job error handling."""

    def test_raises_on_parse_error(self, project_root: Path, state_manager: StateManager) -> None:
        """_get_job wraps ParseError into ToolError."""
        # Overwrite job.yml with invalid content
        job_file = project_root / ".deepwork" / "jobs" / "test_job" / "job.yml"
        job_file.write_text("name: test_job\nsummary: bad\nworkflows: not_a_dict")

        tools = WorkflowTools(project_root, state_manager)
        with pytest.raises(ToolError, match="Failed to parse"):
            tools._get_job("test_job")


# =========================================================================
# TestGetWorkflowAutoSelect
# =========================================================================


class TestGetWorkflowAutoSelect:
    """Tests for _get_workflow auto-selection."""

    def test_auto_selects_single_workflow(
        self, tmp_path: Path, state_manager: StateManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When a job has only one workflow, auto-select it even with wrong name."""
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda project_root: [project_root / ".deepwork" / "jobs"],
        )

        # Create a job with a single workflow
        _create_job_dir(
            tmp_path,
            """\
name: single_wf_job
summary: Job with one workflow

step_arguments:
  - name: out
    description: "output"
    type: string

workflows:
  only_wf:
    summary: "The only workflow"
    steps:
      - name: step1
        instructions: Do it.
        outputs:
          out:
            required: true
""",
            job_name="single_wf_job",
        )

        tools = WorkflowTools(tmp_path, state_manager)
        job = tools._get_job("single_wf_job")
        # Passing wrong name should auto-select since there's only one workflow
        wf = tools._get_workflow(job, "wrong_name")
        assert wf.name == "only_wf"

    def test_raises_when_multiple_workflows_and_wrong_name(self, tools: WorkflowTools) -> None:
        """_get_workflow raises ToolError when multiple workflows and name doesn't match."""
        job = tools._get_job("test_job")
        with pytest.raises(ToolError, match="not found"):
            tools._get_workflow(job, "nonexistent_workflow")


# =========================================================================
# TestValidateOutputsEdgeCases
# =========================================================================


class TestValidateOutputsEdgeCases:
    """Tests for _validate_outputs edge cases.

    These call _validate_outputs directly because Pydantic's type validation
    on FinishedStepInput prevents invalid types from reaching the method.
    In practice, these paths are hit when MCP transports send untyped JSON.
    """

    def test_file_path_list_with_non_string(self, tools: WorkflowTools) -> None:
        """file_path list with non-string elements raises ToolError."""
        job = tools._get_job("test_job")
        wf = tools._get_workflow(job, "main")
        step = wf.steps[0]  # step1 has output1 (file_path)

        with pytest.raises(ToolError, match="all paths must be strings"):
            tools._validate_outputs({"output1": [123, "valid.md"]}, step, job)

    def test_file_path_wrong_type(self, tools: WorkflowTools) -> None:
        """file_path with non-string/non-list type raises ToolError."""
        job = tools._get_job("test_job")
        wf = tools._get_workflow(job, "main")
        step = wf.steps[0]

        with pytest.raises(ToolError, match="must be a string path or list"):
            tools._validate_outputs({"output1": 42}, step, job)


# =========================================================================
# TestBuildStepInstructions
# =========================================================================


class TestBuildStepInstructions:
    """Tests for _build_step_instructions with various input scenarios."""

    async def test_input_not_yet_available(self, tools: WorkflowTools) -> None:
        """Input with no value shows 'not yet available'."""
        await _start_workflow(tools, inputs=None)

        # step1 expects input1 but we didn't provide it
        resp = await _start_workflow(tools, session_id="session2", inputs=None)
        step = resp.begin_step
        # input1 is required but not provided, should show "not yet available"
        assert "not yet available" in step.step_instructions

    async def test_sub_workflow_step_instructions(self, tools: WorkflowTools) -> None:
        """Sub-workflow step generates delegation instructions."""
        resp = await _start_workflow(
            tools, workflow_name="with_sub_workflow", session_id="sub-wf-session"
        )
        step = resp.begin_step
        assert step.step_id == "delegate_step"
        assert "start_workflow" in step.step_instructions
        assert "single_step" in step.step_instructions

    async def test_cross_job_sub_workflow_instructions(self, tools: WorkflowTools) -> None:
        """Cross-job sub-workflow step references the correct job name."""
        resp = await _start_workflow(
            tools, workflow_name="cross_job_sub", session_id="cross-session"
        )
        step = resp.begin_step
        assert step.step_id == "cross_step"
        assert "other_job" in step.step_instructions

    async def test_file_path_input_list_display(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """File path input as list is displayed with backticks."""
        # Start main workflow with a list input
        out1 = project_root / "a.md"
        out2 = project_root / "b.md"
        out1.write_text("a")
        out2.write_text("b")

        await _start_workflow(tools)
        # Complete step1 with a file path output
        inp = FinishedStepInput(
            outputs={"output1": ["a.md", "b.md"]},
            quality_review_override_reason="skip",
            session_id=SESSION_ID,
        )
        resp2 = await tools.finished_step(inp)
        # step2 receives output1 as input - check it's displayed
        assert resp2.begin_step is not None
        assert resp2.begin_step.step_id == "step2"
        # The instructions should contain the paths
        assert "`a.md`" in resp2.begin_step.step_instructions
        assert "`b.md`" in resp2.begin_step.step_instructions


# =========================================================================
# TestGoToStepNoSession
# =========================================================================


class TestGoToStepNoSession:
    """Tests for go_to_step when no session exists."""

    async def test_go_to_step_no_active_session(self, tools: WorkflowTools) -> None:
        """go_to_step raises StateError when no session exists."""
        inp = GoToStepInput(step_id="step1", session_id=SESSION_ID)
        with pytest.raises(StateError, match="No active workflow session"):
            await tools.go_to_step(inp)


# =========================================================================
# TestResolveInputValues
# =========================================================================


class TestResolveInputValues:
    """Tests for _resolve_input_values edge cases."""

    async def test_provided_inputs_override_previous_outputs(self, tools: WorkflowTools) -> None:
        """Provided inputs take priority over previous step outputs."""
        resp = await _start_workflow(tools, inputs={"input1": "provided_value"})
        # input1 should be resolved from provided inputs
        step = resp.begin_step
        input_info = next((i for i in step.step_inputs if i.name == "input1"), None)
        assert input_info is not None
        assert input_info.value == "provided_value"

    async def test_falls_back_to_previous_outputs(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Input values are resolved from previous step outputs when not provided."""
        await _start_workflow(tools)

        out1 = project_root / "out1.md"
        out1.write_text("content")

        # Complete step1 with output1
        inp = FinishedStepInput(
            outputs={"output1": "out1.md"},
            quality_review_override_reason="skip",
            session_id=SESSION_ID,
        )
        resp = await tools.finished_step(inp)

        # step2 should have output1 as input resolved from previous outputs
        assert resp.begin_step is not None
        input_info = next((i for i in resp.begin_step.step_inputs if i.name == "output1"), None)
        assert input_info is not None
        assert input_info.value == "out1.md"
