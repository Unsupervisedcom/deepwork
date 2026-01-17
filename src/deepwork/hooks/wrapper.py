"""
Hook wrapper module for cross-platform hook compatibility.

This module provides utilities for normalizing hook input/output between
different AI CLI platforms (Claude Code, Gemini CLI, etc.).

The wrapper system allows writing hooks once in Python and running them
on any supported platform. Platform-specific shell scripts handle the
input/output translation, while Python hooks work with a normalized format.

Normalized Format:
    Input:
        - session_id: str
        - transcript_path: str
        - cwd: str
        - event: str (normalized: 'after_agent', 'before_tool', 'before_prompt')
        - tool_name: str (normalized: 'write_file', 'shell', etc.)
        - tool_input: dict
        - prompt: str (for agent events)
        - raw_input: dict (original platform-specific input)

    Output:
        - decision: str ('block', 'allow', 'deny')
        - reason: str (explanation for blocking)
        - context: str (additional context to add)
        - raw_output: dict (will be merged into final output)

Usage:
    # In a Python hook:
    from deepwork.hooks.wrapper import HookInput, HookOutput, normalize_input, denormalize_output

    def my_hook(input_data: HookInput) -> HookOutput:
        if should_block:
            return HookOutput(decision='block', reason='Must do X first')
        return HookOutput()  # Allow
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Platform(str, Enum):
    """Supported AI CLI platforms."""

    CLAUDE = "claude"
    GEMINI = "gemini"


class NormalizedEvent(str, Enum):
    """Normalized hook event names."""

    AFTER_AGENT = "after_agent"
    BEFORE_TOOL = "before_tool"
    BEFORE_PROMPT = "before_prompt"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    AFTER_TOOL = "after_tool"
    BEFORE_MODEL = "before_model"
    AFTER_MODEL = "after_model"


# Event name mappings from platform-specific to normalized
EVENT_TO_NORMALIZED: dict[Platform, dict[str, NormalizedEvent]] = {
    Platform.CLAUDE: {
        "Stop": NormalizedEvent.AFTER_AGENT,
        "SubagentStop": NormalizedEvent.AFTER_AGENT,
        "PreToolUse": NormalizedEvent.BEFORE_TOOL,
        "PostToolUse": NormalizedEvent.AFTER_TOOL,
        "UserPromptSubmit": NormalizedEvent.BEFORE_PROMPT,
        "SessionStart": NormalizedEvent.SESSION_START,
        "SessionEnd": NormalizedEvent.SESSION_END,
    },
    Platform.GEMINI: {
        "AfterAgent": NormalizedEvent.AFTER_AGENT,
        "BeforeTool": NormalizedEvent.BEFORE_TOOL,
        "AfterTool": NormalizedEvent.AFTER_TOOL,
        "BeforeAgent": NormalizedEvent.BEFORE_PROMPT,
        "SessionStart": NormalizedEvent.SESSION_START,
        "SessionEnd": NormalizedEvent.SESSION_END,
        "BeforeModel": NormalizedEvent.BEFORE_MODEL,
        "AfterModel": NormalizedEvent.AFTER_MODEL,
    },
}

# Normalized event to platform-specific event name
NORMALIZED_TO_EVENT: dict[Platform, dict[NormalizedEvent, str]] = {
    Platform.CLAUDE: {
        NormalizedEvent.AFTER_AGENT: "Stop",
        NormalizedEvent.BEFORE_TOOL: "PreToolUse",
        NormalizedEvent.AFTER_TOOL: "PostToolUse",
        NormalizedEvent.BEFORE_PROMPT: "UserPromptSubmit",
        NormalizedEvent.SESSION_START: "SessionStart",
        NormalizedEvent.SESSION_END: "SessionEnd",
    },
    Platform.GEMINI: {
        NormalizedEvent.AFTER_AGENT: "AfterAgent",
        NormalizedEvent.BEFORE_TOOL: "BeforeTool",
        NormalizedEvent.AFTER_TOOL: "AfterTool",
        NormalizedEvent.BEFORE_PROMPT: "BeforeAgent",
        NormalizedEvent.SESSION_START: "SessionStart",
        NormalizedEvent.SESSION_END: "SessionEnd",
        NormalizedEvent.BEFORE_MODEL: "BeforeModel",
        NormalizedEvent.AFTER_MODEL: "AfterModel",
    },
}

# Tool name mappings from platform-specific to normalized (snake_case)
TOOL_TO_NORMALIZED: dict[Platform, dict[str, str]] = {
    Platform.CLAUDE: {
        "Write": "write_file",
        "Edit": "edit_file",
        "Read": "read_file",
        "Bash": "shell",
        "Glob": "glob",
        "Grep": "grep",
        "WebFetch": "web_fetch",
        "WebSearch": "web_search",
        "Task": "task",
    },
    Platform.GEMINI: {
        # Gemini already uses snake_case
        "write_file": "write_file",
        "edit_file": "edit_file",
        "read_file": "read_file",
        "shell": "shell",
        "glob": "glob",
        "grep": "grep",
        "web_fetch": "web_fetch",
        "web_search": "web_search",
    },
}

# Normalized tool names to platform-specific
NORMALIZED_TO_TOOL: dict[Platform, dict[str, str]] = {
    Platform.CLAUDE: {
        "write_file": "Write",
        "edit_file": "Edit",
        "read_file": "Read",
        "shell": "Bash",
        "glob": "Glob",
        "grep": "Grep",
        "web_fetch": "WebFetch",
        "web_search": "WebSearch",
        "task": "Task",
    },
    Platform.GEMINI: {
        # Gemini already uses snake_case
        "write_file": "write_file",
        "edit_file": "edit_file",
        "read_file": "read_file",
        "shell": "shell",
        "glob": "glob",
        "grep": "grep",
        "web_fetch": "web_fetch",
        "web_search": "web_search",
    },
}


@dataclass
class HookInput:
    """Normalized hook input data."""

    platform: Platform
    event: NormalizedEvent
    session_id: str = ""
    transcript_path: str = ""
    cwd: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_response: str = ""
    prompt: str = ""
    raw_input: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], platform: Platform) -> HookInput:
        """Create HookInput from raw platform-specific input."""
        # Get event name and normalize
        raw_event = data.get("hook_event_name", "")
        event_map = EVENT_TO_NORMALIZED.get(platform, {})
        event = event_map.get(raw_event, NormalizedEvent.AFTER_AGENT)

        # Get tool name and normalize
        raw_tool = data.get("tool_name", "")
        tool_map = TOOL_TO_NORMALIZED.get(platform, {})
        tool_name = tool_map.get(raw_tool, raw_tool.lower())

        return cls(
            platform=platform,
            event=event,
            session_id=data.get("session_id", ""),
            transcript_path=data.get("transcript_path", ""),
            cwd=data.get("cwd", ""),
            tool_name=tool_name,
            tool_input=data.get("tool_input", {}),
            tool_response=data.get("tool_response", ""),
            prompt=data.get("prompt", ""),
            raw_input=data,
        )


@dataclass
class HookOutput:
    """Normalized hook output data."""

    decision: str = ""  # 'block', 'allow', 'deny', '' (empty = allow)
    reason: str = ""  # Explanation for blocking
    context: str = ""  # Additional context to add
    continue_loop: bool = True  # False to terminate agent loop
    stop_reason: str = ""  # Message when stopping
    suppress_output: bool = False  # Hide from transcript
    raw_output: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, platform: Platform, event: NormalizedEvent) -> dict[str, Any]:
        """Convert to platform-specific output format."""
        result: dict[str, Any] = {}

        # Handle decision
        if self.decision:
            if platform == Platform.GEMINI and self.decision == "block":
                # Gemini prefers 'deny'
                result["decision"] = "deny"
            else:
                result["decision"] = self.decision

        # Handle reason
        if self.reason:
            result["reason"] = self.reason

        # Handle continue_loop
        if not self.continue_loop:
            result["continue"] = False
            if self.stop_reason:
                result["stopReason"] = self.stop_reason

        # Handle suppress_output
        if self.suppress_output:
            result["suppressOutput"] = True

        # Handle context (platform-specific)
        if self.context:
            if platform == Platform.CLAUDE:
                # Claude uses different fields depending on event
                if event == NormalizedEvent.SESSION_START:
                    result.setdefault("hookSpecificOutput", {})
                    result["hookSpecificOutput"]["hookEventName"] = NORMALIZED_TO_EVENT[platform][
                        event
                    ]
                    result["hookSpecificOutput"]["additionalContext"] = self.context
                else:
                    result["systemMessage"] = self.context
            else:
                # Gemini
                result.setdefault("hookSpecificOutput", {})
                result["hookSpecificOutput"]["hookEventName"] = NORMALIZED_TO_EVENT[platform].get(
                    event, str(event)
                )
                result["hookSpecificOutput"]["additionalContext"] = self.context

        # Merge any raw output
        for key, value in self.raw_output.items():
            if key not in result:
                result[key] = value

        return result


def normalize_input(raw_json: str, platform: Platform) -> HookInput:
    """
    Parse raw JSON input and normalize it.

    Args:
        raw_json: JSON string from stdin
        platform: Source platform

    Returns:
        Normalized HookInput
    """
    try:
        data = json.loads(raw_json) if raw_json.strip() else {}
    except json.JSONDecodeError:
        data = {}

    return HookInput.from_dict(data, platform)


def denormalize_output(output: HookOutput, platform: Platform, event: NormalizedEvent) -> str:
    """
    Convert normalized output to platform-specific JSON.

    Args:
        output: Normalized HookOutput
        platform: Target platform
        event: The event being processed

    Returns:
        JSON string for stdout
    """
    result = output.to_dict(platform, event)
    return json.dumps(result) if result else "{}"


def read_stdin() -> str:
    """Read all input from stdin."""
    if sys.stdin.isatty():
        return ""
    try:
        return sys.stdin.read()
    except Exception:
        return ""


def write_stdout(data: str) -> None:
    """Write output to stdout."""
    print(data)


def run_hook(
    hook_fn: Callable[[HookInput], HookOutput],
    platform: Platform,
) -> int:
    """
    Run a hook function with normalized input/output.

    This is the main entry point for Python hooks. It:
    1. Reads raw input from stdin
    2. Normalizes the input
    3. Calls the hook function
    4. Denormalizes the output
    5. Writes to stdout

    Args:
        hook_fn: Function that takes HookInput and returns HookOutput
        platform: The platform calling this hook

    Returns:
        Exit code (0 for success, 2 for blocking)
    """
    # Read and normalize input
    raw_input = read_stdin()
    hook_input = normalize_input(raw_input, platform)

    # Call the hook
    try:
        hook_output = hook_fn(hook_input)
    except Exception as e:
        # On error, allow the action but log
        print(f"Hook error: {e}", file=sys.stderr)
        hook_output = HookOutput()

    # Denormalize and write output
    output_json = denormalize_output(hook_output, platform, hook_input.event)
    write_stdout(output_json)

    # Always return 0 when using JSON output format
    # The decision field in the JSON controls blocking behavior
    return 0
