"""Additional tests for MCP state management to cover edge cases and error paths."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from deepwork.jobs.mcp.state import StateError, StateManager

SESSION_ID = "test-session-cov"
AGENT_ID = "agent-cov"


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()
    return tmp_path


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    return StateManager(project_root=project_root, platform="test")


class TestReadCompletedWorkflowsEdgeCases:
    """Tests for _read_completed_workflows error paths (lines 110, 117-118)."""

    async def test_returns_empty_when_file_missing(self, state_manager: StateManager) -> None:
        """_read_completed_workflows returns [] when state file does not exist."""
        result = await state_manager._read_completed_workflows(SESSION_ID)
        assert result == []

    async def test_returns_empty_on_corrupt_json(self, state_manager: StateManager) -> None:
        """_read_completed_workflows returns [] when state file has invalid JSON."""
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("{invalid json!!!", encoding="utf-8")

        result = await state_manager._read_completed_workflows(SESSION_ID)
        assert result == []


class TestWriteStackEdgeCases:
    """Tests for _write_stack error handling (lines 153-154, 164-170)."""

    async def test_preserves_completed_even_if_corrupt(
        self, state_manager: StateManager
    ) -> None:
        """_write_stack handles corrupt existing file when preserving completed_workflows."""
        # Create a corrupt state file
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("not valid json", encoding="utf-8")

        # Writing with completed_workflows=None should not crash on corrupt existing file
        await state_manager._write_stack(SESSION_ID, [])

        # File should now contain valid JSON with empty stack
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["workflow_stack"] == []
        assert "completed_workflows" not in data

    async def test_write_failure_cleans_up_temp_file(
        self, state_manager: StateManager
    ) -> None:
        """_write_stack cleans up temp file if write fails (lines 164-170)."""
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Patch os.replace to simulate failure after temp file is written
        with patch("deepwork.jobs.mcp.state.os.replace", side_effect=OSError("rename failed")):
            with pytest.raises(OSError, match="rename failed"):
                await state_manager._write_stack(SESSION_ID, [])

        # No temp files should be left behind (cleanup should have removed it)
        session_dir = state_file.parent
        if session_dir.exists():
            tmp_files = list(session_dir.glob("*.tmp"))
            assert tmp_files == []


class TestEmptyStackErrors:
    """Tests for StateError when stack is empty (lines 264, 300, 335, 360, 395, 433, 472)."""

    async def test_start_step_empty_stack(self, state_manager: StateManager) -> None:
        """start_step raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.start_step(SESSION_ID, "step1")

    async def test_complete_step_empty_stack(self, state_manager: StateManager) -> None:
        """complete_step raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.complete_step(SESSION_ID, "step1", {"out": "x.md"})

    async def test_record_quality_attempt_empty_stack(
        self, state_manager: StateManager
    ) -> None:
        """record_quality_attempt raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.record_quality_attempt(SESSION_ID, "step1")

    async def test_advance_to_step_empty_stack(self, state_manager: StateManager) -> None:
        """advance_to_step raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.advance_to_step(SESSION_ID, "step2", 1)

    async def test_go_to_step_empty_stack(self, state_manager: StateManager) -> None:
        """go_to_step raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.go_to_step(SESSION_ID, "step1", 0, ["step1"])

    async def test_complete_workflow_empty_stack(self, state_manager: StateManager) -> None:
        """complete_workflow raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.complete_workflow(SESSION_ID)

    async def test_abort_workflow_empty_stack(self, state_manager: StateManager) -> None:
        """abort_workflow raises StateError when no active session."""
        with pytest.raises(StateError, match="No active workflow session"):
            await state_manager.abort_workflow(SESSION_ID, "cancelled")


class TestStartStepExistingProgress:
    """Tests for start_step when step already has progress (lines 278-280)."""

    async def test_updates_existing_step_progress(self, state_manager: StateManager) -> None:
        """start_step updates started_at and input_values on existing progress entry."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )

        # Start step1 initially
        await state_manager.start_step(SESSION_ID, "step1", input_values={"a": "old"})
        session = state_manager.resolve_session(SESSION_ID)
        first_started_at = session.step_progress["step1"].started_at

        # Start step1 again with new input values
        await state_manager.start_step(SESSION_ID, "step1", input_values={"a": "new"})
        session = state_manager.resolve_session(SESSION_ID)

        assert session.step_progress["step1"].input_values == {"a": "new"}
        # started_at should be updated (different timestamp)
        assert session.step_progress["step1"].started_at is not None

    async def test_updates_existing_without_input_values(
        self, state_manager: StateManager
    ) -> None:
        """start_step on existing progress without new input_values keeps old ones."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal",
            first_step_id="step1",
        )

        await state_manager.start_step(SESSION_ID, "step1", input_values={"a": "old"})

        # Start again without input_values
        await state_manager.start_step(SESSION_ID, "step1")
        session = state_manager.resolve_session(SESSION_ID)

        # Old input_values should be preserved
        assert session.step_progress["step1"].input_values == {"a": "old"}


class TestResolveSessionCorruptJSON:
    """Tests for resolve_session with corrupt JSON (line 249 - empty stack)."""

    def test_resolve_session_empty_stack_in_valid_json(
        self, state_manager: StateManager
    ) -> None:
        """resolve_session raises StateError when JSON is valid but stack is empty."""
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({"workflow_stack": []}), encoding="utf-8")

        with pytest.raises(StateError, match="No active workflow session"):
            state_manager.resolve_session(SESSION_ID)


class TestGetStackCorruptJSON:
    """Tests for get_stack with corrupt JSON files (lines 521-522, 534-535)."""

    def test_corrupt_main_json(self, state_manager: StateManager) -> None:
        """get_stack returns empty when main state file has corrupt JSON."""
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("corrupt json {{{", encoding="utf-8")

        stack = state_manager.get_stack(SESSION_ID)
        assert stack == []

    def test_corrupt_agent_json(self, state_manager: StateManager) -> None:
        """get_stack handles corrupt agent state file gracefully."""
        # Create a valid main state file
        state_file = state_manager._state_file(SESSION_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({"workflow_stack": []}), encoding="utf-8")

        # Create corrupt agent state file
        agent_file = state_manager._state_file(SESSION_ID, AGENT_ID)
        agent_file.write_text("corrupt agent json", encoding="utf-8")

        # Should return empty (main has no stack, agent is corrupt)
        stack = state_manager.get_stack(SESSION_ID, AGENT_ID)
        assert stack == []


class TestGetAllSessionDataEdgeCases:
    """Tests for get_all_session_data edge cases (lines 572, 576-577, 589)."""

    def test_skips_non_json_files(self, state_manager: StateManager) -> None:
        """get_all_session_data ignores non-.json files in the session directory."""
        session_dir = state_manager.sessions_dir / f"session-{SESSION_ID}"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create a valid state file
        (session_dir / "state.json").write_text(
            json.dumps({"workflow_stack": [], "completed_workflows": []}),
            encoding="utf-8",
        )
        # Create a non-JSON file that should be skipped
        (session_dir / "notes.txt").write_text("not a json file")

        result = state_manager.get_all_session_data(SESSION_ID)
        assert None in result
        assert len(result) == 1  # Only state.json

    def test_skips_corrupt_json_files(self, state_manager: StateManager) -> None:
        """get_all_session_data skips files with invalid JSON."""
        session_dir = state_manager.sessions_dir / f"session-{SESSION_ID}"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create a corrupt state file
        (session_dir / "state.json").write_text("corrupt json {{", encoding="utf-8")

        result = state_manager.get_all_session_data(SESSION_ID)
        # Corrupt file is skipped entirely
        assert result == {}

    def test_skips_unknown_filename_patterns(self, state_manager: StateManager) -> None:
        """get_all_session_data skips JSON files that don't match state.json or agent_*.json."""
        session_dir = state_manager.sessions_dir / f"session-{SESSION_ID}"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create a JSON file with unknown naming pattern
        (session_dir / "unknown_pattern.json").write_text(
            json.dumps({"workflow_stack": [], "completed_workflows": []}),
            encoding="utf-8",
        )

        result = state_manager.get_all_session_data(SESSION_ID)
        assert result == {}

    def test_parses_agent_files(self, state_manager: StateManager) -> None:
        """get_all_session_data correctly identifies agent files by naming convention."""
        session_dir = state_manager.sessions_dir / f"session-{SESSION_ID}"
        session_dir.mkdir(parents=True, exist_ok=True)

        (session_dir / "agent_my-agent.json").write_text(
            json.dumps({"workflow_stack": [], "completed_workflows": []}),
            encoding="utf-8",
        )

        result = state_manager.get_all_session_data(SESSION_ID)
        assert "my-agent" in result
        active, completed = result["my-agent"]
        assert active == []
        assert completed == []


class TestCreateSessionCrossAgent:
    """Tests for create_session cross-agent sub-workflow tracking (line 216->229)."""

    async def test_cross_agent_without_main_stack(
        self, state_manager: StateManager
    ) -> None:
        """Creating an agent session when main stack is empty does not crash."""
        # No main stack - just create an agent session directly
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="agent_job",
            workflow_name="agent_wf",
            goal="Agent goal",
            first_step_id="a_step1",
            agent_id=AGENT_ID,
        )

        # Should succeed without error
        assert session.job_name == "agent_job"
        agent_stack = state_manager.get_stack(SESSION_ID, AGENT_ID)
        assert len(agent_stack) == 1
