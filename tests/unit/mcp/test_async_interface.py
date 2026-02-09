"""Tests to ensure the MCP interface remains async.

These tests serve as a regression guard to ensure that key async methods
don't accidentally get converted back to sync methods, which would break
concurrency guarantees.
"""

import asyncio
import inspect
from pathlib import Path

from deepwork.mcp.claude_cli import ClaudeCLI
from deepwork.mcp.quality_gate import MockQualityGate, QualityGate
from deepwork.mcp.state import StateManager
from deepwork.mcp.tools import WorkflowTools


class TestAsyncInterfaceRegression:
    """Tests that verify async interface contract is maintained."""

    def test_state_manager_async_methods(self) -> None:
        """Verify StateManager methods that must be async remain async."""
        async_methods = [
            "create_session",
            "load_session",
            "start_step",
            "complete_step",
            "record_quality_attempt",
            "advance_to_step",
            "complete_workflow",
            "abort_workflow",
            "list_sessions",
            "find_active_sessions_for_workflow",
            "delete_session",
        ]

        for method_name in async_methods:
            method = getattr(StateManager, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"StateManager.{method_name} must be async (coroutine function). "
                f"This is required for concurrent access safety."
            )

    def test_state_manager_has_lock(self, tmp_path: Path) -> None:
        """Verify StateManager has an asyncio.Lock for thread safety."""
        manager = StateManager(tmp_path)

        assert hasattr(manager, "_lock"), "StateManager must have _lock attribute"
        assert isinstance(manager._lock, asyncio.Lock), (
            "StateManager._lock must be an asyncio.Lock for async concurrency safety"
        )

    def test_state_manager_has_session_stack(self, tmp_path: Path) -> None:
        """Verify StateManager uses a session stack for nested workflows."""
        manager = StateManager(tmp_path)

        assert hasattr(manager, "_session_stack"), "StateManager must have _session_stack attribute"
        assert isinstance(manager._session_stack, list), (
            "StateManager._session_stack must be a list for nested workflow support"
        )

    def test_workflow_tools_async_methods(self) -> None:
        """Verify WorkflowTools methods that must be async remain async."""
        async_methods = [
            "start_workflow",
            "finished_step",
            "abort_workflow",
        ]

        for method_name in async_methods:
            method = getattr(WorkflowTools, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"WorkflowTools.{method_name} must be async (coroutine function). "
                f"This is required for non-blocking MCP tool execution."
            )

    def test_claude_cli_async_methods(self) -> None:
        """Verify ClaudeCLI methods that must be async remain async."""
        method = getattr(ClaudeCLI, "run")
        assert inspect.iscoroutinefunction(method), (
            "ClaudeCLI.run must be async (coroutine function). "
            "This is required for non-blocking subprocess execution."
        )

    def test_quality_gate_async_methods(self) -> None:
        """Verify QualityGate methods that must be async remain async."""
        async_methods = [
            "evaluate",
            "_build_payload",
        ]

        for method_name in async_methods:
            method = getattr(QualityGate, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"QualityGate.{method_name} must be async (coroutine function). "
                f"This is required for non-blocking subprocess execution."
            )

    def test_mock_quality_gate_async_methods(self) -> None:
        """Verify MockQualityGate maintains async interface."""
        method = MockQualityGate.evaluate
        assert inspect.iscoroutinefunction(method), (
            "MockQualityGate.evaluate must be async to match QualityGate interface"
        )

    async def test_concurrent_state_operations_are_serialized(self, tmp_path: Path) -> None:
        """Test that concurrent state operations don't corrupt state.

        This test verifies that the async lock properly serializes access
        to shared state, preventing race conditions.
        """
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()

        manager = StateManager(tmp_path)

        # Create initial session
        await manager.create_session(
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )

        # Run multiple concurrent quality attempt recordings
        async def record_attempt() -> int:
            return await manager.record_quality_attempt("step1")

        # Execute 10 concurrent recordings
        results = await asyncio.gather(*[record_attempt() for _ in range(10)])

        # Each should get a unique, sequential number (1-10)
        assert sorted(results) == list(range(1, 11)), (
            "Concurrent quality_attempt recordings should be serialized. "
            f"Expected [1..10] but got {sorted(results)}"
        )

        # Verify final count is correct
        final_session = manager.get_active_session()
        assert final_session is not None
        assert final_session.step_progress["step1"].quality_attempts == 10

    async def test_concurrent_workflows_with_session_id_routing(
        self, tmp_path: Path
    ) -> None:
        """Test that two concurrent sessions can be routed correctly via session_id.

        Two sessions are created on the stack. Concurrent finished_step-like
        operations (complete_step) target different sessions via session_id
        and don't interfere with each other.
        """
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "tmp").mkdir()

        manager = StateManager(tmp_path)

        # Create two sessions on the stack
        session1 = await manager.create_session(
            job_name="job1",
            workflow_name="wf1",
            goal="Goal 1",
            first_step_id="step_a",
        )
        session2 = await manager.create_session(
            job_name="job2",
            workflow_name="wf2",
            goal="Goal 2",
            first_step_id="step_x",
        )

        # Concurrent complete_step calls targeting different sessions
        async def complete_session1() -> None:
            await manager.complete_step(
                step_id="step_a",
                outputs={"out1": "file1.md"},
                session_id=session1.session_id,
            )

        async def complete_session2() -> None:
            await manager.complete_step(
                step_id="step_x",
                outputs={"out2": "file2.md"},
                session_id=session2.session_id,
            )

        # Run concurrently
        await asyncio.gather(complete_session1(), complete_session2())

        # Verify each session got the right updates
        assert "step_a" in session1.step_progress
        assert session1.step_progress["step_a"].outputs == {"out1": "file1.md"}

        assert "step_x" in session2.step_progress
        assert session2.step_progress["step_x"].outputs == {"out2": "file2.md"}

        # Cross-check: session1 should NOT have step_x, session2 should NOT have step_a
        assert "step_x" not in session1.step_progress
        assert "step_a" not in session2.step_progress
