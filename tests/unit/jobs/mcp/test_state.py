"""Tests for MCP state management.

Validates requirements: JOBS-REQ-003, JOBS-REQ-003.1, JOBS-REQ-003.2, JOBS-REQ-003.3,
JOBS-REQ-003.4, JOBS-REQ-003.5, JOBS-REQ-003.6, JOBS-REQ-003.7, JOBS-REQ-003.8,
JOBS-REQ-003.9, JOBS-REQ-003.10, JOBS-REQ-003.11, JOBS-REQ-003.12, JOBS-REQ-003.13,
JOBS-REQ-003.14, JOBS-REQ-003.15, JOBS-REQ-003.16, JOBS-REQ-003.17.
"""

import json
from pathlib import Path

import pytest

from deepwork.jobs.mcp.state import StateError, StateManager

SESSION_ID = "test-session-001"
SESSION_ID_2 = "test-session-002"
AGENT_ID = "agent-abc"
AGENT_ID_2 = "agent-xyz"


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
    return StateManager(project_root=project_root, platform="test")


class TestStateManager:
    """Tests for StateManager class."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.1.1, JOBS-REQ-003.1.2, JOBS-REQ-003.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_init(self, state_manager: StateManager, project_root: Path) -> None:
        """Test StateManager initialization."""
        assert state_manager.project_root == project_root
        assert state_manager.platform == "test"
        assert (
            state_manager.sessions_dir == project_root / ".deepwork" / "tmp" / "sessions" / "test"
        )
        assert state_manager.get_stack_depth(SESSION_ID) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.3.5, JOBS-REQ-003.3.8, JOBS-REQ-003.3.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_create_session(self, state_manager: StateManager) -> None:
        """Test creating a new session."""
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        assert session.session_id == SESSION_ID
        assert session.job_name == "test_job"
        assert session.workflow_name == "main"
        assert session.goal == "Complete the task"
        assert session.current_step_id == "step1"
        assert session.status == "active"

        # Verify state file was created
        state_file = state_manager._state_file(SESSION_ID)
        assert state_file.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.5.1, JOBS-REQ-003.5.6, JOBS-REQ-003.17.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_state_persists_across_manager_instances(
        self, state_manager: StateManager, project_root: Path
    ) -> None:
        """Test state persists across StateManager instances."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # Create a new state manager and resolve the session
        new_manager = StateManager(project_root=project_root, platform="test")
        loaded = new_manager.resolve_session(SESSION_ID)

        assert loaded.session_id == SESSION_ID
        assert loaded.job_name == "test_job"
        assert loaded.goal == "Complete the task"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.5.2, JOBS-REQ-003.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_resolve_session_not_found(self, state_manager: StateManager) -> None:
        """Test resolving non-existent session."""
        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.resolve_session("nonexistent")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.5.1, JOBS-REQ-003.5.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_resolve_session(self, state_manager: StateManager) -> None:
        """Test resolving the active session."""
        # No active session initially
        with pytest.raises(StateError):
            state_manager.resolve_session(SESSION_ID)

        # Create session
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        resolved = state_manager.resolve_session(SESSION_ID)
        assert resolved.job_name == session.job_name

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.5.3, JOBS-REQ-003.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_resolve_session_no_session(self, state_manager: StateManager) -> None:
        """Test resolve_session raises when no session."""
        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.resolve_session(SESSION_ID)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.7.1, JOBS-REQ-003.7.2, JOBS-REQ-003.7.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_step(self, state_manager: StateManager) -> None:
        """Test marking a step as started."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.start_step(SESSION_ID, "step2")
        session = state_manager.resolve_session(SESSION_ID)

        assert session.current_step_id == "step2"
        assert "step2" in session.step_progress
        assert session.step_progress["step2"].started_at is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.7.5, JOBS-REQ-003.7.6, JOBS-REQ-003.7.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_step_with_input_values(self, state_manager: StateManager) -> None:
        """Test that start_step stores input_values in step progress."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        input_vals: dict[str, str | list[str]] = {"query": "test query", "limit": "10"}
        await state_manager.start_step(SESSION_ID, "step2", input_values=input_vals)
        session = state_manager.resolve_session(SESSION_ID)

        assert session.current_step_id == "step2"
        progress = session.step_progress["step2"]
        assert progress.input_values == {"query": "test query", "limit": "10"}

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.8.1, JOBS-REQ-003.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_step(self, state_manager: StateManager) -> None:
        """Test marking a step as completed."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.complete_step(
            session_id=SESSION_ID,
            step_id="step1",
            outputs={"report": "output1.md", "data": "output2.md"},
            work_summary="Done!",
        )

        session = state_manager.resolve_session(SESSION_ID)
        progress = session.step_progress["step1"]

        assert progress.completed_at is not None
        assert progress.outputs == {"report": "output1.md", "data": "output2.md"}
        assert progress.work_summary == "Done!"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.9.1, JOBS-REQ-003.9.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_record_quality_attempt(self, state_manager: StateManager) -> None:
        """Test recording quality gate attempts."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # First attempt
        attempts = await state_manager.record_quality_attempt(SESSION_ID, "step1")
        assert attempts == 1

        # Second attempt
        attempts = await state_manager.record_quality_attempt(SESSION_ID, "step1")
        assert attempts == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.10.1, JOBS-REQ-003.10.2, JOBS-REQ-003.10.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_advance_to_step(self, state_manager: StateManager) -> None:
        """Test advancing to a new step."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.advance_to_step(SESSION_ID, "step2", 1)
        session = state_manager.resolve_session(SESSION_ID)

        assert session.current_step_id == "step2"
        assert session.current_step_index == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.13.1, JOBS-REQ-003.13.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_workflow(self, state_manager: StateManager) -> None:
        """Test marking workflow as complete pops from stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        # Complete workflow — should pop from stack
        new_active = await state_manager.complete_workflow(SESSION_ID)

        # No active session after completion
        assert new_active is None
        assert state_manager.get_stack_depth(SESSION_ID) == 0

        # State file should still exist (stack is empty but file persists)
        state_file = state_manager._state_file(SESSION_ID)
        assert state_file.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.12.1, JOBS-REQ-003.12.2, JOBS-REQ-003.12.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_get_all_outputs(self, state_manager: StateManager) -> None:
        """Test getting all outputs from completed steps."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        await state_manager.complete_step(SESSION_ID, "step1", {"report": "output1.md"})
        await state_manager.complete_step(
            SESSION_ID, "step2", {"data_files": ["output2.md", "output3.md"]}
        )

        outputs = state_manager.get_all_outputs(SESSION_ID)

        assert outputs == {
            "report": "output1.md",
            "data_files": ["output2.md", "output3.md"],
        }
        assert len(outputs) == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.10.1, JOBS-REQ-003.10.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_get_step_input_values(self, state_manager: StateManager) -> None:
        """Test retrieving stored input values for a step."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Complete the task",
            first_step_id="step1",
        )

        input_vals: dict[str, str | list[str]] = {"target": "competitor_x", "depth": "deep"}
        await state_manager.start_step(SESSION_ID, "step1", input_values=input_vals)

        retrieved = state_manager.get_step_input_values(SESSION_ID, "step1")
        assert retrieved == {"target": "competitor_x", "depth": "deep"}

        # Non-existent step returns empty dict
        retrieved_empty = state_manager.get_step_input_values(SESSION_ID, "nonexistent_step")
        assert retrieved_empty == {}


