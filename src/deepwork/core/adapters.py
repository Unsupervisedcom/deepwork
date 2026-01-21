"""Agent adapters for AI coding assistants."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar


class AdapterError(Exception):
    """Exception raised for adapter errors."""

    pass


class SkillLifecycleHook(str, Enum):
    """Generic skill lifecycle hook events supported by DeepWork.

    These represent hook points in the AI agent's skill execution lifecycle.
    Each adapter maps these generic names to platform-specific event names.
    The enum values are the generic names used in job.yml files.
    """

    # Triggered after the agent finishes responding (before returning to user)
    # Use for quality validation loops, output verification
    AFTER_AGENT = "after_agent"

    # Triggered before the agent uses a tool
    # Use for tool-specific validation or pre-processing
    BEFORE_TOOL = "before_tool"

    # Triggered when the user submits a new prompt
    # Use for session initialization, context setup
    BEFORE_PROMPT = "before_prompt"


# List of all supported skill lifecycle hooks
SKILL_LIFECYCLE_HOOKS_SUPPORTED: list[SkillLifecycleHook] = list(SkillLifecycleHook)


class AgentAdapter(ABC):
    """Base class for AI agent platform adapters.

    Subclasses are automatically registered when defined, enabling dynamic
    discovery of supported platforms.
    """

    # Class-level registry for auto-discovery
    _registry: ClassVar[dict[str, type[AgentAdapter]]] = {}

    # Platform configuration (subclasses define as class attributes)
    name: ClassVar[str]
    display_name: ClassVar[str]
    config_dir: ClassVar[str]
    skills_dir: ClassVar[str] = "skills"
    skill_template: ClassVar[str] = "skill-job-step.md.jinja"
    meta_skill_template: ClassVar[str] = "skill-job-meta.md.jinja"

    # Instructions for reloading skills after sync (shown to users)
    # Subclasses should override with platform-specific instructions.
    reload_instructions: ClassVar[str] = "Restart your AI assistant session to use the new skills."

    # Mapping from generic SkillLifecycleHook to platform-specific event names.
    # Subclasses should override this to provide platform-specific mappings.
    hook_name_mapping: ClassVar[dict[SkillLifecycleHook, str]] = {}

    def __init__(self, project_root: Path | str | None = None):
        """
        Initialize adapter with optional project root.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root) if project_root else None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-register subclasses."""
        super().__init_subclass__(**kwargs)
        # Only register if the class has a name attribute set (not inherited default)
        if "name" in cls.__dict__ and cls.name:
            AgentAdapter._registry[cls.name] = cls

    @classmethod
    def get_all(cls) -> dict[str, type[AgentAdapter]]:
        """
        Return all registered adapter classes.

        Returns:
            Dict mapping adapter names to adapter classes
        """
        return cls._registry.copy()

    @classmethod
    def get(cls, name: str) -> type[AgentAdapter]:
        """
        Get adapter class by name.

        Args:
            name: Adapter name (e.g., "claude", "gemini", "copilot")

        Returns:
            Adapter class

        Raises:
            AdapterError: If adapter name is not registered
        """
        if name not in cls._registry:
            raise AdapterError(
                f"Unknown adapter '{name}'. Supported adapters: {', '.join(cls._registry.keys())}"
            )
        return cls._registry[name]

    @classmethod
    def list_names(cls) -> list[str]:
        """
        List all registered adapter names.

        Returns:
            List of adapter names
        """
        return list(cls._registry.keys())

    def get_template_dir(self, templates_root: Path) -> Path:
        """
        Get the template directory for this adapter.

        Args:
            templates_root: Root directory containing platform templates

        Returns:
            Path to this adapter's template directory
        """
        return templates_root / self.name

    def get_skills_dir(self, project_root: Path | None = None) -> Path:
        """
        Get the skills directory path.

        Args:
            project_root: Project root (uses instance's project_root if not provided)

        Returns:
            Path to skills directory

        Raises:
            AdapterError: If no project root specified
        """
        root = project_root or self.project_root
        if not root:
            raise AdapterError("No project root specified")
        return root / self.config_dir / self.skills_dir

    def get_meta_skill_filename(self, job_name: str) -> str:
        """
        Get the filename for a job's meta-skill.

        The meta-skill is the primary user interface for a job.
        Can be overridden for different file formats.

        Args:
            job_name: Name of the job

        Returns:
            Meta-skill filename (e.g., "job_name/SKILL.md" for Claude)
        """
        return f"{job_name}/SKILL.md"

    def get_step_skill_filename(self, job_name: str, step_id: str, exposed: bool = False) -> str:
        """
        Get the filename for a step skill.

        All step skills use the same filename format. The exposed parameter
        is used for template context (user-invocable frontmatter setting).

        Args:
            job_name: Name of the job
            step_id: ID of the step
            exposed: If True, skill is user-invocable (for template context). Default: False.

        Returns:
            Skill filename (e.g., "job_name.step_id/SKILL.md" for Claude)
        """
        return f"{job_name}.{step_id}/SKILL.md"

    def detect(self, project_root: Path | None = None) -> bool:
        """
        Check if this platform is available in the project.

        Args:
            project_root: Project root (uses instance's project_root if not provided)

        Returns:
            True if platform config directory exists
        """
        root = project_root or self.project_root
        if not root:
            return False
        config_path = root / self.config_dir
        return config_path.exists() and config_path.is_dir()

    def get_platform_hook_name(self, hook: SkillLifecycleHook) -> str | None:
        """
        Get the platform-specific event name for a generic hook.

        Args:
            hook: Generic SkillLifecycleHook

        Returns:
            Platform-specific event name, or None if not supported
        """
        return self.hook_name_mapping.get(hook)

    def supports_hook(self, hook: SkillLifecycleHook) -> bool:
        """
        Check if this adapter supports a specific hook.

        Args:
            hook: Generic SkillLifecycleHook

        Returns:
            True if the hook is supported
        """
        return hook in self.hook_name_mapping

    @abstractmethod
    def sync_hooks(self, project_path: Path, hooks: dict[str, list[dict[str, Any]]]) -> int:
        """
        Sync hooks to platform settings.

        Args:
            project_path: Path to project root
            hooks: Dict mapping lifecycle events to hook configurations

        Returns:
            Number of hooks synced

        Raises:
            AdapterError: If sync fails
        """
        pass

    def sync_permissions(self, project_path: Path) -> int:
        """
        Sync required permissions to platform settings.

        This method adds any permissions that DeepWork requires to function
        properly (e.g., access to .deepwork/tmp/ directory).

        Args:
            project_path: Path to project root

        Returns:
            Number of permissions added

        Raises:
            AdapterError: If sync fails
        """
        # Default implementation does nothing - subclasses can override
        return 0


def _hook_already_present(hooks: list[dict[str, Any]], script_path: str) -> bool:
    """Check if a hook with the given script path is already in the list."""
    for hook in hooks:
        hook_list = hook.get("hooks", [])
        for h in hook_list:
            if h.get("command") == script_path:
                return True
    return False


# =============================================================================
# Platform Adapters
# =============================================================================
#
# Each adapter must define hook_name_mapping to indicate which hooks it supports.
# Use an empty dict {} for platforms that don't support skill-level hooks.
#
# Hook support reviewed:
# - Claude Code: Full support (Stop, PreToolUse, UserPromptSubmit) - reviewed 2026-01-16
#   All three skill lifecycle hooks are supported in markdown frontmatter.
#   See: doc/platforms/claude/hooks_system.md
# - Gemini CLI: No skill-level hooks (reviewed 2026-01-12)
#   Gemini's hooks are global/project-level in settings.json, not per-skill.
#   TOML skill files only support 'prompt' and 'description' fields.
#   See: doc/platforms/gemini/hooks_system.md
# =============================================================================


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude Code."""

    name = "claude"
    display_name = "Claude Code"
    config_dir = ".claude"

    # Claude Code doesn't have a reload command - must restart session
    reload_instructions: ClassVar[str] = (
        "Type 'exit' to leave your current session, then run "
        "'claude --resume' (your history will be maintained)."
    )

    # Claude Code uses PascalCase event names
    hook_name_mapping: ClassVar[dict[SkillLifecycleHook, str]] = {
        SkillLifecycleHook.AFTER_AGENT: "Stop",
        SkillLifecycleHook.BEFORE_TOOL: "PreToolUse",
        SkillLifecycleHook.BEFORE_PROMPT: "UserPromptSubmit",
    }

    def sync_hooks(self, project_path: Path, hooks: dict[str, list[dict[str, Any]]]) -> int:
        """
        Sync hooks to Claude Code settings.json.

        Args:
            project_path: Path to project root
            hooks: Merged hooks configuration

        Returns:
            Number of hooks synced

        Raises:
            AdapterError: If sync fails
        """
        if not hooks:
            return 0

        settings_file = project_path / self.config_dir / "settings.json"

        # Load existing settings or create new
        existing_settings: dict[str, Any] = {}
        if settings_file.exists():
            try:
                with open(settings_file, encoding="utf-8") as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise AdapterError(f"Failed to read settings.json: {e}") from e

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
            raise AdapterError(f"Failed to write settings.json: {e}") from e

        # Count total hooks
        total = sum(len(hooks_list) for hooks_list in hooks.values())
        return total

    def sync_permissions(self, project_path: Path) -> int:
        """
        Sync required permissions to Claude Code settings.json.

        Adds permissions for unrestricted access to .deepwork/tmp/** directory,
        which is used for temporary files during DeepWork operations.

        Args:
            project_path: Path to project root

        Returns:
            Number of permissions added

        Raises:
            AdapterError: If sync fails
        """
        settings_file = project_path / self.config_dir / "settings.json"

        # Load existing settings or create new
        existing_settings: dict[str, Any] = {}
        if settings_file.exists():
            try:
                with open(settings_file, encoding="utf-8") as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise AdapterError(f"Failed to read settings.json: {e}") from e

        # Ensure permissions structure exists
        if "permissions" not in existing_settings:
            existing_settings["permissions"] = {}
        if "allow" not in existing_settings["permissions"]:
            existing_settings["permissions"]["allow"] = []

        # Define required permissions for .deepwork/tmp/**
        required_permissions = [
            "Read(.deepwork/tmp/**)",
            "Edit(.deepwork/tmp/**)",
            "Write(.deepwork/tmp/**)",
        ]

        # Add permissions that are not already present
        allow_list = existing_settings["permissions"]["allow"]
        added_count = 0
        for perm in required_permissions:
            if perm not in allow_list:
                allow_list.append(perm)
                added_count += 1

        # Only write back if we added new permissions
        if added_count > 0:
            try:
                settings_file.parent.mkdir(parents=True, exist_ok=True)
                with open(settings_file, "w", encoding="utf-8") as f:
                    json.dump(existing_settings, f, indent=2)
            except OSError as e:
                raise AdapterError(f"Failed to write settings.json: {e}") from e

        return added_count


class GeminiAdapter(AgentAdapter):
    """Adapter for Gemini CLI.

    Gemini CLI uses TOML format for custom skills stored in .gemini/skills/.
    Skills use colon (:) for namespacing instead of dot (.).

    Note: Gemini CLI does NOT support skill-level hooks. Hooks are configured
    globally in settings.json, not per-skill. Therefore, hook_name_mapping
    is empty and sync_hooks returns 0.

    See: doc/platforms/gemini/hooks_system.md
    """

    name = "gemini"
    display_name = "Gemini CLI"
    config_dir = ".gemini"
    skill_template = "skill-job-step.toml.jinja"
    meta_skill_template = "skill-job-meta.toml.jinja"

    # Gemini CLI can reload with /memory refresh
    reload_instructions: ClassVar[str] = (
        "Run '/memory refresh' to reload skills, or restart your Gemini CLI session."
    )

    # Gemini CLI does NOT support skill-level hooks
    # Hooks are global/project-level in settings.json, not per-skill
    hook_name_mapping: ClassVar[dict[SkillLifecycleHook, str]] = {}

    def get_meta_skill_filename(self, job_name: str) -> str:
        """
        Get the filename for a Gemini job's meta-skill.

        Gemini uses TOML files and colon namespacing via subdirectories.
        For job "my_job", creates: my_job/index.toml

        Args:
            job_name: Name of the job

        Returns:
            Meta-skill filename path (e.g., "my_job/index.toml")
        """
        return f"{job_name}/index.toml"

    def get_step_skill_filename(self, job_name: str, step_id: str, exposed: bool = False) -> str:
        """
        Get the filename for a Gemini step skill.

        Gemini uses TOML files and colon namespacing via subdirectories.
        All step skills use the same filename format. The exposed parameter
        is used for template context (user-invocable setting).
        For job "my_job" and step "step_one", creates: my_job/step_one.toml

        Args:
            job_name: Name of the job
            step_id: ID of the step
            exposed: If True, skill is user-invocable (for template context). Default: False.

        Returns:
            Skill filename path (e.g., "my_job/step_one.toml")
        """
        return f"{job_name}/{step_id}.toml"

    def sync_hooks(self, project_path: Path, hooks: dict[str, list[dict[str, Any]]]) -> int:
        """
        Sync hooks to Gemini CLI settings.

        Gemini CLI does not support skill-level hooks. All hooks are
        configured globally in settings.json. This method is a no-op
        that always returns 0.

        Args:
            project_path: Path to project root
            hooks: Dict mapping lifecycle events to hook configurations (ignored)

        Returns:
            0 (Gemini does not support skill-level hooks)
        """
        # Gemini CLI does not support skill-level hooks
        # Hooks are configured globally in settings.json, not per-skill
        return 0
