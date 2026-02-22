"""Tests for MCP state management."""

from pathlib import Path

import pytest

from deepwork.jobs.mcp.state import StateError, StateManager


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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_init(self, state_manager: StateManager, project_root: Path) -> None:
        """Test StateManager initialization."""
        assert state_manager.project_root == project_root
        assert state_manager.sessions_dir == project_root / ".deepwork" / "tmp"
        assert state_manager._session_stack == []
        assert state_manager.get_stack_depth() == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.2.1, REQ-003.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_generate_session_id(self, state_manager: StateManager) -> None:
        """Test session ID generation."""
        session_id = state_manager._generate_session_id()

        assert isinstance(session_id, str)
        assert len(session_id) == 8

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.3.4, REQ-003.3.5, REQ-003.3.8, REQ-003.3.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

        # Verify session file was created
        session_file = state_manager._session_file(session.session_id)
        assert session_file.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.5.1, REQ-003.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_load_session_not_found(self, state_manager: StateManager) -> None:
        """Test loading non-existent session."""
        with pytest.raises(StateError, match="Session not found"):
            await state_manager.load_session("nonexistent")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.6.2, REQ-003.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_require_active_session(self, state_manager: StateManager) -> None:
        """Test require_active_session raises when no session."""
        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.require_active_session()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.8.1, REQ-003.8.2, REQ-003.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.8.5, REQ-003.8.6, REQ-003.8.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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
            outputs={"report": "output1.md", "data": "output2.md"},
            notes="Done!",
        )

        session = state_manager.get_active_session()
        assert session is not None
        progress = session.step_progress["step1"]

        assert progress.completed_at is not None
        assert progress.outputs == {"report": "output1.md", "data": "output2.md"}
        assert progress.notes == "Done!"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.9.1, REQ-003.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.10.1, REQ-003.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.11.1, REQ-003.11.2, REQ-003.11.3, REQ-003.11.4, REQ-003.11.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.14.1, REQ-003.14.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_get_all_outputs(self, state_manager: StateManager) -> None:
        """Test getting all outputs from completed steps."""
        await state_manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.complete_step("step1", {"report": "output1.md"})
        await state_manager.complete_step("step2", {"data_files": ["output2.md", "output3.md"]})

        outputs = state_manager.get_all_outputs()

        assert outputs == {
            "report": "output1.md",
            "data_files": ["output2.md", "output3.md"],
        }
        assert len(outputs) == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.15.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.15.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.16.1, REQ-003.16.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.13.1, REQ-003.13.2, REQ-003.13.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.11.4, REQ-003.11.5, REQ-003.13.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.13.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.12.1, REQ-003.12.2, REQ-003.12.3, REQ-003.12.5, REQ-003.12.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.12.2, REQ-003.12.5, REQ-003.12.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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


class TestSessionIdRouting:
    """Tests for session_id-based routing in StateManager."""

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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_resolve_session_by_id(self, state_manager: StateManager) -> None:
        """Test _resolve_session finds the correct session in a multi-session stack."""
        import asyncio

        async def setup() -> None:
            await state_manager.create_session(
                job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
            )
            await state_manager.create_session(
                job_name="job2", workflow_name="wf2", goal="G2", first_step_id="s2"
            )
            await state_manager.create_session(
                job_name="job3", workflow_name="wf3", goal="G3", first_step_id="s3"
            )

        asyncio.get_event_loop().run_until_complete(setup())

        # Stack has 3 sessions; resolve the middle one by ID
        middle_session = state_manager._session_stack[1]
        resolved = state_manager._resolve_session(middle_session.session_id)
        assert resolved.session_id == middle_session.session_id
        assert resolved.job_name == "job2"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_resolve_session_invalid_id(self, state_manager: StateManager) -> None:
        """Test _resolve_session raises StateError for unknown session ID."""
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            state_manager.create_session(
                job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
            )
        )

        with pytest.raises(StateError, match="Session 'nonexistent' not found"):
            state_manager._resolve_session("nonexistent")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_resolve_session_none_falls_back_to_active(self, state_manager: StateManager) -> None:
        """Test _resolve_session with None falls back to top-of-stack."""
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            state_manager.create_session(
                job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
            )
        )
        asyncio.get_event_loop().run_until_complete(
            state_manager.create_session(
                job_name="job2", workflow_name="wf2", goal="G2", first_step_id="s2"
            )
        )

        resolved = state_manager._resolve_session(None)
        assert resolved.job_name == "job2"  # top-of-stack

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.4, REQ-003.11.4, REQ-003.13.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_workflow_by_session_id(self, state_manager: StateManager) -> None:
        """Test complete_workflow removes a specific session from middle of stack."""
        session1 = await state_manager.create_session(
            job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
        )
        session2 = await state_manager.create_session(
            job_name="job2", workflow_name="wf2", goal="G2", first_step_id="s2"
        )
        session3 = await state_manager.create_session(
            job_name="job3", workflow_name="wf3", goal="G3", first_step_id="s3"
        )

        assert state_manager.get_stack_depth() == 3

        # Complete the middle session by ID
        new_active = await state_manager.complete_workflow(session_id=session2.session_id)

        assert state_manager.get_stack_depth() == 2
        # Stack should have session1 and session3; top is session3
        assert new_active is not None
        assert new_active.session_id == session3.session_id
        assert state_manager.get_active_session() == session3
        remaining_ids = [s.session_id for s in state_manager._session_stack]
        assert session1.session_id in remaining_ids
        assert session2.session_id not in remaining_ids
        assert session3.session_id in remaining_ids

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.4, REQ-003.12.2, REQ-003.12.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_workflow_by_session_id(self, state_manager: StateManager) -> None:
        """Test abort_workflow removes a specific session from middle of stack."""
        session1 = await state_manager.create_session(
            job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
        )
        session2 = await state_manager.create_session(
            job_name="job2", workflow_name="wf2", goal="G2", first_step_id="s2"
        )
        session3 = await state_manager.create_session(
            job_name="job3", workflow_name="wf3", goal="G3", first_step_id="s3"
        )

        # Abort the middle session
        aborted, new_active = await state_manager.abort_workflow(
            "Testing mid-stack abort", session_id=session2.session_id
        )

        assert aborted.session_id == session2.session_id
        assert aborted.status == "aborted"
        assert state_manager.get_stack_depth() == 2
        # Top of stack should still be session3
        assert new_active is not None
        assert new_active.session_id == session3.session_id
        remaining_ids = [s.session_id for s in state_manager._session_stack]
        assert session1.session_id in remaining_ids
        assert session2.session_id not in remaining_ids

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-003.7.4, REQ-003.8.5, REQ-003.8.6, REQ-003.8.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_step_with_session_id(self, state_manager: StateManager) -> None:
        """Test complete_step operates on a non-top session when session_id is given."""
        session1 = await state_manager.create_session(
            job_name="job1", workflow_name="wf1", goal="G1", first_step_id="s1"
        )
        await state_manager.create_session(
            job_name="job2", workflow_name="wf2", goal="G2", first_step_id="s2"
        )

        # Complete step on session1 (not on top) using session_id
        await state_manager.complete_step(
            step_id="s1",
            outputs={"report": "report.md"},
            notes="Done",
            session_id=session1.session_id,
        )

        # Verify session1 was updated
        progress = session1.step_progress["s1"]
        assert progress.completed_at is not None
        assert progress.outputs == {"report": "report.md"}

        # Verify session2 (top) was not affected
        top = state_manager.get_active_session()
        assert top is not None
        assert "s1" not in top.step_progress
