"""Hooks syncer for DeepWork - collects and syncs hooks from jobs to platform settings."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from deepwork.core.detector import PlatformConfig
from deepwork.utils.yaml_utils import load_yaml


class HooksSyncError(Exception):
    """Exception raised for hooks sync errors."""

    pass


@dataclass
class HookEntry:
    """Represents a single hook entry for a lifecycle event."""

    script: str  # Script filename
    job_name: str  # Job that provides this hook
    job_dir: Path  # Full path to job directory

    def get_script_path(self, project_path: Path) -> str:
        """
        Get the script path relative to project root.

        Args:
            project_path: Path to project root

        Returns:
            Relative path to script from project root
        """
        # Script path is: .deepwork/jobs/{job_name}/hooks/{script}
        script_path = self.job_dir / "hooks" / self.script
        try:
            return str(script_path.relative_to(project_path))
        except ValueError:
            # If not relative, return the full path
            return str(script_path)


@dataclass
class JobHooks:
    """Hooks configuration for a job."""

    job_name: str
    job_dir: Path
    hooks: dict[str, list[str]] = field(default_factory=dict)  # event -> [scripts]

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

        # Parse hooks - each key is an event, value is list of scripts
        hooks: dict[str, list[str]] = {}
        for event, scripts in data.items():
            if isinstance(scripts, list):
                hooks[event] = [str(s) for s in scripts]
            elif isinstance(scripts, str):
                hooks[event] = [scripts]

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
        for event, scripts in job_hooks.hooks.items():
            if event not in merged:
                merged[event] = []

            for script in scripts:
                entry = HookEntry(
                    script=script,
                    job_name=job_hooks.job_name,
                    job_dir=job_hooks.job_dir,
                )
                script_path = entry.get_script_path(project_path)

                # Create hook configuration for Claude Code format
                hook_config = {
                    "matcher": "",  # Match all
                    "hooks": [
                        {
                            "type": "command",
                            "command": script_path,
                        }
                    ],
                }

                # Check if this hook is already present (avoid duplicates)
                if not _hook_already_present(merged[event], script_path):
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


def sync_hooks_to_claude(
    project_path: Path,
    platform_config: PlatformConfig,
    hooks: dict[str, list[dict[str, Any]]],
) -> None:
    """
    Sync hooks to Claude Code settings.json.

    Args:
        project_path: Path to project root
        platform_config: Platform configuration
        hooks: Merged hooks configuration

    Raises:
        HooksSyncError: If sync fails
    """
    if not hooks:
        return

    settings_file = project_path / platform_config.config_dir / "settings.json"

    # Load existing settings or create new
    existing_settings: dict[str, Any] = {}
    if settings_file.exists():
        try:
            with open(settings_file, encoding="utf-8") as f:
                existing_settings = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise HooksSyncError(f"Failed to read settings.json: {e}") from e

    # Merge hooks into existing settings
    if "hooks" not in existing_settings:
        existing_settings["hooks"] = {}

    for event, event_hooks in hooks.items():
        if event not in existing_settings["hooks"]:
            existing_settings["hooks"][event] = []

        # Add new hooks that aren't already present
        for hook in event_hooks:
            script_path = hook.get("hooks", [{}])[0].get("command", "")
            if not _hook_already_present(existing_settings["hooks"][event], script_path):
                existing_settings["hooks"][event].append(hook)

    # Write back to settings.json
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(existing_settings, f, indent=2)
    except OSError as e:
        raise HooksSyncError(f"Failed to write settings.json: {e}") from e


def sync_hooks_to_platform(
    project_path: Path,
    platform_config: PlatformConfig,
    job_hooks_list: list[JobHooks],
) -> int:
    """
    Sync hooks from jobs to a specific platform's settings.

    Args:
        project_path: Path to project root
        platform_config: Platform configuration
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

    # Currently only Claude Code is fully supported
    if platform_config.name == "claude":
        sync_hooks_to_claude(project_path, platform_config, merged_hooks)
    else:
        # For other platforms, we'd add support here
        # For now, just skip
        return 0

    # Count total hooks
    total = sum(len(hooks) for hooks in merged_hooks.values())
    return total