class TestStateManagerStack:
    """Tests for stack-based workflow nesting."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.12.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_nested_workflows_stack(self, state_manager: StateManager) -> None:
        """Test that starting workflows pushes onto the stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="workflow1",
            goal="Goal 1",
            first_step_id="step1",
        )

        assert state_manager.get_stack_depth(SESSION_ID) == 1

        # Start nested workflow (same session_id, pushes onto stack)
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="workflow2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        assert state_manager.get_stack_depth(SESSION_ID) == 2

        # Start another nested workflow
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job3",
            workflow_name="workflow3",
            goal="Goal 3",
            first_step_id="stepX",
        )

        assert state_manager.get_stack_depth(SESSION_ID) == 3

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.11.1, JOBS-REQ-003.11.2, JOBS-REQ-003.11.3, JOBS-REQ-003.11.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_workflow_pops_stack(self, state_manager: StateManager) -> None:
        """Test that completing a workflow pops from stack and resumes parent."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="workflow1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="workflow2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        assert state_manager.get_stack_depth(SESSION_ID) == 2

        # Complete inner workflow
        resumed = await state_manager.complete_workflow(SESSION_ID)

        assert state_manager.get_stack_depth(SESSION_ID) == 1
        assert resumed is not None
        assert resumed.job_name == "job1"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.11.1, JOBS-REQ-003.11.2, JOBS-REQ-003.11.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_get_stack(self, state_manager: StateManager) -> None:
        """Test get_stack returns workflow/step info."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        stack = state_manager.get_stack(SESSION_ID)

        assert len(stack) == 2
        assert stack[0].workflow == "job1/wf1"
        assert stack[0].step == "step1"
        assert stack[1].workflow == "job2/wf2"
        assert stack[1].step == "stepA"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.1, JOBS-REQ-003.6.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_workflow(self, state_manager: StateManager) -> None:
        """Test abort_workflow marks as aborted and pops from stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )

        # Abort inner workflow
        aborted, resumed = await state_manager.abort_workflow(SESSION_ID, "Something went wrong")

        assert aborted.session_id == SESSION_ID
        assert aborted.status == "aborted"
        assert aborted.abort_reason == "Something went wrong"
        assert resumed is not None
        assert resumed.job_name == "job1"
        assert state_manager.get_stack_depth(SESSION_ID) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_workflow_no_parent(self, state_manager: StateManager) -> None:
        """Test abort_workflow with no parent workflow."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )

        aborted, resumed = await state_manager.abort_workflow(SESSION_ID, "Cancelled")

        assert aborted.session_id == SESSION_ID
        assert aborted.status == "aborted"
        assert resumed is None
        assert state_manager.get_stack_depth(SESSION_ID) == 0


