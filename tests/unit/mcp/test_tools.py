"""Tests for MCP workflow tools."""

from pathlib import Path

import pytest

from deepwork.mcp.quality_gate import MockQualityGate
from deepwork.mcp.schemas import FinishedStepInput, StartWorkflowInput, StepStatus
from deepwork.mcp.state import StateError, StateManager
from deepwork.mcp.tools import ToolError, WorkflowTools


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project with a test job."""
    # Create .deepwork directory
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()

    # Create jobs directory with a test job
    jobs_dir = deepwork_dir / "jobs"
    jobs_dir.mkdir()

    job_dir = jobs_dir / "test_job"
    job_dir.mkdir()

    # Create job.yml
    job_yml = """
name: test_job
version: "1.0.0"
summary: A test job
description: This is a test job for unit tests

steps:
  - id: step1
    name: First Step
    description: The first step
    instructions_file: steps/step1.md
    outputs:
      - output1.md
    quality_criteria:
      - Output must be valid
  - id: step2
    name: Second Step
    description: The second step
    instructions_file: steps/step2.md
    outputs:
      - output2.md
    dependencies:
      - step1

workflows:
  - name: main
    summary: Main workflow
    steps:
      - step1
      - step2
"""
    (job_dir / "job.yml").write_text(job_yml)

    # Create step instruction files
    steps_dir = job_dir / "steps"
    steps_dir.mkdir()
    (steps_dir / "step1.md").write_text("# Step 1\n\nDo the first thing.")
    (steps_dir / "step2.md").write_text("# Step 2\n\nDo the second thing.")

    return tmp_path


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    """Create a StateManager instance."""
    return StateManager(project_root)


@pytest.fixture
def tools(project_root: Path, state_manager: StateManager) -> WorkflowTools:
    """Create a WorkflowTools instance without quality gate."""
    return WorkflowTools(
        project_root=project_root,
        state_manager=state_manager,
    )


@pytest.fixture
def tools_with_quality(project_root: Path, state_manager: StateManager) -> WorkflowTools:
    """Create a WorkflowTools instance with mock quality gate."""
    return WorkflowTools(
        project_root=project_root,
        state_manager=state_manager,
        quality_gate=MockQualityGate(should_pass=True),
    )


class TestWorkflowTools:
    """Tests for WorkflowTools class."""

    def test_init(self, tools: WorkflowTools, project_root: Path) -> None:
        """Test WorkflowTools initialization."""
        assert tools.project_root == project_root
        assert tools.jobs_dir == project_root / ".deepwork" / "jobs"

    def test_get_workflows(self, tools: WorkflowTools) -> None:
        """Test getting all workflows."""
        response = tools.get_workflows()

        assert len(response.jobs) == 1
        job = response.jobs[0]

        assert job.name == "test_job"
        assert job.summary == "A test job"
        assert len(job.workflows) == 1
        assert job.workflows[0].name == "main"
        assert job.workflows[0].steps == ["step1", "step2"]
        assert job.workflows[0].first_step == "step1"

    def test_get_workflows_empty(self, tmp_path: Path) -> None:
        """Test getting workflows when no jobs exist."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()

        state_manager = StateManager(tmp_path)
        tools = WorkflowTools(
            project_root=tmp_path,
            state_manager=state_manager,
        )

        response = tools.get_workflows()

        assert len(response.jobs) == 0

    def test_start_workflow(self, tools: WorkflowTools) -> None:
        """Test starting a workflow."""
        input_data = StartWorkflowInput(
            goal="Complete the test job",
            job_name="test_job",
            workflow_name="main",
            instance_id="test-instance",
        )

        response = tools.start_workflow(input_data)

        assert response.session_id is not None
        assert "test-instance" in response.branch_name
        assert response.current_step_id == "step1"
        assert "Step 1" in response.step_instructions
        assert "output1.md" in response.step_outputs
        assert "Output must be valid" in response.quality_criteria

    def test_start_workflow_invalid_job(self, tools: WorkflowTools) -> None:
        """Test starting workflow with invalid job."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="nonexistent",
            workflow_name="main",
        )

        with pytest.raises(ToolError, match="Job not found"):
            tools.start_workflow(input_data)

    def test_start_workflow_invalid_workflow(self, tools: WorkflowTools) -> None:
        """Test starting workflow with invalid workflow name."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="nonexistent",
        )

        with pytest.raises(ToolError, match="Workflow.*not found"):
            tools.start_workflow(input_data)

    def test_finished_step_no_session(self, tools: WorkflowTools) -> None:
        """Test finished_step without active session."""
        input_data = FinishedStepInput(outputs=["output1.md"])

        with pytest.raises(StateError, match="No active workflow session"):
            tools.finished_step(input_data)

    def test_finished_step_advances_to_next(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step advances to next step."""
        # Start workflow first
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools.start_workflow(start_input)

        # Create output file
        (project_root / "output1.md").write_text("Test output")

        # Finish first step
        finish_input = FinishedStepInput(
            outputs=["output1.md"],
            notes="Completed step 1",
        )
        response = tools.finished_step(finish_input)

        assert response.status == StepStatus.NEXT_STEP
        assert response.next_step_id == "step2"
        assert response.step_instructions is not None
        assert "Step 2" in response.step_instructions

    def test_finished_step_completes_workflow(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step completes workflow on last step."""
        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools.start_workflow(start_input)

        # Complete first step
        (project_root / "output1.md").write_text("Output 1")
        tools.finished_step(FinishedStepInput(outputs=["output1.md"]))

        # Complete second (last) step
        (project_root / "output2.md").write_text("Output 2")
        response = tools.finished_step(FinishedStepInput(outputs=["output2.md"]))

        assert response.status == StepStatus.WORKFLOW_COMPLETE
        assert response.summary is not None
        assert "completed" in response.summary.lower()
        assert "output1.md" in response.all_outputs
        assert "output2.md" in response.all_outputs

    def test_finished_step_with_quality_gate_pass(
        self, tools_with_quality: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step passes quality gate."""
        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools_with_quality.start_workflow(start_input)

        # Create output and finish step
        (project_root / "output1.md").write_text("Valid output")
        response = tools_with_quality.finished_step(
            FinishedStepInput(outputs=["output1.md"])
        )

        # Should advance to next step
        assert response.status == StepStatus.NEXT_STEP

    def test_finished_step_with_quality_gate_fail(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step fails quality gate."""
        # Create tools with failing quality gate
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=MockQualityGate(should_pass=False, feedback="Needs improvement"),
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools.start_workflow(start_input)

        # Create output and finish step
        (project_root / "output1.md").write_text("Invalid output")
        response = tools.finished_step(FinishedStepInput(outputs=["output1.md"]))

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback == "Needs improvement"
        assert response.failed_criteria is not None

    def test_finished_step_quality_gate_max_attempts(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step fails after max quality gate attempts."""
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=MockQualityGate(should_pass=False, feedback="Always fails"),
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools.start_workflow(start_input)

        # Create output
        (project_root / "output1.md").write_text("Bad output")

        # Try multiple times (max is 3)
        for _ in range(2):
            response = tools.finished_step(FinishedStepInput(outputs=["output1.md"]))
            assert response.status == StepStatus.NEEDS_WORK

        # Third attempt should raise error
        with pytest.raises(ToolError, match="Quality gate failed after.*attempts"):
            tools.finished_step(FinishedStepInput(outputs=["output1.md"]))

    def test_finished_step_quality_gate_override(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step skips quality gate when override reason provided."""
        # Create tools with failing quality gate
        failing_gate = MockQualityGate(should_pass=False, feedback="Would fail")
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=failing_gate,
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        tools.start_workflow(start_input)

        # Create output and finish step with override reason
        (project_root / "output1.md").write_text("Output that would fail quality check")
        response = tools.finished_step(
            FinishedStepInput(
                outputs=["output1.md"],
                quality_review_override_reason="Manual review completed offline",
            )
        )

        # Should advance to next step despite failing quality gate config
        assert response.status == StepStatus.NEXT_STEP
        # Quality gate should not have been called
        assert len(failing_gate.evaluations) == 0
