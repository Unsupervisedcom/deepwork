"""Hooks syncer for DeepWork - collects and syncs hooks from jobs to platform settings."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from deepwork.core.adapters import AgentAdapter


class HooksSyncError(Exception):
    """Exception raised for hooks sync errors."""

    pass


@dataclass
class HookEntry:
    """Represents a single hook entry for a lifecycle event."""

    job_name: str  # Job that provides this hook
    job_dir: Path  # Full path to job directory
    script: str | None = None  # Script filename (if script-based hook)
    module: str | None = None  # Python module (if module-based hook)

    def get_command(self, project_path: Path) -> str:
        """
        Get the command to run this hook.

        Args:
            project_path: Path to project root

        Returns:
            Command string to execute
        """
        if self.module:
            # Python module - run directly with python -m
            return f"python -m {self.module}"
        elif self.script:
            # Script path is: .deepwork/jobs/{job_name}/hooks/{script}
            script_path = self.job_dir / "hooks" / self.script
            try:
                return str(script_path.relative_to(project_path))
            except ValueError:
                # If not relative, return the full path
                return str(script_path)
        else:
            raise ValueError("HookEntry must have either script or module")


@dataclass
class HookSpec:
    """Specification for a single hook (either script or module)."""

    script: str | None = None
    module: str | None = None


@dataclass
class JobHooks:
    """Hooks configuration for a job."""

    job_name: str
    job_dir: Path
    hooks: dict[str, list[HookSpec]] = field(default_factory=dict)  # event -> [HookSpec]

    @classmethod
    def from_job_dir(cls, job_dir: Path) -> "JobHooks | None":
        """
        Load hooks configuration from a job directory.

        Args:
            job_dir: Path to job directory containing hooks/global_hooks.yml

        Returns:
            JobHooks instance or None if no hooks defined
        """
        hooks_file = job_dir / "hooks" / "global_hooks.yml"
        if not hooks_file.exists():
            return None

        try:
            with open(hooks_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError):
            return None

        if not data or not isinstance(data, dict):
            return None

        # Parse hooks - each key is an event, value is list of scripts or module specs
        hooks: dict[str, list[HookSpec]] = {}
        for event, entries in data.items():
            if not isinstance(entries, list):
                entries = [entries]

            hook_specs: list[HookSpec] = []
            for entry in entries:
                if isinstance(entry, str):
                    # Simple script filename
                    hook_specs.append(HookSpec(script=entry))
                elif isinstance(entry, dict) and "module" in entry:
                    # Python module specification
                    hook_specs.append(HookSpec(module=entry["module"]))

            if hook_specs:
                hooks[event] = hook_specs

        if not hooks:
            return None

        return cls(
            job_name=job_dir.name,
            job_dir=job_dir,
            hooks=hooks,
        )


def collect_job_hooks(jobs_dir: Path) -> list[JobHooks]:
    """
    Collect hooks from all jobs in the jobs directory.

    Args:
        jobs_dir: Path to .deepwork/jobs directory

    Returns:
        List of JobHooks for all jobs with hooks defined
    """
    if not jobs_dir.exists():
        return []

    job_hooks_list = []
    for job_dir in jobs_dir.iterdir():
        if not job_dir.is_dir():
            continue

        job_hooks = JobHooks.from_job_dir(job_dir)
        if job_hooks:
            job_hooks_list.append(job_hooks)

    return job_hooks_list


def merge_hooks_for_platform(
    job_hooks_list: list[JobHooks],
    project_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """
    Merge hooks from multiple jobs into a single configuration.

    Args:
        job_hooks_list: List of JobHooks from different jobs
        project_path: Path to project root for relative path calculation

    Returns:
        Dict mapping lifecycle events to hook configurations
    """
    merged: dict[str, list[dict[str, Any]]] = {}

    for job_hooks in job_hooks_list:
        for event, hook_specs in job_hooks.hooks.items():
            if event not in merged:
                merged[event] = []

            for spec in hook_specs:
                entry = HookEntry(
                    job_name=job_hooks.job_name,
                    job_dir=job_hooks.job_dir,
                    script=spec.script,
                    module=spec.module,
                )
                command = entry.get_command(project_path)

                # Create hook configuration for Claude Code format
                hook_config = {
                    "matcher": "",  # Match all
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                        }
                    ],
                }

                # Check if this hook is already present (avoid duplicates)
                if not _hook_already_present(merged[event], command):
                    merged[event].append(hook_config)

    return merged


def _hook_already_present(hooks: list[dict[str, Any]], script_path: str) -> bool:
    """Check if a hook with the given script path is already in the list."""
    for hook in hooks:
        hook_list = hook.get("hooks", [])
        for h in hook_list:
            if h.get("command") == script_path:
                return True
    return False


def sync_hooks_to_platform(
    project_path: Path,
    adapter: AgentAdapter,
    job_hooks_list: list[JobHooks],
) -> int:
    """
    Sync hooks from jobs to a specific platform's settings.

    Args:
        project_path: Path to project root
        adapter: Agent adapter for the target platform
        job_hooks_list: List of JobHooks from jobs

    Returns:
        Number of hooks synced

    Raises:
        HooksSyncError: If sync fails
    """
    # Merge hooks from all jobs
    merged_hooks = merge_hooks_for_platform(job_hooks_list, project_path)

    if not merged_hooks:
        return 0

    # Delegate to adapter's sync_hooks method
    try:
        return adapter.sync_hooks(project_path, merged_hooks)
    except Exception as e:
        raise HooksSyncError(f"Failed to sync hooks: {e}") from e