class TestAgentIsolation:
    """Tests for sub-agent workflow isolation."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_agent_workflow_isolated_from_main(self, state_manager: StateManager) -> None:
        """Agent workflow doesn't appear in the main stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main_wf",
            goal="Main goal",
            first_step_id="step1",
        )

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent goal",
            first_step_id="agent_step1",
            agent_id=AGENT_ID,
        )

        main_stack = state_manager.get_stack(SESSION_ID)
        assert len(main_stack) == 1
        assert main_stack[0].workflow == "main_job/main_wf"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_agent_stack_includes_main(self, state_manager: StateManager) -> None:
        """get_stack with agent_id returns main stack + agent stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main_wf",
            goal="Main goal",
            first_step_id="step1",
        )

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent goal",
            first_step_id="agent_step1",
            agent_id=AGENT_ID,
        )

        agent_stack = state_manager.get_stack(SESSION_ID, AGENT_ID)
        assert len(agent_stack) == 2
        assert agent_stack[0].workflow == "main_job/main_wf"
        assert agent_stack[1].workflow == "agent_job/agent_wf"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.2.3, JOBS-REQ-003.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_concurrent_agents_isolated(self, state_manager: StateManager) -> None:
        """Two agents don't see each other's workflows."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main_wf",
            goal="Main goal",
            first_step_id="step1",
        )

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_a_job",
            workflow_name="agent_a_wf",
            goal="Agent A goal",
            first_step_id="a_step1",
            agent_id=AGENT_ID,
        )

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_b_job",
            workflow_name="agent_b_wf",
            goal="Agent B goal",
            first_step_id="b_step1",
            agent_id=AGENT_ID_2,
        )

        stack_a = state_manager.get_stack(SESSION_ID, AGENT_ID)
        assert len(stack_a) == 2
        assert stack_a[1].workflow == "agent_a_job/agent_a_wf"

        stack_b = state_manager.get_stack(SESSION_ID, AGENT_ID_2)
        assert len(stack_b) == 2
        assert stack_b[1].workflow == "agent_b_job/agent_b_wf"

        main_stack = state_manager.get_stack(SESSION_ID)
        assert len(main_stack) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.14.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_agent_operations_target_agent_stack(self, state_manager: StateManager) -> None:
        """Operations with agent_id target the agent's stack, not main."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main_wf",
            goal="Main goal",
            first_step_id="step1",
        )

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent goal",
            first_step_id="agent_step1",
            agent_id=AGENT_ID,
        )

        await state_manager.complete_step(
            session_id=SESSION_ID,
            step_id="agent_step1",
            outputs={"out": "agent_out.md"},
            agent_id=AGENT_ID,
        )

        agent_session = state_manager.resolve_session(SESSION_ID, AGENT_ID)
        assert "agent_step1" in agent_session.step_progress

        main_session = state_manager.resolve_session(SESSION_ID)
        assert "agent_step1" not in main_session.step_progress

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.14.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_agent_state_file_path(self, state_manager: StateManager) -> None:
        """Agent state is stored in a separate file."""
        main_file = state_manager._state_file(SESSION_ID)
        agent_file = state_manager._state_file(SESSION_ID, AGENT_ID)

        assert main_file.name == "state.json"
        assert agent_file.name == f"agent_{AGENT_ID}.json"
        assert main_file.parent == agent_file.parent


class TestGoToStep:
    """Tests for go_to_step in StateManager."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.14.7, JOBS-REQ-003.14.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_step_clears_invalidated_progress(
        self, state_manager: StateManager
    ) -> None:
        """Test that go_to_step clears step_progress for invalidated steps."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test",
            first_step_id="step1",
        )

        await state_manager.complete_step(SESSION_ID, "step1", {"out1": "out1.md"})
        await state_manager.complete_step(SESSION_ID, "step2", {"out2": "out2.md"})

        session = state_manager.resolve_session(SESSION_ID)
        assert "step1" in session.step_progress
        assert "step2" in session.step_progress

        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step1",
            step_index=0,
            invalidate_step_ids=["step1", "step2"],
        )

        session = state_manager.resolve_session(SESSION_ID)
        assert "step1" not in session.step_progress
        assert "step2" not in session.step_progress

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.14.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_step_preserves_earlier_progress(self, state_manager: StateManager) -> None:
        """Test that go_to_step preserves progress for steps before the target."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test",
            first_step_id="step1",
        )

        await state_manager.complete_step(SESSION_ID, "step1", {"out1": "out1.md"})
        await state_manager.complete_step(SESSION_ID, "step2", {"out2": "out2.md"})
        await state_manager.complete_step(SESSION_ID, "step3", {"out3": "out3.md"})

        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step2",
            step_index=1,
            invalidate_step_ids=["step2", "step3"],
        )

        session = state_manager.resolve_session(SESSION_ID)
        assert "step1" in session.step_progress  # preserved
        assert "step2" not in session.step_progress  # cleared
        assert "step3" not in session.step_progress  # cleared

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.17.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_step_updates_position(self, state_manager: StateManager) -> None:
        """Test that go_to_step updates current_step_id and current_step_index."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test",
            first_step_id="step1",
        )

        await state_manager.advance_to_step(SESSION_ID, "step3", 2)

        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step1",
            step_index=0,
            invalidate_step_ids=["step1", "step2", "step3"],
        )

        session = state_manager.resolve_session(SESSION_ID)
        assert session.current_step_id == "step1"
        assert session.current_step_index == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.4.4, JOBS-REQ-003.17.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_step_persists_to_disk(
        self, state_manager: StateManager, project_root: Path
    ) -> None:
        """Test that go_to_step persists changes to the state file."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test",
            first_step_id="step1",
        )

        await state_manager.complete_step(SESSION_ID, "step1", {"out1": "out1.md"})
        await state_manager.advance_to_step(SESSION_ID, "step2", 1)

        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step1",
            step_index=0,
            invalidate_step_ids=["step1", "step2"],
        )

        # Load from disk with a new manager
        new_manager = StateManager(project_root=project_root, platform="test")
        loaded = new_manager.resolve_session(SESSION_ID)

        assert loaded.current_step_id == "step1"
        assert loaded.current_step_index == 0
        assert "step1" not in loaded.step_progress


