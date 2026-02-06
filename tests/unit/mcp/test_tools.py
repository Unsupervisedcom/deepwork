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
      output1.md:
        type: file
        description: First step output
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
        assert "test-instance" in response.begin_step.branch_name
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

    async def test_start_workflow_invalid_job(self, tools: WorkflowTools) -> None:
        """Test starting workflow with invalid job."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="nonexistent",
            workflow_name="main",
        )

        with pytest.raises(ToolError, match="Job not found"):
            await tools.start_workflow(input_data)

    async def test_start_workflow_auto_selects_single_workflow(
        self, tools: WorkflowTools
    ) -> None:
        """Test that a wrong workflow name auto-selects when job has one workflow."""
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="test_job",
            workflow_name="nonexistent",
        )

        # Should succeed by auto-selecting the only workflow ("main")
        response = await tools.start_workflow(input_data)
        assert response.begin_step.step_id == "step1"

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
description: Test job with multiple workflows

steps:
  - id: step_a
    name: Step A
    description: Step A
    instructions_file: steps/step_a.md
    outputs:
      output_a.md:
        type: file
        description: Step A output
    reviews: []
  - id: step_b
    name: Step B
    description: Step B
    instructions_file: steps/step_b.md
    outputs:
      output_b.md:
        type: file
        description: Step B output
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

        tools = WorkflowTools(
            project_root=project_root, state_manager=state_manager
        )
        input_data = StartWorkflowInput(
            goal="Complete task",
            job_name="multi_wf_job",
            workflow_name="nonexistent",
        )

        with pytest.raises(ToolError, match="Workflow.*not found.*alpha.*beta"):
            await tools.start_workflow(input_data)

    async def test_finished_step_no_session(self, tools: WorkflowTools) -> None:
        """Test finished_step without active session."""
        input_data = FinishedStepInput(outputs={"output1.md": "output1.md"})

        with pytest.raises(StateError, match="No active workflow session"):
            await tools.finished_step(input_data)

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

    async def test_finished_step_with_quality_gate_fail(
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
        await tools.start_workflow(start_input)

        # Create output and finish step
        (project_root / "output1.md").write_text("Invalid output")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"output1.md": "output1.md"})
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback == "Needs improvement"
        assert response.failed_reviews is not None

    async def test_finished_step_quality_gate_max_attempts(
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
            await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": "output1.md"})
            )

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
                FinishedStepInput(
                    outputs={"output1.md": "output1.md", "extra.md": "extra.md"}
                )
            )

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
            await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": ["output1.md"]})
            )

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
            await tools.finished_step(
                FinishedStepInput(outputs={"output1.md": "nonexistent.md"})
            )

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
description: Test job

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
description: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
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
            await tools.finished_step(
                FinishedStepInput(outputs={"reports": "report1.md"})
            )

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
description: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
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
                FinishedStepInput(
                    outputs={"reports": ["report1.md", "missing.md"]}
                )
            )

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
description: Test job

steps:
  - id: generate
    name: Generate
    description: Generates multiple files
    instructions_file: steps/generate.md
    outputs:
      reports:
        type: files
        description: Generated report files
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
            FinishedStepInput(
                outputs={"reports": ["report1.md", "report2.md"]}
            )
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
description: Test job

steps:
  - id: step1
    name: Step 1
    description: First step
    instructions_file: steps/step1.md
    outputs:
      step1_output.md:
        type: file
        description: Step 1 output
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
        await tools.finished_step(
            FinishedStepInput(outputs={"step1_output.md": "step1_output.md"})
        )

        # Complete step2
        (project_root / "step2_output.md").write_text("STEP2_CONTENT_MARKER")
        await tools.finished_step(
            FinishedStepInput(outputs={"step2_output.md": "step2_output.md"})
        )

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
description: Test job

steps:
  - id: write
    name: Write Report
    description: Write a report
    instructions_file: steps/write.md
    outputs:
      report.md:
        type: file
        description: The report
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
        )

        await tools.start_workflow(
            StartWorkflowInput(
                goal="Write report",
                job_name="guided_job",
                workflow_name="main",
            )
        )

        (project_root / "report.md").write_text("Report content")
        response = await tools.finished_step(
            FinishedStepInput(outputs={"report.md": "report.md"})
        )

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
description: Test job

steps:
  - id: analyze
    name: Analyze
    description: Analyze data
    instructions_file: steps/analyze.md
    outputs:
      analysis.md:
        type: file
        description: Analysis output
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
