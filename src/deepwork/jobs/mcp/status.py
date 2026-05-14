"""Status file writer for external consumers.

Writes `.deepwork/tmp/status/v1/` files that external tools (UIs, dashboards,
monitoring) can read to understand the current state of jobs and workflow
sessions without going through the MCP protocol.

IMPORTANT: The file format is a stable external interface. Changes to the
structure of job_manifest.yml or sessions/<session_id>.yml require careful
consideration of backward compatibility.

Status writing is fire-and-forget — failures are logged as warnings and
never fail a tool call.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from deepwork.utils.yaml_utils import save_yaml

if TYPE_CHECKING:
    from deepwork.jobs.mcp.state import StateManager
    from deepwork.jobs.parser import JobDefinition

logger = logging.getLogger("deepwork.jobs.mcp.status")


def _derive_display_name(api_name: str) -> str:
    """Derive a human-readable display name from an API name.

    Replaces underscores and hyphens with spaces and title-cases the result.

    Args:
        api_name: The API/identifier name (e.g., "competitive_research")

    Returns:
        Human-readable name (e.g., "Competitive Research")
    """
    return api_name.replace("_", " ").replace("-", " ").title()


class StatusWriter:
    """Writes status files for external consumers.

    Produces two types of files:
    - job_manifest.yml: catalog of all available jobs/workflows/steps
    - sessions/<session_id>.yml: per-session workflow execution status
    """

    def __init__(self, project_root: Path):
        self.set_project_root(project_root)

    def set_project_root(self, project_root: Path) -> None:
        """Rebind status file paths to a new project root."""
        resolved = project_root.resolve()
        self.status_dir = resolved / ".deepwork" / "tmp" / "status" / "v1"
        self.manifest_path = self.status_dir / "job_manifest.yml"
        self.sessions_dir = self.status_dir / "sessions"

    def write_manifest(self, jobs: list[JobDefinition]) -> None:
        """Write job_manifest.yml with all available jobs, workflows, and steps.

        Jobs are sorted by name, workflows within each job are sorted by name.

        Args:
            jobs: List of parsed job definitions
        """
        sorted_jobs = sorted(jobs, key=lambda j: j.name)
        manifest_jobs: list[dict[str, Any]] = []

        for job in sorted_jobs:
            sorted_workflows = sorted(job.workflows.items(), key=lambda item: item[0])
            wf_list: list[dict[str, Any]] = []
            for wf_name, wf in sorted_workflows:
                steps_list: list[dict[str, str]] = []
                for step in wf.steps:
                    steps_list.append(
                        {
                            "name": step.name,
                            "display_name": _derive_display_name(step.name),
                        }
                    )
                wf_list.append(
                    {
                        "name": wf_name,
                        "display_name": _derive_display_name(wf_name),
                        "summary": wf.summary,
                        "steps": steps_list,
                    }
                )

            manifest_jobs.append(
                {
                    "name": job.name,
                    "display_name": _derive_display_name(job.name),
                    "summary": job.summary,
                    "workflows": wf_list,
                }
            )

        save_yaml(self.manifest_path, {"jobs": manifest_jobs})

    def write_session_status(
        self,
        session_id: str,
        state_manager: StateManager,
        job_loader: Any,
    ) -> None:
        """Write sessions/<session_id>.yml from current state.

        Reads all stacks (main + agent) for the session, loads job definitions
        to include workflow metadata, and writes a unified status file.

        Args:
            session_id: The session ID
            state_manager: StateManager instance to read state from
            job_loader: Callable that returns (list[JobDefinition], list[errors])
        """
        all_data = state_manager.get_all_session_data(session_id)
        if not all_data:
            return

        # Load job definitions for workflow metadata
        jobs, _ = job_loader()
        job_map: dict[str, JobDefinition] = {j.name: j for j in jobs}

        # Collect all workflow instances (active + completed)
        workflows_output: list[dict[str, Any]] = []
        active_instance_id: str | None = None

        for agent_id, (active_stack, completed_wfs) in sorted(
            all_data.items(), key=lambda x: (x[0] is not None, x[0] or "")
        ):
            # Active stack — top is the active workflow
            for i, session in enumerate(active_stack):
                wf_data = self._build_workflow_entry(session, agent_id, job_map)
                workflows_output.append(wf_data)
                # Top of main stack is the active workflow
                if agent_id is None and i == len(active_stack) - 1:
                    active_instance_id = session.workflow_instance_id

            # Completed/aborted workflows
            for session in completed_wfs:
                wf_data = self._build_workflow_entry(session, agent_id, job_map)
                workflows_output.append(wf_data)

        now = datetime.now(UTC).isoformat()
        status_data: dict[str, Any] = {
            "session_id": session_id,
            "last_updated_at": now,
            "active_workflow": active_instance_id,
            "workflows": workflows_output,
        }

        session_file = self.sessions_dir / f"{session_id}.yml"
        save_yaml(session_file, status_data)

    def _build_workflow_entry(
        self,
        session: Any,
        agent_id: str | None,
        job_map: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a workflow entry dict for the session status file.

        Args:
            session: WorkflowSession instance
            agent_id: Agent ID (None for main)
            job_map: Map of job names to JobDefinition instances

        Returns:
            Dict representing the workflow entry
        """
        # Build workflow definition snapshot
        wf_def: dict[str, Any] = {
            "name": session.workflow_name,
            "display_name": _derive_display_name(session.workflow_name),
            "summary": "",
        }

        # Enrich with job definition data if available
        job = job_map.get(session.job_name)
        if job:
            wf = job.workflows.get(session.workflow_name)
            if wf:
                wf_def["summary"] = wf.summary
                wf_def["steps"] = [
                    {
                        "name": step.name,
                        "display_name": _derive_display_name(step.name),
                    }
                    for step in wf.steps
                ]

        # Build ordered step history
        steps_output: list[dict[str, Any]] = []
        for entry in session.step_history:
            step_entry: dict[str, Any] = {
                "step_name": entry.step_id,
                "started_at": entry.started_at,
                "finished_at": entry.finished_at,
                "sub_workflow_instance_ids": entry.sub_workflow_instance_ids,
            }
            steps_output.append(step_entry)

        result: dict[str, Any] = {
            "workflow_instance_id": session.workflow_instance_id,
            "job_name": session.job_name,
            "status": session.status,
            "workflow": wf_def,
            "agent_id": agent_id,
            "steps": steps_output,
        }

        return result