class TestCrashResilience:
    """Tests for crash resilience and atomic writes."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.17.1, JOBS-REQ-003.4.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_invalid_json_treated_as_empty_stack(self, state_manager: StateManager) -> None:
        """Corrupt state file is treated as empty stack, not an unhandled error."""
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("not valid json {{{", encoding="utf-8")

        # _read_stack should return empty list
        stack = await state_manager._read_stack(SESSION_ID)
        assert stack == []

        # resolve_session should raise StateError (not JSONDecodeError)
        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.resolve_session(SESSION_ID)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_write_uses_atomic_rename(self, state_manager: StateManager) -> None:
        """State writes use atomic rename (no temp files left behind)."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test atomic",
            first_step_id="step1",
        )

        state_file = state_manager._state_file(SESSION_ID)
        session_dir = state_file.parent

        # No .tmp files should be left behind after a successful write
        tmp_files = list(session_dir.glob("*.tmp"))
        assert tmp_files == []

        # State file should contain valid JSON
        import json

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert "workflow_stack" in data
        assert len(data["workflow_stack"]) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.4.6, JOBS-REQ-003.17.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_no_in_memory_caching(
        self, state_manager: StateManager, project_root: Path
    ) -> None:
        """Each operation reads from disk — no stale in-memory state."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test no cache",
            first_step_id="step1",
        )

        # A second manager instance can see state written by the first
        manager2 = StateManager(project_root=project_root, platform="test")
        session = manager2.resolve_session(SESSION_ID)
        assert session.job_name == "test_job"

        # Modify via manager2
        await manager2.start_step(SESSION_ID, "step2")

        # Manager1 sees the change (no stale cache)
        session = state_manager.resolve_session(SESSION_ID)
        assert session.current_step_id == "step2"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-003.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_get_stack_without_agent_returns_main_only(
        self, state_manager: StateManager
    ) -> None:
        """get_stack without agent_id returns only the main stack."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main",
            goal="Main",
            first_step_id="step1",
        )
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent",
            first_step_id="a_step1",
            agent_id=AGENT_ID,
        )

        main_stack = state_manager.get_stack(SESSION_ID)
        assert len(main_stack) == 1
        assert main_stack[0].workflow == "main_job/main"


