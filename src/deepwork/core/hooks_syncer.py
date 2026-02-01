"""Hooks syncer for DeepWork - collects and syncs hooks from experts to platform settings."""

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

    expert_name: str  # Expert that provides this hook
    expert_dir: Path  # Full path to expert directory
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
            # Python module - use deepwork hook CLI for portability
            # Extract hook name from module path (e.g., "deepwork.hooks.rules_check" -> "rules_check")
            hook_name = self.module.rsplit(".", 1)[-1]
            return f"deepwork hook {hook_name}"
        elif self.script:
            # Script path is: .deepwork/experts/{expert_name}/hooks/{script}
            script_path = self.expert_dir / "hooks" / self.script
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
class ExpertHooks:
    """Hooks configuration for an expert."""

    expert_name: str
    expert_dir: Path
    hooks: dict[str, list[HookSpec]] = field(default_factory=dict)  # event -> [HookSpec]

    @classmethod
    def from_expert_dir(cls, expert_dir: Path) -> "ExpertHooks | None":
        """
        Load hooks configuration from an expert directory.

        Args:
            expert_dir: Path to expert directory containing hooks/global_hooks.yml

        Returns:
            ExpertHooks instance or None if no hooks defined
        """
        hooks_file = expert_dir / "hooks" / "global_hooks.yml"
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
            expert_name=expert_dir.name,
            expert_dir=expert_dir,
            hooks=hooks,
        )


def collect_expert_hooks(experts_dir: Path) -> list[ExpertHooks]:
    """
    Collect hooks from all experts in the experts directory.

    Args:
        experts_dir: Path to .deepwork/experts directory

    Returns:
        List of ExpertHooks for all experts with hooks defined
    """
    if not experts_dir.exists():
        return []

    expert_hooks_list = []
    for expert_dir in experts_dir.iterdir():
        if not expert_dir.is_dir():
            continue

        # Check if this is a valid expert (has expert.yml)
        if not (expert_dir / "expert.yml").exists():
            continue

        expert_hooks = ExpertHooks.from_expert_dir(expert_dir)
        if expert_hooks:
            expert_hooks_list.append(expert_hooks)

    return expert_hooks_list


def merge_hooks_for_platform(
    expert_hooks_list: list[ExpertHooks],
    project_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """
    Merge hooks from multiple experts into a single configuration.

    Args:
        expert_hooks_list: List of ExpertHooks from different experts
        project_path: Path to project root for relative path calculation

    Returns:
        Dict mapping lifecycle events to hook configurations
    """
    merged: dict[str, list[dict[str, Any]]] = {}

    for expert_hooks in expert_hooks_list:
        for event, hook_specs in expert_hooks.hooks.items():
            if event not in merged:
                merged[event] = []

            for spec in hook_specs:
                entry = HookEntry(
                    expert_name=expert_hooks.expert_name,
                    expert_dir=expert_hooks.expert_dir,
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

    # Claude Code has separate Stop and SubagentStop events. When a Stop hook
    # is defined, also register it for SubagentStop so it triggers for both
    # the main agent and subagents.
    if "Stop" in merged:
        if "SubagentStop" not in merged:
            merged["SubagentStop"] = []
        for hook_config in merged["Stop"]:
            hooks_list = hook_config.get("hooks", [])
            command = hooks_list[0].get("command", "") if hooks_list else ""
            if command and not _hook_already_present(merged["SubagentStop"], command):
                merged["SubagentStop"].append(hook_config)

    return merged


def _hook_already_present(hooks: list[dict[str, Any]], command: str) -> bool:
    """Check if a hook with the given command is already in the list."""
    for hook in hooks:
        hook_list = hook.get("hooks", [])
        for h in hook_list:
            if h.get("command") == command:
                return True
    return False


def sync_hooks_to_platform(
    project_path: Path,
    adapter: AgentAdapter,
    expert_hooks_list: list[ExpertHooks],
) -> int:
    """
    Sync hooks from experts to a specific platform's settings.

    Args:
        project_path: Path to project root
        adapter: Agent adapter for the target platform
        expert_hooks_list: List of ExpertHooks from experts

    Returns:
        Number of hooks synced

    Raises:
        HooksSyncError: If sync fails
    """
    # Merge hooks from all experts
    merged_hooks = merge_hooks_for_platform(expert_hooks_list, project_path)

    if not merged_hooks:
        return 0

    # Delegate to adapter's sync_hooks method
    try:
        return adapter.sync_hooks(project_path, merged_hooks)
    except Exception as e:
        raise HooksSyncError(f"Failed to sync hooks: {e}") from e
