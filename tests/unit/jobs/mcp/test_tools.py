"""Tests for MCP workflow tools."""

from pathlib import Path
from unittest.mock import patch

import pytest

from deepwork.jobs.mcp.schemas import (
    AbortWorkflowInput,
    FinishedStepInput,
    FinishedStepResponse,
    GoToStepInput,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepStatus,
)
from deepwork.jobs.mcp.state import StateManager
from deepwork.jobs.mcp.tools import ToolError, WorkflowTools

SESSION_ID = "test-session"


@pytest.fixture(autouse=True)
def _isolate_job_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from picking up real standard_jobs from the package.

    Each test gets only its own .deepwork/jobs/ directory.
    """
    monkeypatch.setattr(
        "deepwork.jobs.discovery.get_job_folders",
        lambda project_root: [project_root / ".deepwork" / "jobs"],
    )


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project with a test job using the new format."""
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

workflows:
  main:
    summary: "Main workflow"
    common_job_info_provided_to_all_steps_at_runtime: |
      This is a test job for unit tests
    post_workflow_instructions: |
      Remember to create a PR with your changes.
    steps:
      - name: step1
        instructions: |
          Do the first step.
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


async def _start_main_workflow(
    tools: WorkflowTools,
    session_id: str = SESSION_ID,
    goal: str = "Test goal",
) -> StartWorkflowResponse:
    """Start the main workflow and return the response."""
    inp = StartWorkflowInput(
        goal=goal,
        job_name="test_job",
        workflow_name="main",
        session_id=session_id,
    )
    return await tools.start_workflow(inp)


async def _finish_step(
    tools: WorkflowTools,
    outputs: dict,
    session_id: str = SESSION_ID,
    work_summary: str | None = None,
    override: str | None = None,
) -> FinishedStepResponse:
    """Complete the current step."""
    inp = FinishedStepInput(
        outputs=outputs,
        work_summary=work_summary,
        quality_review_override_reason=override,
        session_id=session_id,
    )
    return await tools.finished_step(inp)


# =========================================================================
# TestGetWorkflows
# =========================================================================


