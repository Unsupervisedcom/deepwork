"""Tests for MCP workflow tools."""

from pathlib import Path

import pytest

from deepwork.jobs.mcp.quality_gate import MockQualityGate
from deepwork.jobs.mcp.schemas import (
    AbortWorkflowInput,
    FinishedStepInput,
    StartWorkflowInput,
    StepStatus,
)
from deepwork.jobs.mcp.state import StateError, StateManager
from deepwork.jobs.mcp.tools import ToolError, WorkflowTools


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
common_job_info_provided_to_all_steps_at_runtime: This is a test job for unit tests

steps:
  - id: step1
    name: First Step
    description: The first step
    instructions_file: steps/step1.md
    outputs:
      output1.md:
        type: file
        description: First step output
        required: true
    reviews:
      - run_each: step
        quality_criteria:
          "Output Valid": "Is the output valid?"
  - id: step2
    name: Second Step
    description: The second step
    instructions_file: steps/step2.md
    outputs:
      output2.md:
        type: file
        description: Second step output
        required: true
    dependencies:
      - step1
    reviews: []

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
        external_runner="claude",
    )


class TestWorkflowTools:
    """Tests for WorkflowTools class."""

    def test_init(self, tools: WorkflowTools, project_root: Path) -> None:
        """Test WorkflowTools initialization."""
        assert tools.project_root == project_root

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.2.3, REQ-001.2.4, REQ-001.2.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_get_workflows(self, tools: WorkflowTools) -> None:
        """Test getting all workflows."""
        response = tools.get_workflows()

        assert len(response.jobs) == 1
        job = response.jobs[0]

        assert job.name == "test_job"
        assert job.summary == "A test job"
        assert len(job.workflows) == 1
        assert job.workflows[0].name == "main"
        assert job.workflows[0].summary == "Main workflow"

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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.3.2, REQ-001.3.3, REQ-001.3.9, REQ-001.3.10, REQ-001.3.11, REQ-001.3.13, REQ-001.3.14).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_workflow(self, tools: WorkflowTools) -> None:
        """Test starting a workflow."""
        input_data = StartWorkflowInput(
            goal="Complete the test job",
            job_name="test_job",
            workflow_name="main",
            instance_id="test-instance",
        )

        response = await tools.start_workflow(input_data)

        assert response.begin_step.session_id is not None
        assert response.begin_step.step_id == "step1"
        assert "Step 1" in response.begin_step.step_instructions
        outputs = response.begin_step.step_expected_outputs
        assert len(outputs) == 1
        assert outputs[0].name == "output1.md"
        assert outputs[0].type == "file"
        assert outputs[0].syntax_for_finished_step_tool == "filepath"
        assert len(response.begin_step.step_reviews) == 1
        assert response.begin_step.step_reviews[0].run_each == "step"
        assert "Output Valid" in response.begin_step.step_reviews[0].quality_criteria

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_workflow_invalid_job(self, tools: WorkflowTools) -> None:
        """Test starting workflow with invalid job."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="nonexistent",
            workflow_name="main",
        )

        with pytest.raises(ToolError, match="Job not found"):
            await tools.start_workflow(input_data)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_workflow_auto_selects_single_workflow(self, tools: WorkflowTools) -> None:
        """Test that a wrong workflow name auto-selects when job has one workflow."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="nonexistent",
        )

        # Should succeed by auto-selecting the only workflow ("main")
        response = await tools.start_workflow(input_data)
        assert response.begin_step.step_id == "step1"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.3.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_workflow_invalid_workflow_multiple(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that a wrong workflow name errors when job has multiple workflows."""
        # Create a job with two workflows
        job_dir = project_root / ".deepwork" / "jobs" / "multi_wf_job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text(
            """
name: multi_wf_job
version: "1.0.0"
summary: A job with multiple workflows
common_job_info_provided_to_all_steps_at_runtime: Test job with multiple workflows

steps:
  - id: step_a
    name: Step A
    description: Step A
    instructions_file: steps/step_a.md
    outputs:
      output_a.md:
        type: file
        description: Step A output
        required: true
    reviews: []
  - id: step_b
    name: Step B
    description: Step B
    instructions_file: steps/step_b.md
    outputs:
      output_b.md:
        type: file
        description: Step B output
        required: true
    reviews: []

workflows:
  - name: alpha
    summary: Alpha workflow
    steps:
      - step_a
  - name: beta
    summary: Beta workflow
    steps:
      - step_b
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_a.md").write_text("# Step A")
        (steps_dir / "step_b.md").write_text("# Step B")

        tools = WorkflowTools(project_root=project_root, state_manager=state_manager)
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="multi_wf_job",
            workflow_name="nonexistent",
        )

        with pytest.raises(ToolError, match="Workflow.*not found.*alpha.*beta"):
            await tools.start_workflow(input_data)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_no_session(self, tools: WorkflowTools) -> None:
        """Test finished_step without active session."""
        input_data = FinishedStepInput(outputs={"output1.md": "output1.md"})

        with pytest.raises(StateError, match="No active workflow session"):
            await tools.finished_step(input_data)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.7, REQ-001.4.15, REQ-001.4.17).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_advances_to_next(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step advances to next step."""
        # Start workflow first
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Create output file
        (project_root / "output1.md").write_text("Test output")

        # Finish first step
        finish_input = FinishedStepInput(
            outputs={"output1.md": "output1.md"},
            notes="Completed step 1",
        )
        response = await tools.finished_step(finish_input)

        assert response.status == StepStatus.NEXT_STEP
        assert response.begin_step is not None
        assert response.begin_step.step_id == "step2"
        assert response.begin_step.step_instructions is not None
        assert "Step 2" in response.begin_step.step_instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.15, REQ-001.4.16).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_completes_workflow(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step completes workflow on last step."""
        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Complete first step
        (project_root / "output1.md").write_text("Output 1")
        await tools.finished_step(FinishedStepInput(outputs={"output1.md": "output1.md"}))

        # Complete second (last) step
        (project_root / "output2.md").write_text("Output 2")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"output2.md": "output2.md"})
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE
        assert response.summary is not None
        assert "completed" in response.summary.lower()
        assert response.all_outputs is not None
        assert "output1.md" in response.all_outputs
        assert "output2.md" in response.all_outputs

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.8, REQ-001.4.14).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_with_quality_gate_pass(
        self, tools_with_quality: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step passes quality gate."""
        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools_with_quality.start_workflow(start_input)

        # Create output and finish step
        (project_root / "output1.md").write_text("Valid output")
        response = await tools_with_quality.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        # Should advance to next step
        assert response.status == StepStatus.NEXT_STEP

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.8, REQ-001.4.11, REQ-001.4.12).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_with_quality_gate_fail(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step fails quality gate."""
        # Create tools with failing quality gate
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=MockQualityGate(should_pass=False, feedback="Needs improvement"),
            external_runner="claude",
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Create output and finish step
        (project_root / "output1.md").write_text("Invalid output")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback == "Needs improvement"
        assert response.failed_reviews is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_quality_gate_max_attempts(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step fails after max quality gate attempts."""
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=MockQualityGate(should_pass=False, feedback="Always fails"),
            external_runner="claude",
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Create output
        (project_root / "output1.md").write_text("Bad output")

        # Try multiple times (max is 3)
        for _ in range(2):
            response = await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": "output1.md"})
            )
            assert response.status == StepStatus.NEEDS_WORK

        # Third attempt should raise error
        with pytest.raises(ToolError, match="Quality gate failed after.*attempts"):
            await tools.finished_step(FinishedStepInput(outputs={"output1.md": "output1.md"}))

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_quality_gate_override(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step skips quality gate when override reason provided."""
        # Create tools with failing quality gate
        failing_gate = MockQualityGate(should_pass=False, feedback="Would fail")
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=failing_gate,
            external_runner="claude",
        )

        # Start workflow
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Create output and finish step with override reason
        (project_root / "output1.md").write_text("Output that would fail quality check")
        response = await tools.finished_step(
            FinishedStepInput(
                outputs={"output1.md": "output1.md"},
                quality_review_override_reason="Manual review completed offline",
            )
        )

        # Should advance to next step despite failing quality gate config
        assert response.status == StepStatus.NEXT_STEP
        # Quality gate should not have been called
        assert len(failing_gate.evaluations) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_unknown_output_keys(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step rejects unknown output keys."""
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        (project_root / "output1.md").write_text("content")
        (project_root / "extra.md").write_text("content")

        with pytest.raises(ToolError, match="Unknown output names.*extra.md"):
            await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": "output1.md", "extra.md": "extra.md"})
            )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_missing_output_keys(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step rejects when declared outputs are missing."""
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Step1 declares output1.md, but we provide empty dict
        with pytest.raises(ToolError, match="Missing required outputs.*output1.md"):
            await tools.finished_step(FinishedStepInput(outputs={}))

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_allows_omitting_optional_outputs(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step allows omitting outputs with required: false."""
        job_dir = project_root / ".deepwork" / "jobs" / "optional_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: optional_job
version: "1.0.0"
summary: Job with optional output
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: produce
    name: Produce
    description: Produces outputs
    instructions_file: steps/produce.md
    outputs:
      main_report.md:
        type: file
        description: The main report
        required: true
      supplementary.md:
        type: file
        description: Optional supplementary material
        required: false
      extra_files:
        type: files
        description: Optional extra files
        required: false
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - produce
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "produce.md").write_text("# Produce\n\nProduce outputs.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        await tools.start_workflow(
            StartWorkflowInput(
                goal="Produce outputs",
                job_name="optional_job",
                workflow_name="main",
            )
        )

        # Only provide the required output, omit optional ones
        (project_root / "main_report.md").write_text("Main report content")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"main_report.md": "main_report.md"})
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.2, REQ-001.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_rejects_missing_required_but_not_optional(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step rejects missing required outputs even when optional ones exist."""
        job_dir = project_root / ".deepwork" / "jobs" / "mixed_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: mixed_job
version: "1.0.0"
summary: Job with mixed required/optional outputs
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: produce
    name: Produce
    description: Produces outputs
    instructions_file: steps/produce.md
    outputs:
      required_output.md:
        type: file
        description: Must be provided
        required: true
      optional_output.md:
        type: file
        description: Can be skipped
        required: false
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - produce
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "produce.md").write_text("# Produce\n\nProduce outputs.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        await tools.start_workflow(
            StartWorkflowInput(
                goal="Produce outputs",
                job_name="mixed_job",
                workflow_name="main",
            )
        )

        # Provide only the optional output, not the required one
        (project_root / "optional_output.md").write_text("Optional content")
        with pytest.raises(ToolError, match="Missing required outputs.*required_output.md"):
            await tools.finished_step(
                FinishedStepInput(outputs={"optional_output.md": "optional_output.md"})
            )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_accepts_optional_outputs_when_provided(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step validates optional outputs when they are provided."""
        job_dir = project_root / ".deepwork" / "jobs" / "optional_provided_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: optional_provided_job
version: "1.0.0"
summary: Job with optional output that gets provided
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: produce
    name: Produce
    description: Produces outputs
    instructions_file: steps/produce.md
    outputs:
      main.md:
        type: file
        description: Required output
        required: true
      bonus.md:
        type: file
        description: Optional output
        required: false
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - produce
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "produce.md").write_text("# Produce\n\nProduce outputs.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        await tools.start_workflow(
            StartWorkflowInput(
                goal="Produce outputs",
                job_name="optional_provided_job",
                workflow_name="main",
            )
        )

        # Provide both required and optional
        (project_root / "main.md").write_text("Main content")
        (project_root / "bonus.md").write_text("Bonus content")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"main.md": "main.md", "bonus.md": "bonus.md"})
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.3.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_expected_outputs_include_required_field(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that step_expected_outputs includes the required field."""
        job_dir = project_root / ".deepwork" / "jobs" / "req_field_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: req_field_job
version: "1.0.0"
summary: Job to test required field in expected outputs
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: produce
    name: Produce
    description: Produces outputs
    instructions_file: steps/produce.md
    outputs:
      required_out.md:
        type: file
        description: Required output
        required: true
      optional_out.md:
        type: file
        description: Optional output
        required: false
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - produce
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "produce.md").write_text("# Produce\n\nProduce outputs.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        response = await tools.start_workflow(
            StartWorkflowInput(
                goal="Produce outputs",
                job_name="req_field_job",
                workflow_name="main",
            )
        )

        outputs = response.begin_step.step_expected_outputs
        assert len(outputs) == 2

        required_out = next(o for o in outputs if o.name == "required_out.md")
        optional_out = next(o for o in outputs if o.name == "optional_out.md")

        assert required_out.required is True
        assert optional_out.required is False

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_file_type_must_be_string(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step rejects list value for type: file output."""
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        (project_root / "output1.md").write_text("content")

        with pytest.raises(ToolError, match="type 'file'.*single string path"):
            await tools.finished_step(FinishedStepInput(outputs={"output1.md": ["output1.md"]}))

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_file_existence(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step rejects when file does not exist."""
        start_input = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Don't create the file
        with pytest.raises(ToolError, match="file not found at.*nonexistent.md"):
            await tools.finished_step(FinishedStepInput(outputs={"output1.md": "nonexistent.md"}))

    async def test_finished_step_empty_outputs_for_step_with_no_outputs(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that empty outputs {} works for steps declared with no outputs."""
        # Create a job with a step that has no outputs
        job_dir = project_root / ".deepwork" / "jobs" / "no_output_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: no_output_job
version: "1.0.0"
summary: Job with no-output step
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: cleanup
    name: Cleanup
    description: Cleanup step with no outputs
    instructions_file: steps/cleanup.md
    outputs: {}
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - cleanup
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "cleanup.md").write_text("# Cleanup\n\nDo cleanup.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        start_input = StartWorkflowInput(
            goal="Run cleanup",
            job_name="no_output_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        response = await tools.finished_step(FinishedStepInput(outputs={}))

        assert response.status == StepStatus.WORKFLOW_COMPLETE

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_files_type_output(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step validation for type: files outputs."""
        # Create a job with a files-type output
        job_dir = project_root / ".deepwork" / "jobs" / "files_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: files_job
version: "1.0.0"
summary: Job with files output
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
        required: true
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - generate
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "generate.md").write_text("# Generate\n\nGenerate reports.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        start_input = StartWorkflowInput(
            goal="Generate reports",
            job_name="files_job",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # type: files requires a list, not a string
        with pytest.raises(ToolError, match="type 'files'.*list of paths"):
            await tools.finished_step(FinishedStepInput(outputs={"reports": "report1.md"}))

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_validates_files_type_existence(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step validates file existence for type: files outputs."""
        job_dir = project_root / ".deepwork" / "jobs" / "files_job2"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: files_job2
version: "1.0.0"
summary: Job with files output
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
        required: true
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - generate
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "generate.md").write_text("# Generate\n\nGenerate reports.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        start_input = StartWorkflowInput(
            goal="Generate reports",
            job_name="files_job2",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        # Create one file but not the other
        (project_root / "report1.md").write_text("Report 1")

        with pytest.raises(ToolError, match="file not found at.*missing.md"):
            await tools.finished_step(
                FinishedStepInput(outputs={"reports": ["report1.md", "missing.md"]})
            )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.5.6, REQ-001.5.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_files_type_success(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test finished_step succeeds with valid type: files outputs."""
        job_dir = project_root / ".deepwork" / "jobs" / "files_job3"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: files_job3
version: "1.0.0"
summary: Job with files output
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
        required: true
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - generate
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "generate.md").write_text("# Generate\n\nGenerate reports.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        start_input = StartWorkflowInput(
            goal="Generate reports",
            job_name="files_job3",
            workflow_name="main",
        )
        await tools.start_workflow(start_input)

        (project_root / "report1.md").write_text("Report 1")
        (project_root / "report2.md").write_text("Report 2")

        response = await tools.finished_step(
            FinishedStepInput(outputs={"reports": ["report1.md", "report2.md"]})
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE

    async def test_quality_reviewer_receives_only_current_step_outputs(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that quality reviewer receives ONLY the current step's outputs.

        Prior step outputs are no longer auto-included as inputs.
        """
        # Create a 3-step job: step1 -> step2 -> step3
        job_dir = project_root / ".deepwork" / "jobs" / "chain_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: chain_job
version: "1.0.0"
summary: Three-step chain to test input filtering
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: step1
    name: Step 1
    description: First step
    instructions_file: steps/step1.md
    outputs:
      step1_output.md:
        type: file
        description: Step 1 output
        required: true
    reviews: []

  - id: step2
    name: Step 2
    description: Second step - takes step1 output
    instructions_file: steps/step2.md
    inputs:
      - file: step1_output.md
        from_step: step1
    outputs:
      step2_output.md:
        type: file
        description: Step 2 output
        required: true
    dependencies:
      - step1
    reviews: []

  - id: step3
    name: Step 3
    description: Third step - takes ONLY step2 output (not step1)
    instructions_file: steps/step3.md
    inputs:
      - file: step2_output.md
        from_step: step2
    outputs:
      step3_output.md:
        type: file
        description: Step 3 output
        required: true
    dependencies:
      - step2
    reviews:
      - run_each: step
        quality_criteria:
          "Complete": "Is the output complete?"

workflows:
  - name: main
    summary: Main workflow
    steps:
      - step1
      - step2
      - step3
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1\n\nProduce output.")
        (steps_dir / "step2.md").write_text("# Step 2\n\nProduce output.")
        (steps_dir / "step3.md").write_text("# Step 3\n\nProduce output.")

        mock_gate = MockQualityGate(should_pass=True)
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        # Start workflow
        await tools.start_workflow(
            StartWorkflowInput(
                goal="Test input filtering",
                job_name="chain_job",
                workflow_name="main",
            )
        )

        # Complete step1
        (project_root / "step1_output.md").write_text("STEP1_CONTENT_MARKER")
        await tools.finished_step(FinishedStepInput(outputs={"step1_output.md": "step1_output.md"}))

        # Complete step2
        (project_root / "step2_output.md").write_text("STEP2_CONTENT_MARKER")
        await tools.finished_step(FinishedStepInput(outputs={"step2_output.md": "step2_output.md"}))

        # Complete step3 — quality gate runs here
        (project_root / "step3_output.md").write_text("STEP3_CONTENT_MARKER")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"step3_output.md": "step3_output.md"})
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE

        # Verify reviewer was called WITHOUT any prior step inputs
        assert len(mock_gate.evaluations) == 1
        evaluation = mock_gate.evaluations[0]

        # Should only have the current step's outputs, not inputs from prior steps
        assert "step3_output.md" in evaluation["outputs"]
        assert "inputs" not in evaluation, (
            "Quality reviewer should not receive 'inputs' key — "
            "prior step outputs are no longer auto-included"
        )

    async def test_additional_review_guidance_reaches_reviewer(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that additional_review_guidance from job.yml is passed to the reviewer."""
        job_dir = project_root / ".deepwork" / "jobs" / "guided_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: guided_job
version: "1.0.0"
summary: Job with review guidance
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: write
    name: Write Report
    description: Write a report
    instructions_file: steps/write.md
    outputs:
      report.md:
        type: file
        description: The report
        required: true
    reviews:
      - run_each: report.md
        additional_review_guidance: "Read the project README for context on expected format."
        quality_criteria:
          "Format Correct": "Does the report follow the expected format?"

workflows:
  - name: main
    summary: Main workflow
    steps:
      - write
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "write.md").write_text("# Write\n\nWrite the report.")

        mock_gate = MockQualityGate(should_pass=True)
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        await tools.start_workflow(
            StartWorkflowInput(
                goal="Write report",
                job_name="guided_job",
                workflow_name="main",
            )
        )

        (project_root / "report.md").write_text("Report content")
        response = await tools.finished_step(FinishedStepInput(outputs={"report.md": "report.md"}))

        assert response.status == StepStatus.WORKFLOW_COMPLETE
        assert len(mock_gate.evaluations) == 1
        assert mock_gate.evaluations[0]["additional_review_guidance"] == (
            "Read the project README for context on expected format."
        )

    async def test_review_guidance_in_start_workflow_response(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that ReviewInfo in start_workflow response includes guidance."""
        job_dir = project_root / ".deepwork" / "jobs" / "guided_job2"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """
name: guided_job2
version: "1.0.0"
summary: Job with review guidance
common_job_info_provided_to_all_steps_at_runtime: Test job

steps:
  - id: analyze
    name: Analyze
    description: Analyze data
    instructions_file: steps/analyze.md
    outputs:
      analysis.md:
        type: file
        description: Analysis output
        required: true
    reviews:
      - run_each: step
        additional_review_guidance: "Check the raw data directory for completeness."
        quality_criteria:
          "Thorough": "Is the analysis thorough?"

workflows:
  - name: main
    summary: Main workflow
    steps:
      - analyze
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "analyze.md").write_text("# Analyze\n\nAnalyze the data.")

        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )

        response = await tools.start_workflow(
            StartWorkflowInput(
                goal="Analyze data",
                job_name="guided_job2",
                workflow_name="main",
            )
        )

        reviews = response.begin_step.step_reviews
        assert len(reviews) == 1
        assert reviews[0].additional_review_guidance == (
            "Check the raw data directory for completeness."
        )


class TestSessionIdRouting:
    """Tests for session_id routing in WorkflowTools."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project with two test jobs."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        jobs_dir = deepwork_dir / "jobs"
        jobs_dir.mkdir()

        # Create job_a with two steps
        job_a_dir = jobs_dir / "job_a"
        job_a_dir.mkdir()
        (job_a_dir / "job.yml").write_text(
            """
name: job_a
version: "1.0.0"
summary: Job A
common_job_info_provided_to_all_steps_at_runtime: Test job A

steps:
  - id: a_step1
    name: A Step 1
    description: First step of A
    instructions_file: steps/a_step1.md
    outputs:
      a_out1.md:
        type: file
        description: A step 1 output
        required: true
    reviews: []
  - id: a_step2
    name: A Step 2
    description: Second step of A
    instructions_file: steps/a_step2.md
    outputs:
      a_out2.md:
        type: file
        description: A step 2 output
        required: true
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - a_step1
      - a_step2
"""
        )
        a_steps = job_a_dir / "steps"
        a_steps.mkdir()
        (a_steps / "a_step1.md").write_text("# A Step 1\n\nDo A step 1.")
        (a_steps / "a_step2.md").write_text("# A Step 2\n\nDo A step 2.")

        # Create job_b with one step
        job_b_dir = jobs_dir / "job_b"
        job_b_dir.mkdir()
        (job_b_dir / "job.yml").write_text(
            """
name: job_b
version: "1.0.0"
summary: Job B
common_job_info_provided_to_all_steps_at_runtime: Test job B

steps:
  - id: b_step1
    name: B Step 1
    description: First step of B
    instructions_file: steps/b_step1.md
    outputs:
      b_out1.md:
        type: file
        description: B step 1 output
        required: true
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - b_step1
"""
        )
        b_steps = job_b_dir / "steps"
        b_steps.mkdir()
        (b_steps / "b_step1.md").write_text("# B Step 1\n\nDo B step 1.")

        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root)

    @pytest.fixture
    def tools(self, project_root: Path, state_manager: StateManager) -> WorkflowTools:
        return WorkflowTools(project_root=project_root, state_manager=state_manager)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_finished_step_with_session_id_not_on_top(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test finished_step targets a non-top session when session_id is provided."""
        # Start two workflows — session_a is below session_b on the stack
        resp_a = await tools.start_workflow(
            StartWorkflowInput(goal="Do A", job_name="job_a", workflow_name="main")
        )
        session_a_id = resp_a.begin_step.session_id

        resp_b = await tools.start_workflow(
            StartWorkflowInput(goal="Do B", job_name="job_b", workflow_name="main")
        )
        session_b_id = resp_b.begin_step.session_id

        assert tools.state_manager.get_stack_depth() == 2

        # Create output files for job_a's first step
        (project_root / "a_out1.md").write_text("A output 1")

        # Finish step on session_a (NOT on top) using session_id
        response = await tools.finished_step(
            FinishedStepInput(
                outputs={"a_out1.md": "a_out1.md"},
                session_id=session_a_id,
            )
        )

        # Should advance to next step in job_a
        assert response.status == StepStatus.NEXT_STEP
        assert response.begin_step is not None
        assert response.begin_step.step_id == "a_step2"
        assert response.begin_step.session_id == session_a_id

        # Session B should still be on top and untouched
        top_session = tools.state_manager.get_active_session()
        assert top_session is not None
        assert top_session.session_id == session_b_id
        assert top_session.current_step_id == "b_step1"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.6.3, REQ-001.6.5, REQ-001.6.6, REQ-001.6.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_workflow_with_session_id(
        self, tools: WorkflowTools, project_root: Path
    ) -> None:
        """Test abort_workflow targets a specific session by session_id."""
        # Start two workflows
        resp_a = await tools.start_workflow(
            StartWorkflowInput(goal="Do A", job_name="job_a", workflow_name="main")
        )
        session_a_id = resp_a.begin_step.session_id

        resp_b = await tools.start_workflow(
            StartWorkflowInput(goal="Do B", job_name="job_b", workflow_name="main")
        )
        session_b_id = resp_b.begin_step.session_id

        # Abort session_a (not on top) by ID
        response = await tools.abort_workflow(
            AbortWorkflowInput(
                explanation="Aborting A",
                session_id=session_a_id,
            )
        )

        assert response.aborted_workflow == "job_a/main"
        assert response.explanation == "Aborting A"

        # Stack should only have session_b now
        assert tools.state_manager.get_stack_depth() == 1
        assert tools.state_manager.get_active_session() is not None
        assert tools.state_manager.get_active_session().session_id == session_b_id


class TestExternalRunnerSelfReview:
    """Tests for self-review mode (external_runner=None) in finished_step."""

    @pytest.fixture
    def tools_self_review(self, project_root: Path, state_manager: StateManager) -> WorkflowTools:
        """Create WorkflowTools with quality gate but no external runner (self-review mode)."""
        from deepwork.jobs.mcp.quality_gate import QualityGate

        return WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=QualityGate(cli=None, max_inline_files=0),
            external_runner=None,
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_returns_needs_work(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that self-review mode returns NEEDS_WORK with instructions."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("Some output")

        response = await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.failed_reviews is None  # No actual review results yet

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_feedback_contains_instructions(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that feedback contains subagent and override instructions."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("Some output")

        response = await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        assert "Quality review required" in response.feedback
        assert "subagent" in response.feedback.lower()
        assert "quality_review_override_reason" in response.feedback
        assert ".deepwork/tmp/quality_review_" in response.feedback

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_writes_instructions_file(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that an instructions file is written to .deepwork/tmp/."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("Some output")

        await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        review_files = list((project_root / ".deepwork" / "tmp").glob("quality_review_*.md"))
        assert len(review_files) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_file_contains_criteria(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that the instructions file contains the quality criteria from the job."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("Some output")

        await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        review_files = list((project_root / ".deepwork" / "tmp").glob("quality_review_*.md"))
        content = review_files[0].read_text()

        # step1 has review criteria "Output Valid": "Is the output valid?"
        assert "Output Valid" in content
        assert "Is the output valid?" in content

    async def test_self_review_file_references_outputs_not_inline(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that the instructions file lists output paths, not inline content."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("UNIQUE_CONTENT_MARKER_12345")

        await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        review_files = list((project_root / ".deepwork" / "tmp").glob("quality_review_*.md"))
        content = review_files[0].read_text()

        assert "output1.md" in content
        assert "UNIQUE_CONTENT_MARKER_12345" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_file_named_with_session_and_step(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that review file name includes session and step IDs."""
        resp = await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        session_id = resp.begin_step.session_id
        (project_root / "output1.md").write_text("output")

        await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        expected_file = project_root / ".deepwork" / "tmp" / f"quality_review_{session_id}_step1.md"
        assert expected_file.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.9, REQ-001.4.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_then_override_completes_workflow(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that calling finished_step with override after self-review advances the workflow."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        # First call: self-review
        resp1 = await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )
        assert resp1.status == StepStatus.NEEDS_WORK

        # Second call: override, should advance to step2
        resp2 = await tools_self_review.finished_step(
            FinishedStepInput(
                outputs={"output1.md": "output1.md"},
                quality_review_override_reason="Self-review passed: all criteria met",
            )
        )
        assert resp2.status == StepStatus.NEXT_STEP
        assert resp2.begin_step.step_id == "step2"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_self_review_skipped_for_steps_without_reviews(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that steps without reviews skip self-review entirely."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        # Override step1 to advance to step2 (which has no reviews)
        await tools_self_review.finished_step(
            FinishedStepInput(
                outputs={"output1.md": "output1.md"},
                quality_review_override_reason="Skip",
            )
        )

        # step2 has no reviews, so it should complete without self-review
        (project_root / "output2.md").write_text("step2 output")
        resp = await tools_self_review.finished_step(
            FinishedStepInput(outputs={"output2.md": "output2.md"})
        )
        assert resp.status == StepStatus.WORKFLOW_COMPLETE

    async def test_self_review_includes_notes_in_file(
        self, tools_self_review: WorkflowTools, project_root: Path
    ) -> None:
        """Test that agent notes are included in the review instructions file."""
        await tools_self_review.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        await tools_self_review.finished_step(
            FinishedStepInput(
                outputs={"output1.md": "output1.md"},
                notes="I used the XYZ library for this step.",
            )
        )

        review_files = list((project_root / ".deepwork" / "tmp").glob("quality_review_*.md"))
        content = review_files[0].read_text()
        assert "I used the XYZ library for this step." in content


class TestExternalRunnerClaude:
    """Tests that external_runner='claude' uses subprocess evaluation (existing behavior)."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.8, REQ-001.4.14).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_claude_runner_calls_quality_gate_evaluate(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that claude runner mode invokes evaluate_reviews on the quality gate."""
        mock_gate = MockQualityGate(should_pass=True)
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        await tools.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        response = await tools.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        # Should have called evaluate_reviews and advanced
        assert response.status == StepStatus.NEXT_STEP
        assert len(mock_gate.evaluations) > 0

    async def test_claude_runner_does_not_write_instructions_file(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that claude runner mode does NOT write an instructions file."""
        mock_gate = MockQualityGate(should_pass=True)
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        await tools.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        await tools.finished_step(FinishedStepInput(outputs={"output1.md": "output1.md"}))

        review_files = list((project_root / ".deepwork" / "tmp").glob("quality_review_*.md"))
        assert len(review_files) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.12).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_claude_runner_failing_gate_returns_feedback(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that claude runner with failing gate returns NEEDS_WORK with review feedback."""
        mock_gate = MockQualityGate(should_pass=False, feedback="Missing detail in section 2")
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        await tools.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        response = await tools.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback == "Missing detail in section 2"
        assert response.failed_reviews is not None
        assert len(response.failed_reviews) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.4.11, REQ-001.4.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_claude_runner_records_quality_attempts(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that claude runner mode tracks quality attempt count."""
        mock_gate = MockQualityGate(should_pass=False, feedback="Fail")
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=mock_gate,
            external_runner="claude",
        )

        await tools.start_workflow(
            StartWorkflowInput(goal="Test", job_name="test_job", workflow_name="main")
        )
        (project_root / "output1.md").write_text("output")

        # First two attempts: NEEDS_WORK
        for _ in range(2):
            resp = await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": "output1.md"})
            )
            assert resp.status == StepStatus.NEEDS_WORK

        # Third attempt: raises ToolError
        with pytest.raises(ToolError, match="Quality gate failed after.*attempts"):
            await tools.finished_step(FinishedStepInput(outputs={"output1.md": "output1.md"}))


class TestExternalRunnerInit:
    """Tests for external_runner parameter on WorkflowTools initialization."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_external_runner_is_none(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that external_runner defaults to None."""
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
        )
        assert tools.external_runner is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_explicit_external_runner(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that external_runner is stored correctly."""
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            external_runner="claude",
        )
        assert tools.external_runner == "claude"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-001.1.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_quality_gate_no_external_runner_skips_review(
        self, project_root: Path, state_manager: StateManager
    ) -> None:
        """Test that without quality gate, external_runner is irrelevant."""
        tools = WorkflowTools(
            project_root=project_root,
            state_manager=state_manager,
            quality_gate=None,
            external_runner=None,
        )
        assert tools.quality_gate is None
        assert tools.external_runner is None