class TestWorkflowInstanceId:
    """Tests for workflow_instance_id generation."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.7.1, JOBS-REQ-010.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_workflow_instance_id_generated(self, state_manager: StateManager) -> None:
        """Each session gets a unique workflow_instance_id."""
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        assert session.workflow_instance_id
        assert len(session.workflow_instance_id) == 32  # uuid4().hex

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_workflow_instance_ids_unique(self, state_manager: StateManager) -> None:
        """Two sessions get different instance IDs."""
        s1 = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        s2 = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )
        assert s1.workflow_instance_id != s2.workflow_instance_id

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.7.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_workflow_instance_id_persists(
        self, state_manager: StateManager, project_root: Path
    ) -> None:
        """Instance ID is persisted to disk."""
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        loaded = state_manager.resolve_session(SESSION_ID)
        assert loaded.workflow_instance_id == session.workflow_instance_id


class TestStepHistory:
    """Tests for step_history tracking."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.8.1, JOBS-REQ-010.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_start_step_appends_history(self, state_manager: StateManager) -> None:
        """start_step appends to step_history."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        session = state_manager.resolve_session(SESSION_ID)
        assert len(session.step_history) == 1
        assert session.step_history[0].step_id == "step1"
        assert session.step_history[0].started_at is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_step_sets_finished_at(self, state_manager: StateManager) -> None:
        """complete_step updates the last history entry's finished_at."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.complete_step(SESSION_ID, "step1", {"out": "out.md"})

        session = state_manager.resolve_session(SESSION_ID)
        assert session.step_history[0].finished_at is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.8.4, JOBS-REQ-010.8.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_go_to_step_creates_duplicate_history(self, state_manager: StateManager) -> None:
        """go_to_step + start_step creates a second entry for the same step."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.complete_step(SESSION_ID, "step1", {"out": "out.md"})

        # Go back
        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step1",
            step_index=0,
            invalidate_step_ids=["step1"],
        )
        await state_manager.start_step(SESSION_ID, "step1")

        session = state_manager.resolve_session(SESSION_ID)
        assert len(session.step_history) == 2
        assert all(h.step_id == "step1" for h in session.step_history)

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_multi_step_history_ordering(self, state_manager: StateManager) -> None:
        """Steps appear in history in execution order."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.complete_step(SESSION_ID, "step1", {"out": "out.md"})
        await state_manager.start_step(SESSION_ID, "step2")

        session = state_manager.resolve_session(SESSION_ID)
        assert len(session.step_history) == 2
        assert session.step_history[0].step_id == "step1"
        assert session.step_history[1].step_id == "step2"


class TestCompletedWorkflows:
    """Tests for completed_workflows persistence."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.10.1, JOBS-REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_complete_workflow_preserves_in_completed(
        self, state_manager: StateManager
    ) -> None:
        """Completed workflow is moved to completed_workflows list."""
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        instance_id = session.workflow_instance_id

        await state_manager.complete_workflow(SESSION_ID)

        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        assert len(data["workflow_stack"]) == 0
        assert len(data["completed_workflows"]) == 1
        assert data["completed_workflows"][0]["workflow_instance_id"] == instance_id
        assert data["completed_workflows"][0]["status"] == "completed"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.10.1, JOBS-REQ-010.10.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_abort_workflow_preserves_in_completed(self, state_manager: StateManager) -> None:
        """Aborted workflow is moved to completed_workflows list."""
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        instance_id = session.workflow_instance_id

        await state_manager.abort_workflow(SESSION_ID, "Cancelled")

        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        assert len(data["completed_workflows"]) == 1
        assert data["completed_workflows"][0]["workflow_instance_id"] == instance_id
        assert data["completed_workflows"][0]["status"] == "aborted"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.10.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_multiple_completed_workflows(self, state_manager: StateManager) -> None:
        """Multiple completed workflows accumulate."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.complete_workflow(SESSION_ID)

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="stepA",
        )
        await state_manager.abort_workflow(SESSION_ID, "Done")

        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        assert len(data["completed_workflows"]) == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.10.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_write_stack_preserves_completed_workflows(
        self, state_manager: StateManager
    ) -> None:
        """_write_stack preserves existing completed_workflows when not explicitly provided."""
        # Complete a workflow so completed_workflows exists
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.complete_workflow(SESSION_ID)

        # Start a new workflow — _write_stack is called without completed_workflows param
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="step1",
        )

        # Verify completed_workflows was preserved
        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        assert len(data["completed_workflows"]) == 1
        assert len(data["workflow_stack"]) == 1


