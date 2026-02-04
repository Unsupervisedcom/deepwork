"""Workflow state management for MCP server.

State is persisted to `.deepwork/tmp/session_[id].json` for transparency
and recovery.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles

from deepwork.mcp.schemas import StepProgress, WorkflowSession


class StateError(Exception):
    """Exception raised for state management errors."""

    pass


class StateManager:
    """Manages workflow session state.

    Sessions are persisted to `.deepwork/tmp/` as JSON files for:
    - Transparency: Users can inspect session state
    - Recovery: Sessions survive server restarts
    - Debugging: State history is preserved

    This implementation is async-safe and uses a lock to prevent
    concurrent access issues.
    """

    def __init__(self, project_root: Path):
        """Initialize state manager.

        Args:
            project_root: Path to the project root
        """
        self.project_root = project_root
        self.sessions_dir = project_root / ".deepwork" / "tmp"
        self._active_session: WorkflowSession | None = None
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

    def _generate_branch_name(
        self, job_name: str, workflow_name: str, instance_id: str | None
    ) -> str:
        """Generate a git branch name for the workflow.

        Format: deepwork/[job_name]-[workflow_name]-[instance_id or date]
        """
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        instance = instance_id or date_str
        return f"deepwork/{job_name}-{workflow_name}-{instance}"

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
            branch_name = self._generate_branch_name(job_name, workflow_name, instance_id)
            now = datetime.now(UTC).isoformat()

            session = WorkflowSession(
                session_id=session_id,
                job_name=job_name,
                workflow_name=workflow_name,
                instance_id=instance_id,
                goal=goal,
                branch_name=branch_name,
                current_step_id=first_step_id,
                current_entry_index=0,
                step_progress={},
                started_at=now,
                status="active",
            )

            await self._save_session_unlocked(session)
            self._active_session = session
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
            self._active_session = session
            return session

    def get_active_session(self) -> WorkflowSession | None:
        """Get the currently active session.

        Returns:
            Active session or None if no session active
        """
        return self._active_session

    def require_active_session(self) -> WorkflowSession:
        """Get active session or raise error.

        Returns:
            Active session

        Raises:
            StateError: If no active session
        """
        if self._active_session is None:
            raise StateError(
                "No active workflow session. Use start_workflow to begin a workflow."
            )
        return self._active_session

    async def start_step(self, step_id: str) -> None:
        """Mark a step as started.

        Args:
            step_id: Step ID to start

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            session = self.require_active_session()
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
        self, step_id: str, outputs: list[str], notes: str | None = None
    ) -> None:
        """Mark a step as completed.

        Args:
            step_id: Step ID to complete
            outputs: Output files created
            notes: Optional notes

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            session = self.require_active_session()
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

    async def record_quality_attempt(self, step_id: str) -> int:
        """Record a quality gate attempt for a step.

        Args:
            step_id: Step ID

        Returns:
            Total number of attempts for this step

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            session = self.require_active_session()

            if step_id not in session.step_progress:
                session.step_progress[step_id] = StepProgress(step_id=step_id)

            session.step_progress[step_id].quality_attempts += 1
            await self._save_session_unlocked(session)

            return session.step_progress[step_id].quality_attempts

    async def advance_to_step(self, step_id: str, entry_index: int) -> None:
        """Advance the session to a new step.

        Args:
            step_id: New current step ID
            entry_index: Index in workflow step_entries

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            session = self.require_active_session()
            session.current_step_id = step_id
            session.current_entry_index = entry_index
            await self._save_session_unlocked(session)

    async def complete_workflow(self) -> None:
        """Mark the workflow as complete.

        Raises:
            StateError: If no active session
        """
        async with self._lock:
            session = self.require_active_session()
            now = datetime.now(UTC).isoformat()
            session.completed_at = now
            session.status = "completed"
            await self._save_session_unlocked(session)

    def get_all_outputs(self) -> list[str]:
        """Get all outputs from all completed steps.

        Returns:
            List of all output file paths

        Raises:
            StateError: If no active session
        """
        session = self.require_active_session()
        outputs: list[str] = []
        for progress in session.step_progress.values():
            outputs.extend(progress.outputs)
        return outputs

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
            if s.job_name == job_name
            and s.workflow_name == workflow_name
            and s.status == "active"
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

            if self._active_session and self._active_session.session_id == session_id:
                self._active_session = None
