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

    def register_mcp_server(self, project_path: Path) -> bool:
        """
        Register the DeepWork MCP server with the platform.

        Args:
            project_path: Path to project root

        Returns:
            True if server was registered, False if already registered

        Raises:
            AdapterError: If registration fails
        """
        # Default implementation does nothing - subclasses can override
        return False


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

    def _load_settings(self, project_path: Path) -> dict[str, Any]:
        """
        Load settings.json from the project.

        Args:
            project_path: Path to project root

        Returns:
            Settings dictionary (empty dict if file doesn't exist)

        Raises:
            AdapterError: If file exists but cannot be read
        """
        settings_file = project_path / self.config_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, encoding="utf-8") as f:
                    result: dict[str, Any] = json.load(f)
                    return result
            except (json.JSONDecodeError, OSError) as e:
                raise AdapterError(f"Failed to read settings.json: {e}") from e
        return {}

    def _save_settings(self, project_path: Path, settings: dict[str, Any]) -> None:
        """
        Save settings.json to the project.

        Args:
            project_path: Path to project root
            settings: Settings dictionary to save

        Raises:
            AdapterError: If file cannot be written
        """
        settings_file = project_path / self.config_dir / "settings.json"
        try:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except OSError as e:
            raise AdapterError(f"Failed to write settings.json: {e}") from e

    def add_permission(
        self, project_path: Path, permission: str, settings: dict[str, Any] | None = None
    ) -> bool:
        """
        Add a single permission to settings.json allow list.

        Args:
            project_path: Path to project root
            permission: The permission string to add (e.g., "Read(./.deepwork/tmp/**)")
            settings: Optional pre-loaded settings dict. If provided, modifies in-place
                     and does NOT save to disk (caller is responsible for saving).
                     If None, loads settings, adds permission, and saves.

        Returns:
            True if permission was added, False if already present

        Raises:
            AdapterError: If settings cannot be read/written
        """
        save_after = settings is None
        if settings is None:
            settings = self._load_settings(project_path)

        # Ensure permissions structure exists
        if "permissions" not in settings:
            settings["permissions"] = {}
        if "allow" not in settings["permissions"]:
            settings["permissions"]["allow"] = []

        # Add permission if not already present
        allow_list = settings["permissions"]["allow"]
        if permission not in allow_list:
            allow_list.append(permission)
            if save_after:
                self._save_settings(project_path, settings)
            return True
        return False

    def _get_settings_template_path(self) -> Path:
        """Get the path to the settings.json template for this adapter."""
        return Path(__file__).parent.parent / "templates" / self.name / "settings.json"

    def _load_required_permissions(self) -> list[str]:
        """Load required permissions from the settings template file."""
        settings_template = self._get_settings_template_path()
        with open(settings_template, encoding="utf-8") as f:
            template_settings = json.load(f)
        result: list[str] = template_settings["permissions"]["allow"]
        return result

    def sync_permissions(self, project_path: Path) -> int:
        """
        Sync required permissions to Claude Code settings.json.

        Loads permissions from the settings template file at
        templates/claude/settings.json and merges them into the
        project's .claude/settings.json.

        Args:
            project_path: Path to project root

        Returns:
            Number of permissions added

        Raises:
            AdapterError: If sync fails
        """
        required_permissions = self._load_required_permissions()

        # Load settings once, add all permissions, then save once
        settings = self._load_settings(project_path)
        added_count = 0

        for permission in required_permissions:
            if self.add_permission(project_path, permission, settings):
                added_count += 1

        # Save if any permissions were added
        if added_count > 0:
            self._save_settings(project_path, settings)

        return added_count

    def add_skill_permissions(self, project_path: Path, skill_paths: list[Path]) -> int:
        """
        Add Skill permissions for generated skills to settings.json.

        This allows Claude to invoke the skills without permission prompts.
        Uses the Skill(name) permission syntax.

        Note: Skill permissions are an emerging Claude Code feature and
        behavior may vary between versions.

        Args:
            project_path: Path to project root
            skill_paths: List of paths to generated skill files

        Returns:
            Number of permissions added

        Raises:
            AdapterError: If sync fails
        """
        if not skill_paths:
            return 0

        # Load settings once
        settings = self._load_settings(project_path)
        added_count = 0

        for skill_path in skill_paths:
            # Extract skill name from path
            # Path format: .claude/skills/job_name/SKILL.md -> job_name
            # Path format: .claude/skills/job_name.step_id/SKILL.md -> job_name.step_id
            skill_name = self._extract_skill_name(skill_path)
            if skill_name:
                permission = f"Skill({skill_name})"
                if self.add_permission(project_path, permission, settings):
                    added_count += 1

        # Save if any permissions were added
        if added_count > 0:
            self._save_settings(project_path, settings)

        return added_count

    def _extract_skill_name(self, skill_path: Path) -> str | None:
        """
        Extract skill name from a skill file path.

        Args:
            skill_path: Path to skill file (e.g., .claude/skills/job_name/SKILL.md)

        Returns:
            Skill name (e.g., "job_name") or None if cannot extract
        """
        # Handle both absolute and relative paths
        parts = skill_path.parts

        # Find 'skills' directory and get the next part
        try:
            skills_idx = parts.index("skills")
            if skills_idx + 1 < len(parts):
                # The skill name is the directory after 'skills'
                # e.g., skills/job_name/SKILL.md -> job_name
                return parts[skills_idx + 1]
        except ValueError:
            pass

        return None

    def register_mcp_server(self, project_path: Path) -> bool:
        """
        Register the DeepWork MCP server in .mcp.json at project root.

        Claude Code reads MCP server configurations from .mcp.json (project scope),
        not from settings.json. This method assumes the `deepwork` command is
        available in the user's PATH.

        Args:
            project_path: Path to project root

        Returns:
            True if server was registered or updated, False if no changes needed

        Raises:
            AdapterError: If registration fails
        """
        mcp_file = project_path / ".mcp.json"

        # Load existing .mcp.json or create new
        existing_config: dict[str, Any] = {}
        if mcp_file.exists():
            try:
                with open(mcp_file, encoding="utf-8") as f:
                    existing_config = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise AdapterError(f"Failed to read .mcp.json: {e}") from e

        # Initialize mcpServers if not present
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # Build the new MCP server config
        # Assume deepwork is available in PATH
        # Include --external-runner claude so quality gate reviews use Claude CLI subprocess
        new_server_config = {
            "command": "deepwork",
            "args": ["serve", "--path", ".", "--external-runner", "claude"],
        }

        # Check if already registered with same config
        existing_server = existing_config["mcpServers"].get("deepwork", {})
        if (
            existing_server.get("command") == new_server_config["command"]
            and existing_server.get("args") == new_server_config["args"]
        ):
            return False

        # Register or update the DeepWork MCP server
        existing_config["mcpServers"]["deepwork"] = new_server_config

        # Write .mcp.json
        try:
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(existing_config, f, indent=2)
        except OSError as e:
            raise AdapterError(f"Failed to write .mcp.json: {e}") from e

        return True


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

    # Gemini CLI does NOT support skill-level hooks
    # Hooks are global/project-level in settings.json, not per-skill
    hook_name_mapping: ClassVar[dict[SkillLifecycleHook, str]] = {}

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