class TestGetWorkflows:
    """Tests for get_workflows tool."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_jobs(self, tools: WorkflowTools) -> None:
        resp = tools.get_workflows()
        assert len(resp.jobs) == 1
        job = resp.jobs[0]
        assert job.name == "test_job"
        assert job.summary == "A test job"
        assert len(job.workflows) == 2

        wf_names = {wf.name for wf in job.workflows}
        assert wf_names == {"main", "delegated"}

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.2.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_delegated_workflow_how_to_invoke(self, tools: WorkflowTools) -> None:
        resp = tools.get_workflows()
        job = resp.jobs[0]
        delegated = next(wf for wf in job.workflows if wf.name == "delegated")
        assert "subagent_type" in delegated.how_to_invoke
        assert "research" in delegated.how_to_invoke

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.2.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_main_workflow_how_to_invoke(self, tools: WorkflowTools) -> None:
        resp = tools.get_workflows()
        job = resp.jobs[0]
        main = next(wf for wf in job.workflows if wf.name == "main")
        assert "start_workflow" in main.how_to_invoke

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.2.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_handles_load_errors(self, tmp_path: Path, state_manager: StateManager) -> None:
        """Jobs with invalid YAML appear in errors, not jobs."""
        deepwork_dir = tmp_path / ".deepwork"
        jobs_dir = deepwork_dir / "jobs"

        bad_dir = jobs_dir / "bad_job"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "job.yml").write_text("not: valid: yaml: [")

        tools = WorkflowTools(tmp_path, state_manager)
        resp = tools.get_workflows()

        error_names = [e.job_name for e in resp.errors]
        assert "bad_job" in error_names


# =========================================================================
# TestStartWorkflow
# =========================================================================


class TestStartWorkflow:
    """Tests for start_workflow tool."""

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_creates_session_and_returns_first_step(self, tools: WorkflowTools) -> None:
        resp = await _start_main_workflow(tools)
        step = resp.begin_step

        assert step.session_id == SESSION_ID
        assert step.step_id == "step1"
        assert "Do the first step" in step.step_instructions
        assert len(step.step_expected_outputs) == 1
        assert step.step_expected_outputs[0].name == "output1"
        assert step.step_expected_outputs[0].type == "file_path"
        assert step.step_expected_outputs[0].required is True

    async def test_start_workflow_auto_generates_session_id(self, tools: WorkflowTools) -> None:
        """Test that start_workflow auto-generates a session_id when none is provided (non-claude platform)."""
        import re

        # tools fixture uses platform="test", so auto-generation should work
        input_data = StartWorkflowInput(
            goal="Complete the test job",
            job_name="test_job",
            workflow_name="main",
        )

        response = await tools.start_workflow(input_data)

        # Should return a 32-character hex string (uuid4().hex format)
        assert re.fullmatch(r"[0-9a-f]{32}", response.begin_step.session_id)

    async def test_start_workflow_auto_generated_session_id_is_stable(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test that the auto-generated session_id is usable for subsequent calls."""
        input_data = StartWorkflowInput(
            goal="Complete the test job",
            job_name="test_job",
            workflow_name="main",
        )

        response = await tools.start_workflow(input_data)
        generated_sid = response.begin_step.session_id

        # Use the returned session_id to finish the first step
        (project_root / "output1").write_text("Test output")
        finish_input = FinishedStepInput(
            outputs={"output1": "output1"},
            session_id=generated_sid,
        )
        finish_response = await tools.finished_step(finish_input)

        assert finish_response.status == StepStatus.NEXT_STEP
        assert finish_response.begin_step is not None
        assert finish_response.begin_step.step_id == "step2"

    async def test_start_workflow_requires_session_id_on_claude(
        self, project_root: Path
    ) -> None:
        """Test that session_id is required when platform is 'claude'."""
        claude_state = StateManager(project_root, platform="claude")
        claude_tools = WorkflowTools(project_root, claude_state)

        input_data = StartWorkflowInput(
            goal="Complete the test job",
            job_name="test_job",
            workflow_name="main",
        )

        with pytest.raises(ToolError, match="session_id is required"):
            await claude_tools.start_workflow(input_data)

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.11).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_common_job_info(self, tools: WorkflowTools) -> None:
        resp = await _start_main_workflow(tools)
        assert "test job for unit tests" in resp.begin_step.common_job_info

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_workflow_not_found(self, tools: WorkflowTools) -> None:
        inp = StartWorkflowInput(
            goal="Test",
            job_name="test_job",
            workflow_name="nonexistent",
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="not found"):
            await tools.start_workflow(inp)

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_job_not_found(self, tools: WorkflowTools) -> None:
        inp = StartWorkflowInput(
            goal="Test",
            job_name="nonexistent_job",
            workflow_name="main",
            session_id=SESSION_ID,
        )
        with pytest.raises(ToolError, match="not found"):
            await tools.start_workflow(inp)

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_inputs_passed_to_first_step(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Provided inputs are available to the first step."""
        # Create a file so the input value is valid
        outfile = project_root / "pre_existing.md"
        outfile.write_text("pre-existing content")

        inp = StartWorkflowInput(
            goal="Test with inputs",
            job_name="test_job",
            workflow_name="main",
            session_id=SESSION_ID,
            inputs={"output1": "pre_existing.md"},
        )
        resp = await tools.start_workflow(inp)
        # The input values should be resolved for step1 even though output1
        # is declared as an output (the inputs dict flows through)
        assert resp.begin_step.step_id == "step1"

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.3.12).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_stack_populated(self, tools: WorkflowTools) -> None:
        resp = await _start_main_workflow(tools)
        assert len(resp.stack) == 1
        assert resp.stack[0].workflow == "test_job/main"
        assert resp.stack[0].step == "step1"


# =========================================================================
# TestFinishedStep
# =========================================================================


class TestFinishedStep:
    """Tests for finished_step tool."""

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_missing_required_output(self, tools: WorkflowTools) -> None:
        await _start_main_workflow(tools)

        with pytest.raises(ToolError, match="Missing required outputs"):
            await _finish_step(tools, outputs={}, override="skip")

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_unknown_output(self, tools: WorkflowTools, project_root: Path) -> None:
        await _start_main_workflow(tools)

        outfile = project_root / "out.md"
        outfile.write_text("content")

        with pytest.raises(ToolError, match="Unknown output names"):
            await _finish_step(
                tools,
                outputs={"output1": "out.md", "bogus": "out.md"},
                override="skip",
            )

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_file_not_found(self, tools: WorkflowTools) -> None:
        await _start_main_workflow(tools)

        with pytest.raises(ToolError, match="file not found"):
            await _finish_step(
                tools,
                outputs={"output1": "nonexistent.md"},
                override="skip",
            )

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.17).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_advances_to_next_step(self, tools: WorkflowTools, project_root: Path) -> None:
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")

        resp = await _finish_step(
            tools,
            outputs={"output1": "out1.md"},
            override="skip",
        )
        assert resp.status == StepStatus.NEXT_STEP
        assert resp.begin_step is not None
        assert resp.begin_step.step_id == "step2"
        assert "Do the second step" in resp.begin_step.step_instructions

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.17).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_next_step_receives_inputs(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Step2 should receive output1 as an input."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")

        resp = await _finish_step(
            tools,
            outputs={"output1": "out1.md"},
            override="skip",
        )
        assert resp.begin_step is not None
        assert len(resp.begin_step.step_inputs) == 1
        assert resp.begin_step.step_inputs[0].name == "output1"
        assert resp.begin_step.step_inputs[0].value == "out1.md"

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.16).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_completes_workflow(self, tools: WorkflowTools, project_root: Path) -> None:
        await _start_main_workflow(tools)

        out1 = project_root / "out1.md"
        out1.write_text("step1 output")
        resp = await _finish_step(tools, outputs={"output1": "out1.md"}, override="skip")
        assert resp.status == StepStatus.NEXT_STEP

        out2 = project_root / "out2.md"
        out2.write_text("step2 output")
        resp = await _finish_step(tools, outputs={"output2": "out2.md"}, override="skip")
        assert resp.status == StepStatus.WORKFLOW_COMPLETE
        assert resp.summary is not None
        assert "completed" in resp.summary.lower()
        assert resp.all_outputs is not None
        assert "output1" in resp.all_outputs
        assert "output2" in resp.all_outputs

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.16).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_post_workflow_instructions(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        await _start_main_workflow(tools)

        out1 = project_root / "out1.md"
        out1.write_text("step1 output")
        await _finish_step(tools, outputs={"output1": "out1.md"}, override="skip")

        out2 = project_root / "out2.md"
        out2.write_text("step2 output")
        resp = await _finish_step(tools, outputs={"output2": "out2.md"}, override="skip")
        assert resp.status == StepStatus.WORKFLOW_COMPLETE
        assert resp.post_workflow_instructions is not None
        assert "PR" in resp.post_workflow_instructions

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_string_type_validation(self, tools: WorkflowTools, project_root: Path) -> None:
        """String type outputs must be strings, not other types."""
        # Start the delegated workflow which has a string_output
        inp = StartWorkflowInput(
            goal="Test string",
            job_name="test_job",
            workflow_name="delegated",
            session_id=SESSION_ID,
        )
        await tools.start_workflow(inp)

        with pytest.raises(ToolError, match="must be a string"):
            await _finish_step(
                tools,
                outputs={"string_output": ["not", "a", "string"]},
                override="skip",
            )

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_string_type_accepts_string(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        inp = StartWorkflowInput(
            goal="Test string",
            job_name="test_job",
            workflow_name="delegated",
            session_id=SESSION_ID,
        )
        await tools.start_workflow(inp)

        resp = await _finish_step(
            tools,
            outputs={"string_output": "some research findings"},
            override="skip",
        )
        assert resp.status == StepStatus.WORKFLOW_COMPLETE

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.14).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_quality_gate_pass(self, tools: WorkflowTools, project_root: Path) -> None:
        """When quality gate returns None (pass), step advances."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")

        with patch("deepwork.jobs.mcp.tools.run_quality_gate", return_value=None):
            resp = await _finish_step(
                tools,
                outputs={"output1": "out1.md"},
                work_summary="Did the thing",
            )
        assert resp.status == StepStatus.NEXT_STEP

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.12).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_quality_gate_fail(self, tools: WorkflowTools, project_root: Path) -> None:
        """When quality gate returns feedback, status is NEEDS_WORK."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")

        with patch(
            "deepwork.jobs.mcp.tools.run_quality_gate",
            return_value="Output is missing key details.",
        ):
            resp = await _finish_step(
                tools,
                outputs={"output1": "out1.md"},
                work_summary="Did the thing",
            )
        assert resp.status == StepStatus.NEEDS_WORK
        assert resp.feedback is not None
        assert "missing key details" in resp.feedback

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_quality_gate_skipped_with_override(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Providing override reason skips quality gate entirely."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")

        # Patch to ensure it's NOT called
        with patch(
            "deepwork.jobs.mcp.tools.run_quality_gate",
        ) as mock_qg:
            resp = await _finish_step(
                tools,
                outputs={"output1": "out1.md"},
                override="Testing override",
            )
            mock_qg.assert_not_called()
        assert resp.status == StepStatus.NEXT_STEP

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_no_active_session(self, tools: WorkflowTools) -> None:
        with pytest.raises(ToolError, match="No active workflow session"):
            await _finish_step(tools, outputs={"output1": "x.md"}, override="skip")

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_file_path_list_validated(self, tools: WorkflowTools, project_root: Path) -> None:
        """file_path type accepts a list of paths and validates each."""
        await _start_main_workflow(tools)

        existing = project_root / "exists.md"
        existing.write_text("content")

        with pytest.raises(ToolError, match="file not found"):
            await _finish_step(
                tools,
                outputs={"output1": ["exists.md", "missing.md"]},
                override="skip",
            )

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_file_path_list_all_exist(self, tools: WorkflowTools, project_root: Path) -> None:
        await _start_main_workflow(tools)

        f1 = project_root / "a.md"
        f2 = project_root / "b.md"
        f1.write_text("a")
        f2.write_text("b")

        resp = await _finish_step(
            tools,
            outputs={"output1": ["a.md", "b.md"]},
            override="skip",
        )
        assert resp.status == StepStatus.NEXT_STEP


# =========================================================================
# TestAbortWorkflow
# =========================================================================


class TestAbortWorkflow:
    """Tests for abort_workflow tool."""

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.6.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_returns_to_empty_stack(self, tools: WorkflowTools) -> None:
        await _start_main_workflow(tools)

        inp = AbortWorkflowInput(
            explanation="Changed my mind",
            session_id=SESSION_ID,
        )
        resp = await tools.abort_workflow(inp)

        assert resp.aborted_workflow == "test_job/main"
        assert resp.aborted_step == "step1"
        assert resp.explanation == "Changed my mind"
        assert resp.resumed_workflow is None
        assert resp.resumed_step is None
        assert len(resp.stack) == 0

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.6.5, JOBS-REQ-001.6.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_returns_to_parent(self, tools: WorkflowTools, project_root: Path) -> None:
        """Aborting a nested workflow returns to the parent."""
        # Start outer workflow
        await _start_main_workflow(tools)

        # Start inner (nested) workflow on the same session
        inner_inp = StartWorkflowInput(
            goal="Inner goal",
            job_name="test_job",
            workflow_name="delegated",
            session_id=SESSION_ID,
        )
        await tools.start_workflow(inner_inp)

        # Abort inner
        abort_inp = AbortWorkflowInput(
            explanation="Inner done",
            session_id=SESSION_ID,
        )
        resp = await tools.abort_workflow(abort_inp)

        assert resp.aborted_workflow == "test_job/delegated"
        assert resp.resumed_workflow == "test_job/main"
        assert resp.resumed_step == "step1"
        assert len(resp.stack) == 1


# =========================================================================
# TestGoToStep
# =========================================================================


class TestGoToStep:
    """Tests for go_to_step tool."""

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.7.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_navigate_back(self, tools: WorkflowTools, project_root: Path) -> None:
        """Navigate back to step1 after advancing to step2."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")
        await _finish_step(tools, outputs={"output1": "out1.md"}, override="skip")

        inp = GoToStepInput(step_id="step1", session_id=SESSION_ID)
        resp = await tools.go_to_step(inp)

        assert resp.begin_step.step_id == "step1"
        assert "step1" in resp.invalidated_steps
        assert "step2" in resp.invalidated_steps

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.7.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_clears_progress(
        self, tools: WorkflowTools, project_root: Path, state_manager: StateManager
    ) -> None:
        """Going back clears step progress from target onward."""
        await _start_main_workflow(tools)

        outfile = project_root / "out1.md"
        outfile.write_text("step1 output")
        await _finish_step(tools, outputs={"output1": "out1.md"}, override="skip")

        inp = GoToStepInput(step_id="step1", session_id=SESSION_ID)
        await tools.go_to_step(inp)

        # Previous outputs for step1 should be cleared
        session = state_manager.resolve_session(SESSION_ID)
        # step1 progress was cleared and then re-created by start_step
        # step2 progress should be gone
        assert "step2" not in session.step_progress

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.7.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_prevents_going_forward(self, tools: WorkflowTools) -> None:
        """Cannot use go_to_step to go forward."""
        await _start_main_workflow(tools)

        inp = GoToStepInput(step_id="step2", session_id=SESSION_ID)
        with pytest.raises(ToolError, match="Cannot go forward"):
            await tools.go_to_step(inp)

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.7.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_invalid_step_name(self, tools: WorkflowTools) -> None:
        await _start_main_workflow(tools)

        inp = GoToStepInput(step_id="nonexistent", session_id=SESSION_ID)
        with pytest.raises(ToolError, match="not found"):
            await tools.go_to_step(inp)

    @pytest.mark.asyncio
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.7.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_current_step(self, tools: WorkflowTools) -> None:
        """Going to the current step is allowed (index == current)."""
        await _start_main_workflow(tools)

        inp = GoToStepInput(step_id="step1", session_id=SESSION_ID)
        resp = await tools.go_to_step(inp)
        assert resp.begin_step.step_id == "step1"
