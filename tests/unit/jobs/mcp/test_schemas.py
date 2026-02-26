"""Tests for MCP schemas."""

from deepwork.jobs.mcp.schemas import (
    ActiveStepInfo,
    ExpectedOutput,
    FinishedStepInput,
    FinishedStepResponse,
    JobInfo,
    QualityCriteriaResult,
    QualityGateResult,
    ReviewInfo,
    ReviewResult,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepInfo,
    StepProgress,
    StepStatus,
    WorkflowInfo,
    WorkflowSession,
    WorkflowStepEntryInfo,
)


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_enum_values(self) -> None:
        """Test that enum has expected values."""
        assert StepStatus.NEEDS_WORK == "needs_work"
        assert StepStatus.NEXT_STEP == "next_step"
        assert StepStatus.WORKFLOW_COMPLETE == "workflow_complete"


class TestStepInfo:
    """Tests for StepInfo model."""

    def test_basic_step(self) -> None:
        """Test creating basic step info."""
        step = StepInfo(
            id="step1",
            name="First Step",
            description="Does something",
        )

        assert step.id == "step1"
        assert step.name == "First Step"
        assert step.description == "Does something"
        assert step.dependencies == []

    def test_step_with_dependencies(self) -> None:
        """Test step with dependencies."""
        step = StepInfo(
            id="step2",
            name="Second Step",
            description="Depends on step1",
            dependencies=["step1"],
        )

        assert step.dependencies == ["step1"]


class TestWorkflowStepEntryInfo:
    """Tests for WorkflowStepEntryInfo model."""

    def test_sequential_entry(self) -> None:
        """Test sequential step entry."""
        entry = WorkflowStepEntryInfo(step_ids=["step1"])

        assert entry.step_ids == ["step1"]
        assert entry.is_concurrent is False

    def test_concurrent_entry(self) -> None:
        """Test concurrent step entry."""
        entry = WorkflowStepEntryInfo(
            step_ids=["step1", "step2"],
            is_concurrent=True,
        )

        assert entry.step_ids == ["step1", "step2"]
        assert entry.is_concurrent is True


class TestWorkflowInfo:
    """Tests for WorkflowInfo model."""

    def test_basic_workflow(self) -> None:
        """Test basic workflow info."""
        workflow = WorkflowInfo(
            name="test_workflow",
            summary="A test workflow",
        )

        assert workflow.name == "test_workflow"
        assert workflow.summary == "A test workflow"
        assert workflow.how_to_invoke is None

    def test_workflow_with_how_to_invoke(self) -> None:
        """Test workflow info with how_to_invoke field."""
        workflow = WorkflowInfo(
            name="test_workflow",
            summary="A test workflow",
            how_to_invoke='Invoke as a Task using subagent_type="general-purpose"',
        )

        assert workflow.how_to_invoke is not None
        assert "general-purpose" in workflow.how_to_invoke


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
        )

        assert input_data.goal == "Complete a task"
        assert input_data.job_name == "test_job"
        assert input_data.workflow_name == "main"
        assert input_data.instance_id is None

    def test_with_instance_id(self) -> None:
        """Test with optional instance_id."""
        input_data = StartWorkflowInput(
            goal="Complete a task",
            job_name="test_job",
            workflow_name="main",
            instance_id="acme",
        )

        assert input_data.instance_id == "acme"


class TestFinishedStepInput:
    """Tests for FinishedStepInput model."""

    def test_with_outputs(self) -> None:
        """Test with structured outputs."""
        input_data = FinishedStepInput(
            outputs={"report": "report.md", "data_files": ["a.csv", "b.csv"]}
        )

        assert input_data.outputs == {"report": "report.md", "data_files": ["a.csv", "b.csv"]}
        assert input_data.notes is None

    def test_with_empty_outputs(self) -> None:
        """Test with empty outputs dict (for steps with no outputs)."""
        input_data = FinishedStepInput(outputs={})

        assert input_data.outputs == {}

    def test_with_notes(self) -> None:
        """Test with notes."""
        input_data = FinishedStepInput(
            outputs={"output": "output.md"},
            notes="Completed successfully",
        )

        assert input_data.notes == "Completed successfully"


class TestQualityCriteriaResult:
    """Tests for QualityCriteriaResult model."""

    def test_passed_criterion(self) -> None:
        """Test passed criterion."""
        result = QualityCriteriaResult(
            criterion="Output must be valid",
            passed=True,
        )

        assert result.passed is True
        assert result.feedback is None

    def test_failed_criterion(self) -> None:
        """Test failed criterion with feedback."""
        result = QualityCriteriaResult(
            criterion="Output must be valid",
            passed=False,
            feedback="Output was incomplete",
        )

        assert result.passed is False
        assert result.feedback == "Output was incomplete"


