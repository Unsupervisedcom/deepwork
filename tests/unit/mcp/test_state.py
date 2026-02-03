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
        assert state_manager._active_session is None

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

    def test_create_session(self, state_manager: StateManager) -> None:
        """Test creating a new session."""
        session = state_manager.create_session(
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

    def test_load_session(self, state_manager: StateManager) -> None:
        """Test loading an existing session."""
        # Create a session first
        created_session = state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # Create a new state manager and load the session
        new_manager = StateManager(state_manager.project_root)
        loaded_session = new_manager.load_session(created_session.session_id)

        assert loaded_session.session_id == created_session.session_id
        assert loaded_session.job_name == "test_job"
        assert loaded_session.goal == "Complete the task"

    def test_load_session_not_found(self, state_manager: StateManager) -> None:
        """Test loading non-existent session."""
        with pytest.raises(StateError, match="Session not found"):
            state_manager.load_session("nonexistent")

    def test_get_active_session(self, state_manager: StateManager) -> None:
        """Test getting active session."""
        # No active session initially
        assert state_manager.get_active_session() is None

        # Create session
        session = state_manager.create_session(
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

    def test_start_step(self, state_manager: StateManager) -> None:
        """Test marking a step as started."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        state_manager.start_step("step2")
        session = state_manager.get_active_session()

        assert session is not None
        assert session.current_step_id == "step2"
        assert "step2" in session.step_progress
        assert session.step_progress["step2"].started_at is not None

    def test_complete_step(self, state_manager: StateManager) -> None:
        """Test marking a step as completed."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        state_manager.complete_step(
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

    def test_record_quality_attempt(self, state_manager: StateManager) -> None:
        """Test recording quality gate attempts."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # First attempt
        attempts = state_manager.record_quality_attempt("step1")
        assert attempts == 1

        # Second attempt
        attempts = state_manager.record_quality_attempt("step1")
        assert attempts == 2

    def test_advance_to_step(self, state_manager: StateManager) -> None:
        """Test advancing to a new step."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        state_manager.advance_to_step("step2", 1)
        session = state_manager.get_active_session()

        assert session is not None
        assert session.current_step_id == "step2"
        assert session.current_entry_index == 1

    def test_complete_workflow(self, state_manager: StateManager) -> None:
        """Test marking workflow as complete."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        state_manager.complete_workflow()
        session = state_manager.get_active_session()

        assert session is not None
        assert session.status == "completed"
        assert session.completed_at is not None

    def test_get_all_outputs(self, state_manager: StateManager) -> None:
        """Test getting all outputs from completed steps."""
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        state_manager.complete_step("step1", ["output1.md"])
        state_manager.complete_step("step2", ["output2.md", "output3.md"])

        outputs = state_manager.get_all_outputs()

        assert "output1.md" in outputs
        assert "output2.md" in outputs
        assert "output3.md" in outputs
        assert len(outputs) == 3

    def test_list_sessions(self, state_manager: StateManager) -> None:
        """Test listing all sessions."""
        # Create multiple sessions
        state_manager.create_session(
            job_name="job1",
            workflow_name="main",
            goal="Goal 1",
            first_step_id="step1",
        )
        state_manager.create_session(
            job_name="job2",
            workflow_name="main",
            goal="Goal 2",
            first_step_id="step1",
        )

        sessions = state_manager.list_sessions()

        assert len(sessions) == 2
        job_names = {s.job_name for s in sessions}
        assert "job1" in job_names
        assert "job2" in job_names

    def test_find_active_sessions_for_workflow(self, state_manager: StateManager) -> None:
        """Test finding active sessions for a workflow."""
        # Create sessions for different workflows
        state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Goal 1",
            first_step_id="step1",
        )
        state_manager.create_session(
            job_name="test_job",
            workflow_name="other",
            goal="Goal 2",
            first_step_id="step1",
        )

        sessions = state_manager.find_active_sessions_for_workflow("test_job", "main")

        assert len(sessions) == 1
        assert sessions[0].workflow_name == "main"

    def test_delete_session(self, state_manager: StateManager) -> None:
        """Test deleting a session."""
        session = state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Goal",
            first_step_id="step1",
        )

        session_file = state_manager._session_file(session.session_id)
        assert session_file.exists()

        state_manager.delete_session(session.session_id)

        assert not session_file.exists()
        assert state_manager.get_active_session() is None
