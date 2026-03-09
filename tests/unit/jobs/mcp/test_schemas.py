"""Tests for MCP schemas."""

from deepwork.jobs.mcp.schemas import (
    ActiveStepInfo,
    ExpectedOutput,
    FinishedStepInput,
    FinishedStepResponse,
    JobInfo,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepInputInfo,
    StepProgress,
    StepStatus,
    WorkflowInfo,
    WorkflowSession,
)


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_enum_values(self) -> None:
        """Test that enum has expected values."""
        assert StepStatus.NEEDS_WORK.value == "needs_work"
        assert StepStatus.NEXT_STEP.value == "next_step"
        assert StepStatus.WORKFLOW_COMPLETE.value == "workflow_complete"


class TestWorkflowInfo:
    """Tests for WorkflowInfo model."""

    def test_basic_workflow(self) -> None:
        """Test basic workflow info with how_to_invoke."""
        workflow = WorkflowInfo(
            name="test_workflow",
            summary="A test workflow",
            how_to_invoke="Call the `start_workflow` DeepWork MCP tool",
        )

        assert workflow.name == "test_workflow"
        assert workflow.summary == "A test workflow"
        assert "start_workflow" in workflow.how_to_invoke

    def test_workflow_with_agent_how_to_invoke(self) -> None:
        """Test workflow info with agent-based how_to_invoke."""
        workflow = WorkflowInfo(
            name="test_workflow",
            summary="A test workflow",
            how_to_invoke='Invoke as a Task using subagent_type="general-purpose"',
        )

        assert "general-purpose" in workflow.how_to_invoke
        assert "Task" in workflow.how_to_invoke


class TestJobInfo:
    """Tests for JobInfo model."""

    def test_basic_job(self) -> None:
        """Test basic job info."""
        job = JobInfo(
            name="test_job",
            summary="A test job",
        )

        assert job.name == "test_job"
        assert job.summary == "A test job"
        assert job.workflows == []


class TestStartWorkflowInput:
    """Tests for StartWorkflowInput model."""

    def test_required_fields(self) -> None:
        """Test required fields only."""
        input_data = StartWorkflowInput(
            goal="Complete a task",
            job_name="test_job",
            workflow_name="main",
            session_id="test-session",
        )

        assert input_data.goal == "Complete a task"
        assert input_data.job_name == "test_job"
        assert input_data.workflow_name == "main"
        assert input_data.session_id == "test-session"
        assert input_data.inputs is None

    def test_with_inputs(self) -> None:
        """Test with inputs parameter."""
        input_data = StartWorkflowInput(
            goal="Complete a task",
            job_name="test_job",
            workflow_name="main",
            session_id="test-session",
            inputs={"source_file": "src/main.py", "targets": ["a.py", "b.py"]},
        )

        assert input_data.inputs is not None
        assert input_data.inputs["source_file"] == "src/main.py"
        assert input_data.inputs["targets"] == ["a.py", "b.py"]


class TestFinishedStepInput:
    """Tests for FinishedStepInput model."""

    def test_with_outputs(self) -> None:
        """Test with structured outputs."""
        input_data = FinishedStepInput(
            outputs={"report": "report.md", "data_files": ["a.csv", "b.csv"]},
            session_id="test-session",
        )

        assert input_data.outputs == {"report": "report.md", "data_files": ["a.csv", "b.csv"]}
        assert input_data.work_summary is None

    def test_with_empty_outputs(self) -> None:
        """Test with empty outputs dict (for steps with no outputs)."""
        input_data = FinishedStepInput(outputs={}, session_id="test-session")

        assert input_data.outputs == {}

    def test_with_work_summary(self) -> None:
        """Test with work_summary field."""
        input_data = FinishedStepInput(
            outputs={"output": "output.md"},
            work_summary="Completed the analysis using approach X",
            session_id="test-session",
        )

        assert input_data.work_summary == "Completed the analysis using approach X"

    def test_with_quality_review_override_reason(self) -> None:
        """Test with quality_review_override_reason field."""
        input_data = FinishedStepInput(
            outputs={"output": "output.md"},
            quality_review_override_reason="Review timed out after 120s",
            session_id="test-session",
        )

        assert input_data.quality_review_override_reason == "Review timed out after 120s"


