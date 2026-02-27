"""Workflow state management for MCP server.

State is persisted to `.deepwork/tmp/session_[id].json` for transparency
and recovery.

Supports nested workflows via a session stack - when a step starts a new
workflow, it's pushed onto the stack. When a workflow completes or is
aborted, it's popped from the stack.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles

from deepwork.jobs.mcp.schemas import StackEntry, StepProgress, WorkflowSession


class StateError(Exception):
    """Exception raised for state management errors."""

    pass


class StateManager:
    """Manages workflow session state with stack-based nesting support.

    Sessions are persisted to `.deepwork/tmp/` as JSON files for:
    - Transparency: Users can inspect session state
    - Recovery: Sessions survive server restarts
    - Debugging: State history is preserved

    This implementation is async-safe and uses a lock to prevent
    concurrent access issues.

    Supports nested workflows via a session stack - starting a new workflow
    while one is active pushes onto the stack. Completing or aborting pops
    from the stack.
    """

    def __init__(self, project_root: Path):
        """Initialize state manager.

        Args:
            project_root: Path to the project root
        """
        self.project_root = project_root
        self.sessions_dir = project_root / ".deepwork" / "tmp"
        self._session_stack: list[WorkflowSession] = []
        self._lock = asyncio.Lock()

    def _ensure_sessions_dir(self) -> None:
        """Ensure the sessions directory exists."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        """Get the path to a session file."""
        return self.sessions_dir / f"session_{session_id}.json"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())[:8]

    async def create_session(
        self,
        job_name: str,
        workflow_name: str,
        goal: str,
        first_step_id: str,
        instance_id: str | None = None,
    ) -> WorkflowSession:
        """Create a new workflow session.

        Args:
            job_name: Name of the job
            workflow_name: Name of the workflow
            goal: User's goal for this workflow
            first_step_id: ID of the first step
            instance_id: Optional instance identifier

        Returns:
            New WorkflowSession
        """
        async with self._lock:
            self._ensure_sessions_dir()

            session_id = self._generate_session_id()
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

            await self._save_session_unlocked(session)
            self._session_stack.append(session)
            return session

    async def _save_session_unlocked(self, session: WorkflowSession) -> None:
        """Save session to file (must be called with lock held)."""
        self._ensure_sessions_dir()
        session_file = self._session_file(session.session_id)
        content = json.dumps(session.to_dict(), indent=2)
        async with aiofiles.open(session_file, "w", encoding="utf-8") as f:
            await f.write(content)

    async def _save_session(self, session: WorkflowSession) -> None:
        """Save session to file with lock."""
        async with self._lock:
            await self._save_session_unlocked(session)

    async def load_session(self, session_id: str) -> WorkflowSession:
        """Load a session from file.

        Args:
            session_id: Session ID to load

        Returns:
            WorkflowSession

        Raises:
            StateError: If session not found
        """
        async with self._lock:
            session_file = self._session_file(session_id)
            if not session_file.exists():
                raise StateError(f"Session not found: {session_id}")

            async with aiofiles.open(session_file, encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)

            session = WorkflowSession.from_dict(data)
            # Replace top of stack or push if empty
            if self._session_stack:
                self._session_stack[-1] = session
            else:
                self._session_stack.append(session)
            return session

    def get_active_session(self) -> WorkflowSession | None:
        """Get the currently active session (top of stack).

        Returns:
            Active session or None if no session active
        """
        return self._session_stack[-1] if self._session_stack else None

    def require_active_session(self) -> WorkflowSession:
        """Get active session (top of stack) or raise error.

        Returns:
            Active session

        Raises:
            StateError: If no active session
        """
        if not self._session_stack:
            raise StateError("No active workflow session. Use start_workflow to begin a workflow.")
        return self._session_stack[-1]

    def _resolve_session(self, session_id: str | None = None) -> WorkflowSession:
        """Resolve a session by ID or fall back to top-of-stack.

        This is used internally (called inside locked blocks or sync methods)
        to find a specific session when session_id is provided, or fall back
        to the default top-of-stack behavior.

        Args:
            session_id: Optional session ID to look up. If None, returns top-of-stack.

        Returns:
            WorkflowSession matching the ID, or the active (top-of-stack) session.

        Raises:
            StateError: If session_id is provided but not found, or no active session.
        """
        if session_id:
            for s in self._session_stack:
                if s.session_id == session_id:
                    return s
            raise StateError(f"Session '{session_id}' not found in active stack")
        return self.require_active_session()

    async def start_step(self, step_id: str, session_id: str | None = None) -> None:
        """Mark a step as started.

        Args:
            step_id: Step ID to start
            session_id: Optional session ID to target a specific session

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)
            now = datetime.now(UTC).isoformat()

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(
                    step_id=step_id,
                    started_at=now,
                )
            else:
                session.step_progress[step_id].started_at = now

            session.current_step_id = step_id
            await self._save_session_unlocked(session)

    async def complete_step(
        self,
        step_id: str,
        outputs: dict[str, str | list[str]],
        notes: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Mark a step as completed.

        Args:
            step_id: Step ID to complete
            outputs: Map of output names to file path(s)
            notes: Optional notes
            session_id: Optional session ID to target a specific session

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)
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

            await self._save_session_unlocked(session)

    async def record_quality_attempt(self, step_id: str, session_id: str | None = None) -> int:
        """Record a quality gate attempt for a step.

        Args:
            step_id: Step ID
            session_id: Optional session ID to target a specific session

        Returns:
            Total number of attempts for this step

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(step_id=step_id)

            session.step_progress[step_id].quality_attempts += 1
            await self._save_session_unlocked(session)

            return session.step_progress[step_id].quality_attempts

    async def advance_to_step(
        self, step_id: str, entry_index: int, session_id: str | None = None
    ) -> None:
        """Advance the session to a new step.

        Args:
            step_id: New current step ID
            entry_index: Index in workflow step_entries
            session_id: Optional session ID to target a specific session

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)
            session.current_step_id = step_id
            session.current_entry_index = entry_index
            await self._save_session_unlocked(session)

    async def go_to_step(
        self,
        step_id: str,
        entry_index: int,
        invalidate_step_ids: list[str],
        session_id: str | None = None,
    ) -> None:
        """Navigate back to a prior step, clearing progress from that step onward.

        Args:
            step_id: Step ID to navigate to
            entry_index: Index of the target entry in workflow step_entries
            invalidate_step_ids: Step IDs whose progress should be cleared
            session_id: Optional session ID to target a specific session

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)

            # Clear progress for all invalidated steps
            for sid in invalidate_step_ids:
                if sid in session.step_progress:
                    del session.step_progress[sid]

            # Update position
            session.current_step_id = step_id
            session.current_entry_index = entry_index

            await self._save_session_unlocked(session)

    async def complete_workflow(self, session_id: str | None = None) -> WorkflowSession | None:
        """Mark the workflow as complete and remove from stack.

        Args:
            session_id: Optional session ID to target a specific session.
                If omitted, completes the top-of-stack session.

        Returns:
            The new active session after removal, or None if stack is empty

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)
            now = datetime.now(UTC).isoformat()
            session.completed_at = now
            session.status = "completed"
            await self._save_session_unlocked(session)

            # Remove completed session from stack (filter, not pop, for mid-stack removal)
            self._session_stack = [
                s for s in self._session_stack if s.session_id != session.session_id
            ]

            # Return new active session (if any)
            return self._session_stack[-1] if self._session_stack else None

    async def abort_workflow(
        self, explanation: str, session_id: str | None = None
    ) -> tuple[WorkflowSession, WorkflowSession | None]:
        """Abort a workflow and remove from stack.

        Args:
            explanation: Reason for aborting the workflow
            session_id: Optional session ID to target a specific session.
                If omitted, aborts the top-of-stack session.

        Returns:
            Tuple of (aborted session, new active session or None)

        Raises:
            StateError: If no active session or session_id not found
        """
        async with self._lock:
            session = self._resolve_session(session_id)
            now = datetime.now(UTC).isoformat()
            session.completed_at = now
            session.status = "aborted"
            session.abort_reason = explanation
            await self._save_session_unlocked(session)

            # Remove aborted session from stack (filter, not pop, for mid-stack removal)
            self._session_stack = [
                s for s in self._session_stack if s.session_id != session.session_id
            ]

            # Return aborted session and new active session (if any)
            new_active = self._session_stack[-1] if self._session_stack else None
            return session, new_active

    def get_all_outputs(self, session_id: str | None = None) -> dict[str, str | list[str]]:
        """Get all outputs from all completed steps.

        Args:
            session_id: Optional session ID to target a specific session

        Returns:
            Merged dict of all output names to file path(s)

        Raises:
            StateError: If no active session or session_id not found
        """
        session = self._resolve_session(session_id)
        all_outputs: dict[str, str | list[str]] = {}
        for progress in session.step_progress.values():
            all_outputs.update(progress.outputs)
        return all_outputs

    def get_stack(self) -> list[StackEntry]:
        """Get the current workflow stack as StackEntry objects.

        Returns:
            List of StackEntry with workflow and step info, bottom to top
        """
        return [
            StackEntry(
                workflow=f"{s.job_name}/{s.workflow_name}",
                step=s.current_step_id,
            )
            for s in self._session_stack
        ]

    def get_stack_depth(self) -> int:
        """Get the current stack depth.

        Returns:
            Number of active workflow sessions on the stack
        """
        return len(self._session_stack)

    async def list_sessions(self) -> list[WorkflowSession]:
        """List all saved sessions.

        Returns:
            List of WorkflowSession objects
        """
        if not self.sessions_dir.exists():
            return []

        sessions = []
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                async with aiofiles.open(session_file, encoding="utf-8") as f:
                    content = await f.read()
                    data = json.loads(content)
                sessions.append(WorkflowSession.from_dict(data))
            except (json.JSONDecodeError, ValueError):
                # Skip corrupted files
                continue

        return sorted(sessions, key=lambda s: s.started_at, reverse=True)

    async def find_active_sessions_for_workflow(
        self, job_name: str, workflow_name: str
    ) -> list[WorkflowSession]:
        """Find active sessions for a specific workflow.

        Args:
            job_name: Job name
            workflow_name: Workflow name

        Returns:
            List of active sessions matching the criteria
        """
        all_sessions = await self.list_sessions()
        return [
            s
            for s in all_sessions
            if s.job_name == job_name and s.workflow_name == workflow_name and s.status == "active"
        ]

    async def delete_session(self, session_id: str) -> None:
        """Delete a session file.

        Args:
            session_id: Session ID to delete
        """
        async with self._lock:
            session_file = self._session_file(session_id)
            if session_file.exists():
                session_file.unlink()

            # Remove from stack if present
            self._session_stack = [s for s in self._session_stack if s.session_id != session_id]