class TestGetAllSessionData:
    """Tests for get_all_session_data."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.11.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_returns_empty_for_missing_session(self, state_manager: StateManager) -> None:
        result = state_manager.get_all_session_data("nonexistent")
        assert result == {}

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.11.1, JOBS-REQ-010.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_returns_main_stack(self, state_manager: StateManager) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )

        result = state_manager.get_all_session_data(SESSION_ID)
        assert None in result
        active_stack, completed = result[None]
        assert len(active_stack) == 1
        assert len(completed) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.11.1, JOBS-REQ-010.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_returns_agent_stacks(self, state_manager: StateManager) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main",
            goal="Main",
            first_step_id="step1",
        )
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent",
            first_step_id="a_step1",
            agent_id=AGENT_ID,
        )

        result = state_manager.get_all_session_data(SESSION_ID)
        assert None in result
        assert AGENT_ID in result
        active, _ = result[AGENT_ID]
        assert len(active) == 1
        assert active[0].job_name == "agent_job"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_includes_completed_workflows(self, state_manager: StateManager) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )
        await state_manager.complete_workflow(SESSION_ID)

        result = state_manager.get_all_session_data(SESSION_ID)
        active, completed = result[None]
        assert len(active) == 0
        assert len(completed) == 1
        assert completed[0].status == "completed"


class TestSubWorkflowInstanceIds:
    """Tests for sub_workflow_instance_ids tracking on parent steps."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()
        return tmp_path

    @pytest.fixture
    def state_manager(self, project_root: Path) -> StateManager:
        return StateManager(project_root=project_root, platform="test")

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.9.1, JOBS-REQ-010.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_nested_workflow_records_instance_on_parent_step_progress(
        self, state_manager: StateManager
    ) -> None:
        """Starting a nested workflow records the child's instance ID on parent's step_progress."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="parent_job",
            workflow_name="parent_wf",
            goal="Parent",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        child = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="child_job",
            workflow_name="child_wf",
            goal="Child",
            first_step_id="child_step1",
        )

        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        parent_data = data["workflow_stack"][0]
        assert (
            child.workflow_instance_id
            in parent_data["step_progress"]["step1"]["sub_workflow_instance_ids"]
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.9.2, JOBS-REQ-010.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_nested_workflow_records_instance_on_parent_step_history(
        self, state_manager: StateManager
    ) -> None:
        """Starting a nested workflow records the child's instance ID on parent's step_history."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="parent_job",
            workflow_name="parent_wf",
            goal="Parent",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        child = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="child_job",
            workflow_name="child_wf",
            goal="Child",
            first_step_id="child_step1",
        )

        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        parent_data = data["workflow_stack"][0]
        assert (
            child.workflow_instance_id
            in parent_data["step_history"][-1]["sub_workflow_instance_ids"]
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.9.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_cross_agent_sub_workflow_records_on_main_stack(
        self, state_manager: StateManager
    ) -> None:
        """Cross-agent sub-workflow records instance ID on main stack parent's step."""
        # Create parent on main stack
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="parent_job",
            workflow_name="parent_wf",
            goal="Parent",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        # Create child on agent stack — this should also update main stack parent
        child = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="child_job",
            workflow_name="child_wf",
            goal="Child",
            first_step_id="child_step1",
            agent_id=AGENT_ID,
        )

        # Verify main stack parent has the child's instance ID
        main_state_file = state_manager._state_file(SESSION_ID, agent_id=None)
        main_data = json.loads(main_state_file.read_text())
        parent_data = main_data["workflow_stack"][0]
        assert (
            child.workflow_instance_id
            in parent_data["step_progress"]["step1"]["sub_workflow_instance_ids"]
        )
        assert (
            child.workflow_instance_id
            in parent_data["step_history"][-1]["sub_workflow_instance_ids"]
        )