class TestStepInputInfo:
    """Tests for StepInputInfo model."""

    def test_basic_creation(self) -> None:
        """Test creating a basic step input info."""
        info = StepInputInfo(
            name="source_file",
            type="file_path",
            description="The source file to analyze",
        )

        assert info.name == "source_file"
        assert info.type == "file_path"
        assert info.description == "The source file to analyze"
        assert info.value is None
        assert info.required is True

    def test_with_value(self) -> None:
        """Test step input info with a value."""
        info = StepInputInfo(
            name="source_file",
            type="file_path",
            description="The source file to analyze",
            value="src/main.py",
        )

        assert info.value == "src/main.py"

    def test_with_list_value(self) -> None:
        """Test step input info with a list value."""
        info = StepInputInfo(
            name="targets",
            type="file_path",
            description="Target files",
            value=["a.py", "b.py"],
        )

        assert info.value == ["a.py", "b.py"]

    def test_optional_input(self) -> None:
        """Test step input info that is not required."""
        info = StepInputInfo(
            name="config",
            type="string",
            description="Optional config",
            required=False,
        )

        assert info.required is False


class TestActiveStepInfo:
    """Tests for ActiveStepInfo model."""

    def test_basic_step_info(self) -> None:
        """Test basic active step info."""
        expected = [
            ExpectedOutput(
                name="output.md",
                type="file",
                description="Test output",
                required=True,
                syntax_for_finished_step_tool="filepath",
            )
        ]
        step_inputs = [
            StepInputInfo(
                name="source",
                type="file_path",
                description="Source file",
                value="src/main.py",
            )
        ]
        step_info = ActiveStepInfo(
            session_id="abc123",
            step_id="step1",
            job_dir="/tmp/test_job",
            step_expected_outputs=expected,
            step_inputs=step_inputs,
            step_instructions="Do something",
            common_job_info="Test job info",
        )

        assert step_info.session_id == "abc123"
        assert step_info.step_id == "step1"
        assert step_info.job_dir == "/tmp/test_job"
        assert len(step_info.step_expected_outputs) == 1
        assert step_info.step_expected_outputs[0].name == "output.md"
        assert step_info.step_expected_outputs[0].type == "file"
        assert step_info.step_expected_outputs[0].syntax_for_finished_step_tool == "filepath"
        assert len(step_info.step_inputs) == 1
        assert step_info.step_inputs[0].name == "source"
        assert step_info.step_inputs[0].value == "src/main.py"
        assert step_info.step_instructions == "Do something"
        assert step_info.common_job_info == "Test job info"

    def test_default_step_inputs(self) -> None:
        """Test default empty step_inputs."""
        step_info = ActiveStepInfo(
            session_id="abc123",
            step_id="step1",
            job_dir="/tmp/test_job",
            step_expected_outputs=[
                ExpectedOutput(
                    name="output.md",
                    type="file",
                    description="Test output",
                    required=True,
                    syntax_for_finished_step_tool="filepath",
                )
            ],
            step_instructions="Do something",
        )

        assert step_info.step_inputs == []

    def test_default_common_job_info(self) -> None:
        """Test common_job_info defaults to empty string."""
        step_info = ActiveStepInfo(
            session_id="abc123",
            step_id="step1",
            job_dir="/tmp/test_job",
            step_expected_outputs=[
                ExpectedOutput(
                    name="output.md",
                    type="file",
                    description="Test output",
                    required=True,
                    syntax_for_finished_step_tool="filepath",
                )
            ],
            step_instructions="Do something",
        )

        assert step_info.common_job_info == ""


class TestStartWorkflowResponse:
    """Tests for StartWorkflowResponse model."""

    def test_basic_response(self) -> None:
        """Test basic response."""
        response = StartWorkflowResponse(
            begin_step=ActiveStepInfo(
                session_id="abc123",
                step_id="step1",
                job_dir="/tmp/test_job",
                step_expected_outputs=[
                    ExpectedOutput(
                        name="output.md",
                        type="file",
                        description="Test output",
                        required=True,
                        syntax_for_finished_step_tool="filepath",
                    )
                ],
                step_instructions="Do something",
            )
        )

        assert response.begin_step.session_id == "abc123"
        assert response.begin_step.step_id == "step1"
        assert response.begin_step.step_inputs == []
        assert response.begin_step.common_job_info == ""


