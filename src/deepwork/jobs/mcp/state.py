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
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles

from deepwork.jobs.mcp.schemas import (
    ArgumentValue,
    StackEntry,
    StepHistoryEntry,
    StepProgress,
    WorkflowSession,
)


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
        """Get the path to a state file."""
        session_dir = self.sessions_dir / f"session-{session_id}"
        if agent_id:
            return session_dir / f"agent_{agent_id}.json"
        return session_dir / "state.json"

    async def _read_stack(
        self, session_id: str, agent_id: str | None = None
    ) -> list[WorkflowSession]:
        """Read the workflow stack from disk."""
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

    async def _read_completed_workflows(
        self, session_id: str, agent_id: str | None = None
    ) -> list[WorkflowSession]:
        """Read completed/aborted workflows from disk.

        Args:
            session_id: Claude Code session ID
            agent_id: Optional agent ID for sub-agent scoped state

        Returns:
            List of completed/aborted WorkflowSession objects
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

        completed_data = data.get("completed_workflows", [])
        return [WorkflowSession.from_dict(entry) for entry in completed_data]

    async def _write_stack(
        self,
        session_id: str,
        stack: list[WorkflowSession],
        agent_id: str | None = None,
        completed_workflows: list[WorkflowSession] | None = None,
    ) -> None:
        """Write the workflow stack to disk.

        Args:
            session_id: Claude Code session ID
            stack: List of WorkflowSession objects to persist
            agent_id: Optional agent ID for sub-agent scoped state
            completed_workflows: Optional list of completed/aborted workflows to persist.
                If None, preserves existing completed_workflows from the file.
        """
        state_file = self._state_file(session_id, agent_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {"workflow_stack": [s.to_dict() for s in stack]}

        if completed_workflows is not None:
            data["completed_workflows"] = [s.to_dict() for s in completed_workflows]
        else:
            # Preserve existing completed_workflows if present
            if state_file.exists():
                try:
                    existing = json.loads(state_file.read_text(encoding="utf-8"))
                    if "completed_workflows" in existing:
                        data["completed_workflows"] = existing["completed_workflows"]
                except (json.JSONDecodeError, OSError):
                    pass

        content = json.dumps(data, indent=2)

        # Write to a temp file then atomically rename to avoid partial reads
        fd, tmp_path = tempfile.mkstemp(dir=str(state_file.parent), suffix=".tmp")
        try:
            async with aiofiles.open(fd, "w", encoding="utf-8", closefd=True) as f:
                await f.write(content)
            os.replace(tmp_path, state_file)
        except BaseException:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    async def create_session(
        self,
        session_id: str,
        job_name: str,
        workflow_name: str,
        goal: str,
        first_step_id: str,
        agent_id: str | None = None,
    ) -> WorkflowSession:
        """Create a new workflow session and push onto the stack."""
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            now = datetime.now(UTC).isoformat()

            session = WorkflowSession(
                session_id=session_id,
                job_name=job_name,
                workflow_name=workflow_name,
                goal=goal,
                current_step_id=first_step_id,
                current_step_index=0,
                step_progress={},
                started_at=now,
                status="active",
            )

            # If there's a parent workflow on the stack, record this sub-workflow's
            # instance ID on the parent's current step
            if stack:
                parent = stack[-1]
                parent_step_id = parent.current_step_id
                # Update step_progress
                if parent_step_id in parent.step_progress:
                    parent.step_progress[parent_step_id].sub_workflow_instance_ids.append(
                        session.workflow_instance_id
                    )
                # Update last step_history entry if it matches
                if parent.step_history and parent.step_history[-1].step_id == parent_step_id:
                    parent.step_history[-1].sub_workflow_instance_ids.append(
                        session.workflow_instance_id
                    )
            elif agent_id:
                # Cross-agent sub-workflow: also update main stack's parent
                main_stack = await self._read_stack(session_id, agent_id=None)
                if main_stack:
                    parent = main_stack[-1]
                    parent_step_id = parent.current_step_id
                    if parent_step_id in parent.step_progress:
                        parent.step_progress[parent_step_id].sub_workflow_instance_ids.append(
                            session.workflow_instance_id
                        )
                    if parent.step_history and parent.step_history[-1].step_id == parent_step_id:
                        parent.step_history[-1].sub_workflow_instance_ids.append(
                            session.workflow_instance_id
                        )
                    await self._write_stack(session_id, main_stack, agent_id=None)

            stack.append(session)
            await self._write_stack(session_id, stack, agent_id)
            return session

    def resolve_session(self, session_id: str, agent_id: str | None = None) -> WorkflowSession:
        """Resolve the active session (top of stack) synchronously."""
        state_file = self._state_file(session_id, agent_id)
        if not state_file.exists():
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")

        content = state_file.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise StateError(
                "No active workflow session. Use start_workflow to begin a workflow."
            ) from exc

        stack_data = data.get("workflow_stack", [])
        if not stack_data:
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")

        return WorkflowSession.from_dict(stack_data[-1])

    async def start_step(
        self,
        session_id: str,
        step_id: str,
        input_values: dict[str, ArgumentValue] | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Mark a step as started, optionally storing input values."""
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
                    input_values=input_values or {},
                )
            else:
                session.step_progress[step_id].started_at = now
                if input_values:
                    session.step_progress[step_id].input_values = input_values

            # Append to step history
            session.step_history.append(StepHistoryEntry(step_id=step_id, started_at=now))

            session.current_step_id = step_id
            await self._write_stack(session_id, stack, agent_id)

    async def complete_step(
        self,
        session_id: str,
        step_id: str,
        outputs: dict[str, ArgumentValue],
        work_summary: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Mark a step as completed."""
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
            progress.work_summary = work_summary

            # Update the last step_history entry's finished_at
            if session.step_history and session.step_history[-1].step_id == step_id:
                session.step_history[-1].finished_at = now

            await self._write_stack(session_id, stack, agent_id)

    async def record_quality_attempt(
        self, session_id: str, step_id: str, agent_id: str | None = None
    ) -> int:
        """Record a quality gate attempt for a step.

        Returns:
            Total number of attempts for this step
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
        step_index: int,
        agent_id: str | None = None,
    ) -> None:
        """Advance the session to a new step."""
        async with self._lock:
            stack = await self._read_stack(session_id, agent_id)
            if not stack:
                raise StateError(
                    "No active workflow session. Use start_workflow to begin a workflow."
                )

            session = stack[-1]
            session.current_step_id = step_id
            session.current_step_index = step_index
            await self._write_stack(session_id, stack, agent_id)

    async def go_to_step(
        self,
        session_id: str,
        step_id: str,
        step_index: int,
        invalidate_step_ids: list[str],
        agent_id: str | None = None,
    ) -> None:
        """Navigate back to a prior step, clearing progress from that step onward.

        Step history is preserved (not cleared) -- the step will appear again
        in history when start_step is called, showing the re-execution.

        Args:
            session_id: Claude Code session ID
            step_id: Step ID to navigate to
            step_index: Index of the target step in workflow steps
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
            session.current_step_index = step_index

            await self._write_stack(session_id, stack, agent_id)

    async def complete_workflow(
        self, session_id: str, agent_id: str | None = None
    ) -> WorkflowSession | None:
        """Mark the workflow as complete and remove from stack.

        The completed session is preserved in the completed_workflows list
        for status reporting.

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

            # Move from stack to completed_workflows
            completed = await self._read_completed_workflows(session_id, agent_id)
            completed.append(session)
            stack.pop()
            await self._write_stack(session_id, stack, agent_id, completed_workflows=completed)

            return stack[-1] if stack else None

    async def abort_workflow(
        self, session_id: str, explanation: str, agent_id: str | None = None
    ) -> tuple[WorkflowSession, WorkflowSession | None]:
        """Abort a workflow and remove from stack.

        The aborted session is preserved in the completed_workflows list
        for status reporting.

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

            # Move from stack to completed_workflows
            completed = await self._read_completed_workflows(session_id, agent_id)
            completed.append(session)
            stack.pop()
            await self._write_stack(session_id, stack, agent_id, completed_workflows=completed)

            new_active = stack[-1] if stack else None
            return session, new_active

    def get_all_outputs(
        self, session_id: str, agent_id: str | None = None
    ) -> dict[str, ArgumentValue]:
        """Get all outputs from all completed steps of the top-of-stack session."""
        session = self.resolve_session(session_id, agent_id)
        all_outputs: dict[str, ArgumentValue] = {}
        for progress in session.step_progress.values():
            all_outputs.update(progress.outputs)
        return all_outputs

    def get_step_input_values(
        self, session_id: str, step_id: str, agent_id: str | None = None
    ) -> dict[str, ArgumentValue]:
        """Get stored input values for a specific step."""
        session = self.resolve_session(session_id, agent_id)
        if step_id in session.step_progress:
            return session.step_progress[step_id].input_values
        return {}

    def get_stack(self, session_id: str, agent_id: str | None = None) -> list[StackEntry]:
        """Get the current workflow stack as StackEntry objects."""
        main_file = self._state_file(session_id, agent_id=None)
        main_stack: list[WorkflowSession] = []
        if main_file.exists():
            content = main_file.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
                main_stack = [
                    WorkflowSession.from_dict(entry) for entry in data.get("workflow_stack", [])
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
                        WorkflowSession.from_dict(entry) for entry in data.get("workflow_stack", [])
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

    def get_stack_depth(self, session_id: str, agent_id: str | None = None) -> int:
        """Get the current stack depth."""
        return len(self.get_stack(session_id, agent_id))

    def get_all_session_data(
        self, session_id: str
    ) -> dict[str | None, tuple[list[WorkflowSession], list[WorkflowSession]]]:
        """Return all stacks and completed workflows for a session.

        Scans the session directory for state.json and agent_*.json files.

        Args:
            session_id: Claude Code session ID

        Returns:
            Dict mapping agent_id (None for main) to
            (active_stack, completed_workflows) tuples
        """
        session_dir = self.sessions_dir / f"session-{session_id}"
        result: dict[str | None, tuple[list[WorkflowSession], list[WorkflowSession]]] = {}

        if not session_dir.exists():
            return result

        for state_file in sorted(session_dir.iterdir()):
            if not state_file.suffix == ".json":
                continue

            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            stack = [WorkflowSession.from_dict(entry) for entry in data.get("workflow_stack", [])]
            completed = [
                WorkflowSession.from_dict(entry) for entry in data.get("completed_workflows", [])
            ]

            if state_file.name == "state.json":
                agent_id = None
            elif state_file.name.startswith("agent_") and state_file.name.endswith(".json"):
                agent_id = state_file.name[len("agent_") : -len(".json")]
            else:
                continue

            result[agent_id] = (stack, completed)

        return result