class TestQualityGateResult:
    """Tests for QualityGateResult model."""

    def test_passed_gate(self) -> None:
        """Test passed quality gate."""
        result = QualityGateResult(
            passed=True,
            feedback="All criteria met",
            criteria_results=[
                QualityCriteriaResult(criterion="Test 1", passed=True),
            ],
        )

        assert result.passed is True
        assert len(result.criteria_results) == 1

    def test_failed_gate(self) -> None:
        """Test failed quality gate."""
        result = QualityGateResult(
            passed=False,
            feedback="Some criteria failed",
            criteria_results=[
                QualityCriteriaResult(criterion="Test 1", passed=True),
                QualityCriteriaResult(
                    criterion="Test 2",
                    passed=False,
                    feedback="Failed check",
                ),
            ],
        )

        assert result.passed is False
        assert len(result.criteria_results) == 2


class TestReviewInfo:
    """Tests for ReviewInfo model."""

    def test_step_review(self) -> None:
        """Test step-level review info."""
        review = ReviewInfo(
            run_each="step",
            quality_criteria={"Complete": "Is it complete?"},
        )

        assert review.run_each == "step"
        assert review.quality_criteria == {"Complete": "Is it complete?"}

    def test_output_review(self) -> None:
        """Test output-specific review info."""
        review = ReviewInfo(
            run_each="reports",
            quality_criteria={
                "Valid": "Is it valid?",
                "Complete": "Is it complete?",
            },
        )

        assert review.run_each == "reports"
        assert len(review.quality_criteria) == 2


class TestReviewResult:
    """Tests for ReviewResult model."""

    def test_passed_review(self) -> None:
        """Test passed review result."""
        result = ReviewResult(
            review_run_each="step",
            target_file=None,
            passed=True,
            feedback="All good",
        )

        assert result.passed is True
        assert result.target_file is None

    def test_failed_per_file_review(self) -> None:
        """Test failed per-file review result."""
        result = ReviewResult(
            review_run_each="reports",
            target_file="report1.md",
            passed=False,
            feedback="Issues found",
            criteria_results=[
                QualityCriteriaResult(criterion="Valid", passed=False, feedback="Not valid"),
            ],
        )

        assert result.passed is False
        assert result.target_file == "report1.md"
        assert result.review_run_each == "reports"
        assert len(result.criteria_results) == 1


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
        step_info = ActiveStepInfo(
            session_id="abc123",
            step_id="step1",
            job_dir="/tmp/test_job",
            step_expected_outputs=expected,
            step_reviews=[
                ReviewInfo(
                    run_each="step",
                    quality_criteria={"Complete": "Is it complete?"},
                )
            ],
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
        assert len(step_info.step_reviews) == 1
        assert step_info.step_reviews[0].run_each == "step"
        assert step_info.step_instructions == "Do something"
        assert step_info.common_job_info == "Test job info"

    def test_default_reviews(self) -> None:
        """Test default empty reviews."""
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
            common_job_info="Test job info",
        )

        assert step_info.step_reviews == []


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
                common_job_info="Test job info",
            )
        )

        assert response.begin_step.session_id == "abc123"

        assert response.begin_step.step_id == "step1"
        assert response.begin_step.step_reviews == []


class TestFinishedStepResponse:
    """Tests for FinishedStepResponse model."""

    def test_needs_work_status(self) -> None:
        """Test needs_work response."""
        response = FinishedStepResponse(
            status=StepStatus.NEEDS_WORK,
            feedback="Fix the issues",
            failed_reviews=[
                ReviewResult(
                    review_run_each="step",
                    target_file=None,
                    passed=False,
                    feedback="Issues found",
                    criteria_results=[
                        QualityCriteriaResult(criterion="Test", passed=False, feedback="Failed"),
                    ],
                ),
            ],
        )

        assert response.status == StepStatus.NEEDS_WORK
        assert response.feedback is not None
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
        """Test workflow_complete response."""
        response = FinishedStepResponse(
            status=StepStatus.WORKFLOW_COMPLETE,
            summary="Workflow completed!",
            all_outputs={"output1": "output1.md", "output2": "output2.md"},
        )

        assert response.status == StepStatus.WORKFLOW_COMPLETE
        assert response.summary is not None
        assert response.all_outputs is not None
        assert response.all_outputs == {"output1": "output1.md", "output2": "output2.md"}


class TestStepProgress:
    """Tests for StepProgress model."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.18.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_new_step(self) -> None:
        """Test new step progress."""
        progress = StepProgress(step_id="step1")

        assert progress.step_id == "step1"
        assert progress.started_at is None
        assert progress.completed_at is None
        assert progress.outputs == {}
        assert progress.quality_attempts == 0


class TestWorkflowSession:
    """Tests for WorkflowSession model."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.18.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.18.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.18.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_from_dict(self) -> None:
        """Test creating session from dict."""
        data = {
            "session_id": "abc123",
            "job_name": "test_job",
            "workflow_name": "main",
            "goal": "Complete the task",
            "current_step_id": "step1",
            "current_entry_index": 0,
            "step_progress": {},
            "started_at": "2024-01-01T00:00:00Z",
            "completed_at": None,
            "status": "active",
        }

        session = WorkflowSession.from_dict(data)

        assert session.session_id == "abc123"
        assert session.job_name == "test_job"
