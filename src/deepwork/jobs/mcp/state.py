"""Workflow state management for MCP server.

State is persisted to `.deepwork/tmp/sessions/<platform>/session-<id>/state.json`
under the project root for durability across server restarts (e.g. `claude -r`).

Supports nested workflows via a session stack — when a step starts a new
workflow, it's pushed onto the stack. When a workflow completes or is
aborted, it's popped from the stack.

Sub-agents get their own isolated workflow stacks stored in
`agent_<agent_id>.json` alongside the main `state.json`. A sub-agent's
`get_stack` returns the main stack plus its own, giving it visibility into
the parent context without polluting it.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import aiofiles

from deepwork.jobs.mcp.schemas import StackEntry, StepProgress, WorkflowSession


class StateError(Exception):
    """Exception raised for state management errors."""

    pass


class StateManager:
    """Manages workflow session state with stack-based nesting support.

    State is persisted to .deepwork/tmp/sessions/<platform>/session-<id>/ as
    JSON files:
    - state.json: main workflow stack (top-level agent)
    - agent_<agent_id>.json: per-agent workflow stack (sub-agents)

    No in-memory caching — every operation reads from and writes to disk.
    This ensures state survives MCP server restarts.

    This implementation is async-safe and uses a lock to prevent
    concurrent access issues.
    """

    def __init__(self, project_root: Path, platform: str):
        """Initialize state manager.

        Args:
            project_root: Path to the project root directory
            platform: Platform identifier (e.g., 'claude', 'gemini')
        """
        self.project_root = project_root
        self.platform = platform
        self.sessions_dir = project_root / ".deepwork" / "tmp" / "sessions" / platform
        self._lock = asyncio.Lock()

    def _state_file(self, session_id: str, agent_id: str | None = None) -> Path:
        """Get the path to a state file.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Path to the state file
        """
        session_dir = self.sessions_dir / f"session-{session_id}"
        if agent_id:
            return session_dir / f"agent_{agent_id}.json"
        return session_dir / "state.json"

    async def _read_stack(
        self, session_id: str, agent_id: str | None = None
    ) -> list[WorkflowSession]:
        """Read the workflow stack from disk.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            List of WorkflowSession objects (the stack), or empty list if no state file
        """
        state_file = self._state_file(session_id, agent_id)
        if not state_file.exists():
            return []

        async with aiofiles.open(state_file, encoding="utf-8") as f:
            content = await f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        stack_data = data.get("workflow_stack", [])
        return [WorkflowSession.from_dict(entry) for entry in stack_data]

    async def _write_stack(
        self,
        session_id: str,
        stack: list[WorkflowSession],
        agent_id: str | None = None,
    ) -> None:
        """Write the workflow stack to disk.

        Args:
            session_id: Claude Code session ID
            stack: List of WorkflowSession objects to persist
            agent_id: Optional agent ID for sub-agent scoped state
        """
        state_file = self._state_file(session_id, agent_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {"workflow_stack": [s.to_dict() for s in stack]}
        content = json.dumps(data, indent=2)

        async with aiofiles.open(state_file, "w", encoding="utf-8") as f:
            await f.write(content)

    async def create_session(
        self,
        session_id: str,
        job_name: str,
        workflow_name: str,
        goal: str,
        first_step_id: str,
        instance_id: str | None = None,
        agent_id: str | None = None,
    ) -> WorkflowSession:
        """Create a new workflow session and push onto the stack.

        Args:
            session_id: Claude Code session ID (storage key)
            job_name: Name of the job
            workflow_name: Name of the workflow
            goal: User's goal for this workflow
            first_step_id: ID of the first step
            instance_id: Optional instance identifier
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            New WorkflowSession
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            now = datetime.now(UTC).isoformat()

            session = WorkflowSession(
                session_id=session_id,
                job_name=job_name,
                workflow_name=workflow_name,
                instance_id=instance_id,
                goal=goal,
                current_step_id=first_step_id,
                current_entry_index=0,
                step_progress={},
                started_at=now,
                status="active",
            )

            stack.append(session)
            await self._write_stack(session_id, stack, agent_id)
            return session

    def resolve_session(self, session_id: str, agent_id: str | None = None) -> WorkflowSession:
        """Resolve the active session (top of stack) synchronously.

        This is a synchronous convenience wrapper that reads state from disk
        using synchronous I/O. For async contexts, prefer using _read_stack
        directly within an async with self._lock block.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Top-of-stack WorkflowSession

        Raises:
            StateError: If no active workflow session
        """
        state_file = self._state_file(session_id, agent_id)
        if not state_file.exists():
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")

        content = state_file.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")

        stack_data = data.get("workflow_stack", [])
        if not stack_data:
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")

        return WorkflowSession.from_dict(stack_data[-1])

    async def start_step(
        self, session_id: str, step_id: str, agent_id: str | None = None
    ) -> None:
        """Mark a step as started.

        Args:
            session_id: Claude Code session ID
            step_id: Step ID to start
            agent_id: Optional agent ID for sub-agent scoped state

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            now = datetime.now(UTC).isoformat()

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(
                    step_id=step_id,
                    started_at=now,
                )
            else:
                session.step_progress[step_id].started_at = now

            session.current_step_id = step_id
            await self._write_stack(session_id, stack, agent_id)

    async def complete_step(
        self,
        session_id: str,
        step_id: str,
        outputs: dict[str, str | list[str]],
        notes: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Mark a step as completed.

        Args:
            session_id: Claude Code session ID
            step_id: Step ID to complete
            outputs: Map of output names to file path(s)
            notes: Optional notes
            agent_id: Optional agent ID for sub-agent scoped state

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            now = datetime.now(UTC).isoformat()

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(
                    step_id=step_id,
                    started_at=now,
                )

            progress = session.step_progress[step_id]
            progress.completed_at = now
            progress.outputs = outputs
            progress.notes = notes

            await self._write_stack(session_id, stack, agent_id)

    async def record_quality_attempt(
        self, session_id: str, step_id: str, agent_id: str | None = None
    ) -> int:
        """Record a quality gate attempt for a step.

        Args:
            session_id: Claude Code session ID
            step_id: Step ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Total number of attempts for this step

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(step_id=step_id)

            session.step_progress[step_id].quality_attempts += 1
            await self._write_stack(session_id, stack, agent_id)

            return session.step_progress[step_id].quality_attempts

    async def advance_to_step(
        self,
        session_id: str,
        step_id: str,
        entry_index: int,
        agent_id: str | None = None,
    ) -> None:
        """Advance the session to a new step.

        Args:
            session_id: Claude Code session ID
            step_id: New current step ID
            entry_index: Index in workflow step_entries
            agent_id: Optional agent ID for sub-agent scoped state

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            session.current_step_id = step_id
            session.current_entry_index = entry_index
            await self._write_stack(session_id, stack, agent_id)

    async def go_to_step(
        self,
        session_id: str,
        step_id: str,
        entry_index: int,
        invalidate_step_ids: list[str],
        agent_id: str | None = None,
    ) -> None:
        """Navigate back to a prior step, clearing progress from that step onward.

        Args:
            session_id: Claude Code session ID
            step_id: Step ID to navigate to
            entry_index: Index of the target entry in workflow step_entries
            invalidate_step_ids: Step IDs whose progress should be cleared
            agent_id: Optional agent ID for sub-agent scoped state

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]

            # Clear progress for all invalidated steps
            for sid in invalidate_step_ids:
                if sid in session.step_progress:
                    del session.step_progress[sid]

            # Update position
            session.current_step_id = step_id
            session.current_entry_index = entry_index

            await self._write_stack(session_id, stack, agent_id)

    async def complete_workflow(
        self, session_id: str, agent_id: str | None = None
    ) -> WorkflowSession | None:
        """Mark the workflow as complete and remove from stack.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            The new active session after removal, or None if stack is empty

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            now = datetime.now(UTC).isoformat()
            session.completed_at = now
            session.status = "completed"

            # Pop the completed session from the stack
            stack.pop()
            await self._write_stack(session_id, stack, agent_id)

            return stack[-1] if stack else None

    async def abort_workflow(
        self, session_id: str, explanation: str, agent_id: str | None = None
    ) -> tuple[WorkflowSession, WorkflowSession | None]:
        """Abort a workflow and remove from stack.

        Args:
            session_id: Claude Code session ID
            explanation: Reason for aborting the workflow
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Tuple of (aborted session, new active session or None)

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            now = datetime.now(UTC).isoformat()
            session.completed_at = now
            session.status = "aborted"
            session.abort_reason = explanation

            # Pop the aborted session from the stack
            stack.pop()
            await self._write_stack(session_id, stack, agent_id)

            new_active = stack[-1] if stack else None
            return session, new_active

    def get_all_outputs(
        self, session_id: str, agent_id: str | None = None
    ) -> dict[str, str | list[str]]:
        """Get all outputs from all completed steps of the top-of-stack session.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Merged dict of all output names to file path(s)

        Raises:
            StateError: If no active session
        """
        session = self.resolve_session(session_id, agent_id)
        all_outputs: dict[str, str | list[str]] = {}
        for progress in session.step_progress.values():
            all_outputs.update(progress.outputs)
        return all_outputs

    def get_stack(
        self, session_id: str, agent_id: str | None = None
    ) -> list[StackEntry]:
        """Get the current workflow stack as StackEntry objects.

        When agent_id is provided, returns the main stack concatenated with
        the agent's stack, giving the sub-agent visibility into parent context.
        When agent_id is None, returns only the main stack.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            List of StackEntry with workflow and step info, bottom to top
        """
        main_file = self._state_file(session_id, agent_id=None)
        main_stack: list[WorkflowSession] = []
        if main_file.exists():
            content = main_file.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
                main_stack = [
                    WorkflowSession.from_dict(entry)
                    for entry in data.get("workflow_stack", [])
                ]
            except json.JSONDecodeError:
                pass

        agent_stack: list[WorkflowSession] = []
        if agent_id:
            agent_file = self._state_file(session_id, agent_id)
            if agent_file.exists():
                content = agent_file.read_text(encoding="utf-8")
                try:
                    data = json.loads(content)
                    agent_stack = [
                        WorkflowSession.from_dict(entry)
                        for entry in data.get("workflow_stack", [])
                    ]
                except json.JSONDecodeError:
                    pass

        combined = main_stack + agent_stack
        return [
            StackEntry(
                workflow=f"{s.job_name}/{s.workflow_name}",
                step=s.current_step_id,
            )
            for s in combined
        ]

    def get_stack_depth(
        self, session_id: str, agent_id: str | None = None
    ) -> int:
        """Get the current stack depth.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            Number of active workflow sessions on the stack
        """
        return len(self.get_stack(session_id, agent_id))
