"""Tests to ensure the MCP interface remains async.

These tests serve as a regression guard to ensure that key async methods
don't accidentally get converted back to sync methods, which would break
concurrency guarantees.
"""

import asyncio
import inspect
from pathlib import Path

from deepwork.jobs.mcp.state import StateManager
from deepwork.jobs.mcp.tools import WorkflowTools

SESSION_ID = "async-test-session"


class TestAsyncInterfaceRegression:
    """Tests that verify async interface contract is maintained."""

    def test_state_manager_async_methods(self) -> None:
        """Verify StateManager methods that must be async remain async."""
        async_methods = [
            "create_session",
            "start_step",
            "complete_step",
            "record_quality_attempt",
            "advance_to_step",
            "complete_workflow",
            "abort_workflow",
            "go_to_step",
        ]

        for method_name in async_methods:
            method = getattr(StateManager, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"StateManager.{method_name} must be async (coroutine function). "
                f"This is required for concurrent access safety."
            )

    def test_state_manager_has_lock(self, tmp_path: Path) -> None:
        """Verify StateManager has an asyncio.Lock for thread safety."""
        manager = StateManager(project_root=tmp_path, platform="test")

        assert hasattr(manager, "_lock"), "StateManager must have _lock attribute"
        assert isinstance(manager._lock, asyncio.Lock), (
            "StateManager._lock must be an asyncio.Lock for async concurrency safety"
        )

    def test_workflow_tools_async_methods(self) -> None:
        """Verify WorkflowTools methods that must be async remain async."""
        async_methods = [
            "start_workflow",
            "finished_step",
            "abort_workflow",
            "go_to_step",
        ]

        for method_name in async_methods:
            method = getattr(WorkflowTools, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"WorkflowTools.{method_name} must be async (coroutine function). "
                f"This is required for non-blocking MCP tool execution."
            )

    async def test_concurrent_state_operations_are_serialized(self, tmp_path: Path) -> None:
        """Test that concurrent state operations don't corrupt state."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()

        manager = StateManager(project_root=tmp_path, platform="test")

        await manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )

        async def record_attempt() -> int:
            return await manager.record_quality_attempt(SESSION_ID, "step1")

        results = await asyncio.gather(*[record_attempt() for _ in range(10)])

        assert sorted(results) == list(range(1, 11)), (
            "Concurrent quality_attempt recordings should be serialized. "
            f"Expected [1..10] but got {sorted(results)}"
        )

        final_session = manager.resolve_session(SESSION_ID)
        assert final_session.step_progress["step1"].quality_attempts == 10

    async def test_concurrent_workflows_with_agent_isolation(self, tmp_path: Path) -> None:
        """Test that two concurrent agents can operate independently."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()

        manager = StateManager(project_root=tmp_path, platform="test")

        await manager.create_session(
            session_id=SESSION_ID,
            job_name="main_job",
            workflow_name="main_wf",
            goal="Main goal",
            first_step_id="step1",
        )

        await manager.create_session(
            session_id=SESSION_ID,
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step_a",
            agent_id="agent-1",
        )
        await manager.create_session(
            session_id=SESSION_ID,
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="step_x",
            agent_id="agent-2",
        )

        async def complete_agent1() -> None:
            await manager.complete_step(
                session_id=SESSION_ID,
                step_id="step_a",
                outputs={"out1": "file1.md"},
                agent_id="agent-1",
            )

        async def complete_agent2() -> None:
            await manager.complete_step(
                session_id=SESSION_ID,
                step_id="step_x",
                outputs={"out2": "file2.md"},
                agent_id="agent-2",
            )

        await asyncio.gather(complete_agent1(), complete_agent2())

        agent1_session = manager.resolve_session(SESSION_ID, "agent-1")
        assert "step_a" in agent1_session.step_progress
        assert agent1_session.step_progress["step_a"].outputs == {"out1": "file1.md"}

        agent2_session = manager.resolve_session(SESSION_ID, "agent-2")
        assert "step_x" in agent2_session.step_progress
        assert agent2_session.step_progress["step_x"].outputs == {"out2": "file2.md"}

        assert "step_x" not in agent1_session.step_progress
        assert "step_a" not in agent2_session.step_progress
