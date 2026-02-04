"""Tests for MCP state management."""

from pathlib import Path

import pytest

from deepwork.mcp.state import StateError, StateManager


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with .deepwork directory."""
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()
    return tmp_path


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    """Create a StateManager instance."""
    return StateManager(project_root)


class TestStateManager:
    """Tests for StateManager class."""

    def test_init(self, state_manager: StateManager, project_root: Path) -> None:
        """Test StateManager initialization."""
        assert state_manager.project_root == project_root
        assert state_manager.sessions_dir == project_root / ".deepwork" / "tmp"
        assert state_manager._session_stack == []
        assert state_manager.get_stack_depth() == 0

    def test_generate_session_id(self, state_manager: StateManager) -> None:
        """Test session ID generation."""
        session_id = state_manager._generate_session_id()

        assert isinstance(session_id, str)
        assert len(session_id) == 8

    def test_generate_branch_name_with_instance(self, state_manager: StateManager) -> None:
        """Test branch name generation with instance ID."""
        branch = state_manager._generate_branch_name("test_job", "main", "acme")

        assert branch == "deepwork/test_job-main-acme"

    def test_generate_branch_name_without_instance(self, state_manager: StateManager) -> None:
        """Test branch name generation without instance ID (uses date)."""
        branch = state_manager._generate_branch_name("test_job", "main", None)

        assert branch.startswith("deepwork/test_job-main-")
        # Should be a date like 20240101
        assert len(branch.split("-")[-1]) == 8

    async def test_create_session(self, state_manager: StateManager) -> None:
        """Test creating a new session."""
        session = await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
            instance_id="acme",
        )

        assert session.job_name == "test_job"
        assert session.workflow_name == "main"
        assert session.goal == "Complete the task"
        assert session.current_step_id == "step1"
        assert session.instance_id == "acme"
        assert session.status == "active"
        assert "acme" in session.branch_name

        # Verify session file was created
        session_file = state_manager._session_file(session.session_id)
        assert session_file.exists()

    async def test_load_session(self, state_manager: StateManager) -> None:
        """Test loading an existing session."""
        # Create a session first
        created_session = await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # Create a new state manager and load the session
        new_manager = StateManager(state_manager.project_root)
        loaded_session = await new_manager.load_session(created_session.session_id)

        assert loaded_session.session_id == created_session.session_id
        assert loaded_session.job_name == "test_job"
        assert loaded_session.goal == "Complete the task"

    async def test_load_session_not_found(self, state_manager: StateManager) -> None:
        """Test loading non-existent session."""
        with pytest.raises(StateError, match="Session not found"):
            await state_manager.load_session("nonexistent")

    async def test_get_active_session(self, state_manager: StateManager) -> None:
        """Test getting active session."""
        # No active session initially
        assert state_manager.get_active_session() is None

        # Create session
        session = await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        assert state_manager.get_active_session() == session

    def test_require_active_session(self, state_manager: StateManager) -> None:
        """Test require_active_session raises when no session."""
        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.require_active_session()

    async def test_start_step(self, state_manager: StateManager) -> None:
        """Test marking a step as started."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.start_step("step2")
        session = state_manager.get_active_session()

        assert session is not None
        assert session.current_step_id == "step2"
        assert "step2" in session.step_progress
        assert session.step_progress["step2"].started_at is not None

    async def test_complete_step(self, state_manager: StateManager) -> None:
        """Test marking a step as completed."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.complete_step(
            step_id="step1",
            outputs=["output1.md", "output2.md"],
            notes="Done!",
        )

        session = state_manager.get_active_session()
        assert session is not None
        progress = session.step_progress["step1"]

        assert progress.completed_at is not None
        assert progress.outputs == ["output1.md", "output2.md"]
        assert progress.notes == "Done!"

    async def test_record_quality_attempt(self, state_manager: StateManager) -> None:
        """Test recording quality gate attempts."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # First attempt
        attempts = await state_manager.record_quality_attempt("step1")
        assert attempts == 1

        # Second attempt
        attempts = await state_manager.record_quality_attempt("step1")
        assert attempts == 2

    async def test_advance_to_step(self, state_manager: StateManager) -> None:
        """Test advancing to a new step."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.advance_to_step("step2", 1)
        session = state_manager.get_active_session()

        assert session is not None
        assert session.current_step_id == "step2"
        assert session.current_entry_index == 1

    async def test_complete_workflow(self, state_manager: StateManager) -> None:
        """Test marking workflow as complete pops from stack."""
        session = await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )
        session_id = session.session_id

        # Complete workflow - should pop from stack
        new_active = await state_manager.complete_workflow()

        # No active session after completion
        assert new_active is None
        assert state_manager.get_active_session() is None
        assert state_manager.get_stack_depth() == 0

        # But completed session should be persisted to disk
        loaded = await state_manager.load_session(session_id)
        assert loaded.status == "completed"
        assert loaded.completed_at is not None

    async def test_get_all_outputs(self, state_manager: StateManager) -> None:
        """Test getting all outputs from completed steps."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.complete_step("step1", ["output1.md"])
        await state_manager.complete_step("step2", ["output2.md", "output3.md"])

        outputs = state_manager.get_all_outputs()

        assert "output1.md" in outputs
        assert "output2.md" in outputs
        assert "output3.md" in outputs
        assert len(outputs) == 3

    async def test_list_sessions(self, state_manager: StateManager) -> None:
        """Test listing all sessions."""
        # Create multiple sessions
        await state_manager.create_session(
            job_name="job1",
            workflow_name="main",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            job_name="job2",
            workflow_name="main",
            goal="Goal 2",
            first_step_id="step1",
        )

        sessions = await state_manager.list_sessions()

        assert len(sessions) == 2
        job_names = {s.job_name for s in sessions}
        assert "job1" in job_names
        assert "job2" in job_names

    async def test_find_active_sessions_for_workflow(self, state_manager: StateManager) -> None:
        """Test finding active sessions for a workflow."""
        # Create sessions for different workflows
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="other",
            goal="Goal 2",
            first_step_id="step1",
        )

        sessions = await state_manager.find_active_sessions_for_workflow("test_job", "main")

        assert len(sessions) == 1
        assert sessions[0].workflow_name == "main"

    async def test_delete_session(self, state_manager: StateManager) -> None:
        """Test deleting a session."""
        session = await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Goal",
            first_step_id="step1",
        )

        session_file = state_manager._session_file(session.session_id)
        assert session_file.exists()

        await state_manager.delete_session(session.session_id)

        assert not session_file.exists()
        assert state_manager.get_active_session() is None


