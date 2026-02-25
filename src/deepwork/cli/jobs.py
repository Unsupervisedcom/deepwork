"""Jobs CLI commands for DeepWork.

Provides commands for inspecting active workflow sessions,
primarily used by hooks to restore context after compaction.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import click

from deepwork.jobs.discovery import find_job_dir
from deepwork.jobs.mcp.schemas import WorkflowSession
from deepwork.jobs.parser import ParseError, parse_job_definition

logger = logging.getLogger("deepwork.cli.jobs")


@click.group()
def jobs() -> None:
    """Job inspection commands."""
    pass


@jobs.command()
@click.option(
    "--path",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory (default: current directory)",
)
def get_stack(path: str) -> None:
    """Output active workflow sessions as JSON.

    Reads session state from .deepwork/tmp/ and enriches each active
    session with the job's common info and current step instructions.
    Used by post-compaction hooks to restore workflow context.
    """
    project_root = Path(path).resolve()
    result = _get_active_sessions(project_root)
    click.echo(json.dumps(result, indent=2))


def _list_sessions_sync(sessions_dir: Path) -> list[WorkflowSession]:
    """Read all session files synchronously.

    Args:
        sessions_dir: Path to .deepwork/tmp/ directory.

    Returns:
        List of WorkflowSession objects, sorted by started_at descending.
    """
    if not sessions_dir.exists():
        return []

    sessions: list[WorkflowSession] = []
    for session_file in sessions_dir.glob("session_*.json"):
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            sessions.append(WorkflowSession.from_dict(data))
        except (json.JSONDecodeError, ValueError):
            continue

    return sorted(sessions, key=lambda s: s.started_at, reverse=True)


def _get_active_sessions(project_root: Path) -> dict[str, Any]:
    """Load active sessions and enrich with job context.

    Args:
        project_root: Resolved path to the project root.

    Returns:
        Dict with "active_sessions" list ready for JSON serialization.
    """
    sessions_dir = project_root / ".deepwork" / "tmp"
    all_sessions = _list_sessions_sync(sessions_dir)

    active = [s for s in all_sessions if s.status == "active"]
    if not active:
        return {"active_sessions": []}

    sessions_out: list[dict[str, Any]] = []
    for session in active:
        # Determine completed steps from step_progress
        completed_steps = [
            sp.step_id for sp in session.step_progress.values() if sp.completed_at is not None
        ]

        entry: dict[str, Any] = {
            "session_id": session.session_id,
            "job_name": session.job_name,
            "workflow_name": session.workflow_name,
            "goal": session.goal,
            "current_step_id": session.current_step_id,
            "instance_id": session.instance_id,
            "completed_steps": completed_steps,
            "common_job_info": None,
            "current_step_instructions": None,
        }

        # Try to load job definition for enrichment
        job_dir = find_job_dir(project_root, session.job_name)
        if job_dir:
            try:
                job_def = parse_job_definition(job_dir)
                entry["common_job_info"] = job_def.common_job_info_provided_to_all_steps_at_runtime

                step = job_def.get_step(session.current_step_id)
                if step:
                    instructions_path = job_dir / step.instructions_file
                    if instructions_path.exists():
                        entry["current_step_instructions"] = instructions_path.read_text(
                            encoding="utf-8"
                        )

                    # Add step position in workflow
                    position = job_def.get_step_position_in_workflow(session.current_step_id)
                    if position:
                        entry["step_number"] = position[0]
                        entry["total_steps"] = position[1]
            except ParseError:
                logger.warning("Could not parse job definition for '%s'", session.job_name)

        sessions_out.append(entry)

    return {"active_sessions": sessions_out}
