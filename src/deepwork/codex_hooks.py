"""Codex hook setup and hook entrypoints for DeepWork."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepwork.cli.jobs import _get_active_sessions
from deepwork.hooks.deepschema_write import deepschema_write_hook
from deepwork.hooks.wrapper import HookInput, HookOutput, NormalizedEvent, Platform
from deepwork.utils.fs import ensure_dir

_TABLE_HEADER_RE = re.compile(r"^\s*\[\[?.*?\]\]?\s*(?:#.*)?$")
_FEATURES_HEADER_RE = re.compile(r"^\s*\[features\]\s*(?:#.*)?$")
_FEATURES_CHILD_RE = re.compile(r"^\s*\[features\.[^\]]+\]\s*(?:#.*)?$")
_CODEX_HOOKS_KEY_RE = re.compile(r"^\s*codex_hooks\s*=")

_SESSION_START_COMMAND = "uvx deepwork codex-hook session_start"
_POST_TOOL_USE_COMMAND = "uvx deepwork codex-hook post_tool_use"
_POST_WRITE_COMMAND = "uvx deepwork codex-hook post_write"
_POST_EDIT_COMMAND = "uvx deepwork codex-hook post_edit"

_REVIEW_REMINDER = (
    "You MUST offer to run the `review` skill to review the changes you just committed "
    "if you have not run a review recently."
)


class CodexHookSetupError(Exception):
    """Raised when DeepWork cannot safely set up Codex hooks."""


@dataclass(frozen=True)
class CodexHookSetupResult:
    """Summary of repo-local Codex hook setup changes."""

    config_updated: bool
    hooks_updated: bool


def setup_codex_hooks(project_root: Path) -> CodexHookSetupResult:
    """Ensure repo-local Codex config enables hooks and registers DeepWork handlers."""
    codex_dir = ensure_dir(project_root / ".codex")
    config_updated = ensure_codex_hooks_enabled(codex_dir / "config.toml")
    hooks_updated = ensure_codex_hook_entries(codex_dir / "hooks.json")
    return CodexHookSetupResult(
        config_updated=config_updated,
        hooks_updated=hooks_updated,
    )


def ensure_codex_hooks_enabled(config_path: Path) -> bool:
    """Ensure `.codex/config.toml` has `[features].codex_hooks = true`."""
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""

    if existing:
        try:
            parsed = tomllib.loads(existing)
        except tomllib.TOMLDecodeError as e:
            raise CodexHookSetupError(f"Failed to parse {config_path}: {e}") from e
        if (
            isinstance(parsed.get("features"), dict)
            and parsed["features"].get("codex_hooks") is True
        ):
            return False

    updated = _set_codex_hooks_flag(existing)
    if updated == existing and config_path.exists():
        return False

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return True


def ensure_codex_hook_entries(hooks_path: Path) -> bool:
    """Ensure `.codex/hooks.json` contains the DeepWork Codex hook entries."""
    if hooks_path.exists():
        try:
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CodexHookSetupError(f"Failed to parse {hooks_path}: {e}") from e
    else:
        payload = {}

    if not isinstance(payload, dict):
        raise CodexHookSetupError(f"{hooks_path} must contain a JSON object.")

    hooks = payload.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise CodexHookSetupError(f"{hooks_path} field 'hooks' must be a JSON object.")

    changed = False
    changed |= _ensure_command_hook(
        hooks=hooks,
        event_name="SessionStart",
        matcher="startup|resume",
        command=_SESSION_START_COMMAND,
        status_message="Loading DeepWork context",
    )
    changed |= _ensure_command_hook(
        hooks=hooks,
        event_name="PostToolUse",
        matcher="Bash",
        command=_POST_TOOL_USE_COMMAND,
        status_message="Checking DeepWork post-tool hooks",
    )
    changed |= _ensure_command_hook(
        hooks=hooks,
        event_name="PostToolUse",
        matcher="Write",
        command=_POST_WRITE_COMMAND,
        status_message="Validating DeepSchema after write",
    )
    changed |= _ensure_command_hook(
        hooks=hooks,
        event_name="PostToolUse",
        matcher="Edit",
        command=_POST_EDIT_COMMAND,
        status_message="Validating DeepSchema after edit",
    )

    if not changed and hooks_path.exists():
        return False

    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return True


def build_session_start_output(hook_input: dict[str, Any]) -> dict[str, Any]:
    """Build Codex SessionStart hook output for DeepWork."""
    session_id = str(hook_input.get("session_id") or "").strip()
    cwd_value = str(hook_input.get("cwd") or "").strip()
    source = str(hook_input.get("source") or "").strip()

    parts: list[str] = []
    if session_id:
        parts.append(f"DEEPWORK_SESSION_ID={session_id}")
        parts.append("Use this value as `session_id` when calling DeepWork MCP tools.")

    if source == "resume" and cwd_value:
        restored = _build_restored_workflow_context(Path(cwd_value))
        if restored:
            parts.append(restored)

    if not parts:
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(parts),
        }
    }


def build_post_tool_use_output(hook_input: dict[str, Any]) -> dict[str, Any]:
    """Build Codex PostToolUse hook output for DeepWork."""
    tool_input = hook_input.get("tool_input")
    if not isinstance(tool_input, dict):
        return {}

    command = str(tool_input.get("command") or "")
    if "git commit" not in command:
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": _REVIEW_REMINDER,
        }
    }


def build_deepschema_output(
    hook_input: dict[str, Any],
    tool_name: str,
) -> dict[str, Any]:
    """Build Codex PostToolUse hook output for DeepSchema write/edit validation."""
    normalized = HookInput(
        platform=Platform.CLAUDE,
        event=NormalizedEvent.AFTER_TOOL,
        session_id=str(hook_input.get("session_id") or ""),
        cwd=str(hook_input.get("cwd") or ""),
        tool_name=tool_name,
        tool_input=_extract_tool_input(hook_input),
        raw_input=hook_input,
    )
    result = deepschema_write_hook(normalized)
    return _hook_output_to_codex_payload(result)


def run_codex_hook(hook_name: str, raw_input: str) -> str:
    """Execute a DeepWork Codex hook and return a JSON response string."""
    try:
        parsed = json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    if hook_name == "session_start":
        output = build_session_start_output(parsed)
    elif hook_name == "post_tool_use":
        output = build_post_tool_use_output(parsed)
    elif hook_name == "post_write":
        output = build_deepschema_output(parsed, "write_file")
    elif hook_name == "post_edit":
        output = build_deepschema_output(parsed, "edit_file")
    else:
        raise CodexHookSetupError(f"Unknown Codex hook: {hook_name}")

    return json.dumps(output) if output else "{}"


def _set_codex_hooks_flag(existing: str) -> str:
    """Return TOML content with `[features].codex_hooks = true` enabled."""
    if not existing.strip():
        return "[features]\ncodex_hooks = true\n"

    lines = existing.splitlines(keepends=True)
    features_index = _find_matching_line(lines, _FEATURES_HEADER_RE)
    if features_index is not None:
        return _update_explicit_features_section(lines, features_index)

    features_child_index = _find_matching_line(lines, _FEATURES_CHILD_RE)
    block = "[features]\ncodex_hooks = true\n\n"
    if features_child_index is not None:
        lines.insert(features_child_index, block)
        return "".join(lines)

    suffix = "" if existing.endswith("\n") else "\n"
    return f"{existing}{suffix}\n[features]\ncodex_hooks = true\n"


def _update_explicit_features_section(lines: list[str], features_index: int) -> str:
    """Set or insert `codex_hooks = true` inside an explicit `[features]` section."""
    section_end = len(lines)
    for i in range(features_index + 1, len(lines)):
        if _TABLE_HEADER_RE.match(lines[i]):
            section_end = i
            break

    for i in range(features_index + 1, section_end):
        if _CODEX_HOOKS_KEY_RE.match(lines[i]):
            newline = "\n" if lines[i].endswith("\n") else ""
            lines[i] = f"codex_hooks = true{newline}"
            return "".join(lines)

    lines.insert(section_end, "codex_hooks = true\n")
    return "".join(lines)


def _find_matching_line(lines: list[str], pattern: re.Pattern[str]) -> int | None:
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i
    return None


def _extract_tool_input(hook_input: dict[str, Any]) -> dict[str, Any]:
    """Extract tool input from Codex hook payloads."""
    tool_input = hook_input.get("tool_input")
    if isinstance(tool_input, dict):
        return tool_input

    fallback: dict[str, Any] = {}
    if "file_path" in hook_input:
        fallback["file_path"] = hook_input["file_path"]
    if "command" in hook_input:
        fallback["command"] = hook_input["command"]
    return fallback


def _hook_output_to_codex_payload(output: HookOutput) -> dict[str, Any]:
    """Convert a normalized hook output into Codex command-hook JSON."""
    if output.context:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": output.context,
            }
        }
    if output.raw_output:
        return output.raw_output
    if output.decision or output.reason:
        payload: dict[str, Any] = {}
        if output.decision:
            payload["decision"] = output.decision
        if output.reason:
            payload["reason"] = output.reason
        return payload
    return {}


def _ensure_command_hook(
    hooks: dict[str, Any],
    event_name: str,
    matcher: str,
    command: str,
    status_message: str,
) -> bool:
    """Ensure a command hook is present under the given event/matcher."""
    event_entries = hooks.setdefault(event_name, [])
    if not isinstance(event_entries, list):
        raise CodexHookSetupError(f"Hook event '{event_name}' must be a JSON array.")

    handler = {
        "type": "command",
        "command": command,
        "statusMessage": status_message,
    }

    for entry in event_entries:
        if not isinstance(entry, dict):
            continue
        entry_matcher = entry.get("matcher", "")
        if entry_matcher != matcher:
            continue

        hook_list = entry.setdefault("hooks", [])
        if not isinstance(hook_list, list):
            raise CodexHookSetupError(
                f"Hook event '{event_name}' matcher '{matcher}' must have a 'hooks' array."
            )

        for existing in hook_list:
            if (
                isinstance(existing, dict)
                and existing.get("type") == "command"
                and existing.get("command") == command
            ):
                return False

        hook_list.append(handler)
        return True

    event_entries.append(
        {
            "matcher": matcher,
            "hooks": [handler],
        }
    )
    return True


def _build_restored_workflow_context(project_root: Path) -> str | None:
    """Build developer context for active DeepWork sessions on resume."""
    result = _get_active_sessions(project_root.resolve())
    sessions = result.get("active_sessions")
    if not isinstance(sessions, list) or not sessions:
        return None

    lines = [
        "# DeepWork Workflow Context",
        "",
        "You are in the middle of a DeepWork workflow. Use the DeepWork MCP tools to continue.",
        "Call `finished_step` with your outputs when you complete the current step.",
    ]

    for session in sessions:
        if not isinstance(session, dict):
            continue

        session_id = session.get("session_id", "")
        job_name = session.get("job_name", "")
        workflow_name = session.get("workflow_name", "")
        goal = session.get("goal", "")
        current_step = session.get("current_step_id", "")
        step_number = session.get("step_number")
        total_steps = session.get("total_steps")
        completed_steps = session.get("completed_steps") or []
        common_info = session.get("common_job_info")
        step_instructions = session.get("current_step_instructions")

        if step_number and total_steps:
            current_step_label = f"{current_step} (step {step_number} of {total_steps})"
        else:
            current_step_label = str(current_step)

        lines.extend(
            [
                "",
                f"## Active Session: {session_id}",
                f"- **Workflow**: {job_name}/{workflow_name}",
                f"- **Goal**: {goal}",
                f"- **Current Step**: {current_step_label}",
            ]
        )

        if completed_steps:
            completed = ", ".join(str(step) for step in completed_steps)
            lines.append(f"- **Completed Steps**: {completed}")

        if common_info:
            lines.extend(["", "### Common Job Info", str(common_info)])

        if step_instructions:
            lines.extend(["", "### Current Step Instructions", str(step_instructions)])

    return "\n".join(lines)