class TestStateManagerStack:
    """Tests for stack-based workflow nesting."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project root with .deepwork directory."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        """Create a StateManager instance."""
        return StateManager(project_root)

    async def test_nested_workflows_stack(self, state_manager: StateManager) -> None:
        """Test that starting workflows pushes onto the stack."""
        # Start first workflow
        session1 = await state_manager.create_session(
            job_name="job1",
            workflow_name="workflow1",
            goal="Goal 1",
            first_step_id="step1",
        )

        assert state_manager.get_stack_depth() == 1
        assert state_manager.get_active_session() == session1

        # Start nested workflow
        session2 = await state_manager.create_session(
            job_name="job2",
            workflow_name="workflow2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        assert state_manager.get_stack_depth() == 2
        assert state_manager.get_active_session() == session2

        # Start another nested workflow
        session3 = await state_manager.create_session(
            job_name="job3",
            workflow_name="workflow3",
            goal="Goal 3",
            first_step_id="stepX",
        )

        assert state_manager.get_stack_depth() == 3
        assert state_manager.get_active_session() == session3

    async def test_complete_workflow_pops_stack(self, state_manager: StateManager) -> None:
        """Test that completing a workflow pops from stack and resumes parent."""
        # Start two nested workflows
        session1 = await state_manager.create_session(
            job_name="job1",
            workflow_name="workflow1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            job_name="job2",
            workflow_name="workflow2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        assert state_manager.get_stack_depth() == 2

        # Complete inner workflow
        resumed = await state_manager.complete_workflow()

        assert state_manager.get_stack_depth() == 1
        assert resumed == session1
        assert state_manager.get_active_session() == session1

    async def test_get_stack(self, state_manager: StateManager) -> None:
        """Test get_stack returns workflow/step info."""
        await state_manager.create_session(
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        stack = state_manager.get_stack()

        assert len(stack) == 2
        assert stack[0].workflow == "job1/wf1"
        assert stack[0].step == "step1"
        assert stack[1].workflow == "job2/wf2"
        assert stack[1].step == "stepA"

    async def test_abort_workflow(self, state_manager: StateManager) -> None:
        """Test abort_workflow marks as aborted and pops from stack."""
        session1 = await state_manager.create_session(
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        session2 = await state_manager.create_session(
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        # Abort inner workflow
        aborted, resumed = await state_manager.abort_workflow("Something went wrong")

        assert aborted.session_id == session2.session_id
        assert aborted.status == "aborted"
        assert aborted.abort_reason == "Something went wrong"
        assert resumed == session1
        assert state_manager.get_stack_depth() == 1
        assert state_manager.get_active_session() == session1

    async def test_abort_workflow_no_parent(self, state_manager: StateManager) -> None:
        """Test abort_workflow with no parent workflow."""
        session = await state_manager.create_session(
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )

        aborted, resumed = await state_manager.abort_workflow("Cancelled")

        assert aborted.session_id == session.session_id
        assert aborted.status == "aborted"
        assert resumed is None
        assert state_manager.get_stack_depth() == 0
        assert state_manager.get_active_session() is None