class TestFinishedStepResponse:
    """Tests for FinishedStepResponse model."""

    def test_needs_work_status(self) -> None:
        """Test needs_work response with feedback."""
        response = FinishedStepResponse(
            status=StepStatus.NEEDS_WORK,
            feedback="Fix the issues found in the output",
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback == "Fix the issues found in the output"
        assert response.begin_step is None

    def test_next_step_status(self) -> None:
        """Test next_step response."""
        response = FinishedStepResponse(
            status=StepStatus.NEXT_STEP,
            begin_step=ActiveStepInfo(
                session_id="abc123",
                step_id="step2",
                job_dir="/tmp/test_job",
                step_expected_outputs=[
                    ExpectedOutput(
                        name="output2.md",
                        type="file",
                        description="Test output",
                        required=True,
                        syntax_for_finished_step_tool="filepath",
                    )
                ],
                step_instructions="Next step instructions",
                common_job_info="Test job info",
            ),
        )

        assert response.status == StepStatus.NEXT_STEP
        assert response.begin_step is not None
        assert response.begin_step.step_id == "step2"
        assert response.summary is None

    def test_workflow_complete_status(self) -> None:
        """Test workflow_complete response with post_workflow_instructions."""
        response = FinishedStepResponse(
            status=StepStatus.WORKFLOW_COMPLETE,
            summary="Workflow completed!",
            all_outputs={"output1": "output1.md", "output2": "output2.md"},
            post_workflow_instructions="Create a PR with the results",
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE
        assert response.summary == "Workflow completed!"
        assert response.all_outputs == {"output1": "output1.md", "output2": "output2.md"}
        assert response.post_workflow_instructions == "Create a PR with the results"

    def test_workflow_complete_no_post_instructions(self) -> None:
        """Test workflow_complete without post_workflow_instructions."""
        response = FinishedStepResponse(
            status=StepStatus.WORKFLOW_COMPLETE,
            summary="Done",
        )

        assert response.post_workflow_instructions is None


class TestStepProgress:
    """Tests for StepProgress model."""

    def test_new_step(self) -> None:
        """Test new step progress with defaults."""
        progress = StepProgress(step_id="step1")

        assert progress.step_id == "step1"
        assert progress.started_at is None
        assert progress.completed_at is None
        assert progress.outputs == {}
        assert progress.quality_attempts == 0
        assert progress.work_summary is None
        assert progress.input_values == {}

    def test_with_work_summary(self) -> None:
        """Test step progress with work_summary."""
        progress = StepProgress(
            step_id="step1",
            work_summary="Analyzed the codebase and produced report",
        )

        assert progress.work_summary == "Analyzed the codebase and produced report"

    def test_with_input_values(self) -> None:
        """Test step progress with input_values."""
        progress = StepProgress(
            step_id="step1",
            input_values={"source": "main.py", "targets": ["a.py", "b.py"]},
        )

        assert progress.input_values["source"] == "main.py"
        assert progress.input_values["targets"] == ["a.py", "b.py"]


class TestWorkflowSession:
    """Tests for WorkflowSession model."""

    def test_basic_session(self) -> None:
        """Test basic session creation."""
        session = WorkflowSession(
            session_id="abc123",
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            current_step_id="step1",
            started_at="2024-01-01T00:00:00Z",
        )

        assert session.session_id == "abc123"
        assert session.job_name == "test_job"
        assert session.status == "active"
        assert session.completed_at is None
        assert session.current_step_index == 0

    def test_current_step_index(self) -> None:
        """Test current_step_index field."""
        session = WorkflowSession(
            session_id="abc123",
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            current_step_id="step3",
            current_step_index=2,
            started_at="2024-01-01T00:00:00Z",
        )

        assert session.current_step_index == 2

    def test_to_dict(self) -> None:
        """Test converting session to dict."""
        session = WorkflowSession(
            session_id="abc123",
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            current_step_id="step1",
            started_at="2024-01-01T00:00:00Z",
        )

        data = session.to_dict()

        assert isinstance(data, dict)
        assert data["session_id"] == "abc123"
        assert data["job_name"] == "test_job"
        assert data["current_step_index"] == 0

    def test_from_dict(self) -> None:
        """Test creating session from dict."""
        data = {
            "session_id": "abc123",
            "job_name": "test_job",
            "workflow_name": "main",
            "goal": "Complete the task",
            "current_step_id": "step1",
            "current_step_index": 0,
            "step_progress": {},
            "started_at": "2024-01-01T00:00:00Z",
            "completed_at": None,
            "status": "active",
        }

        session = WorkflowSession.from_dict(data)

        assert session.session_id == "abc123"
        assert session.job_name == "test_job"
        assert session.current_step_index == 0
