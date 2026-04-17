"""PreToolUse hook for tool requirements policy enforcement.

Fires before every tool call. Contacts the MCP sidecar server to check
whether the call complies with policies defined in
.deepwork/tool_requirements/*.yml.

Fail-closed: if the sidecar is unreachable, the hook denies the call
with a message to restart the MCP server.
"""

from __future__ import annotations

import http.client
import json
import os
import sys
from pathlib import Path
from typing import Any

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    output_hook_error,
    run_hook,
)
from deepwork.tool_requirements.sidecar import discover_sidecar

# Tool name substrings to skip (loop prevention)
_SKIP_TOOLS = ("appeal_tool_requirement",)


def tool_requirements_hook(hook_input: HookInput) -> HookOutput:
    """Pre-tool hook: check tool call against requirement policies."""
    if hook_input.event != NormalizedEvent.BEFORE_TOOL:
        return HookOutput()

    # Loop prevention: skip the appeal MCP tool itself
    raw_tool = hook_input.raw_input.get("tool_name", "")
    for skip in _SKIP_TOOLS:
        if skip in raw_tool:
            return HookOutput()

    cwd = hook_input.cwd or os.getcwd()
    session_id = hook_input.session_id or ""

    # Discover sidecar
    sidecar = discover_sidecar(Path(cwd), session_id)
    if sidecar is None:
        return _deny(
            "DeepWork Tool Requirements: MCP server is not running. "
            "The tool_requirements system requires the MCP server to be active. "
            "Please restart the MCP server."
        )

    # Send check request to sidecar
    try:
        response = _http_post(
            sidecar["port"],
            "/check",
            {
                "tool_name": hook_input.tool_name,
                "tool_input": hook_input.tool_input,
                "raw_tool_name": raw_tool,
                "session_id": session_id,
            },
        )
    except Exception as e:
        return _deny(
            f"DeepWork Tool Requirements: Failed to reach MCP server sidecar: {e}. "
            "Please restart the MCP server."
        )

    if response.get("decision") == "allow":
        return HookOutput()

    if response.get("decision") == "deny":
        reason = response.get("reason", "Tool call blocked by policy")
        return _deny(reason)

    # Unexpected response — allow (fail-open only for malformed responses
    # from an actually-running sidecar, not for missing sidecars)
    return HookOutput()


def _deny(reason: str) -> HookOutput:
    """Create a deny output for PreToolUse with proper Claude Code format."""
    return HookOutput(
        raw_output={
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def _http_post(port: int, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Send an HTTP POST to the sidecar on localhost."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        payload = json.dumps(body).encode("utf-8")
        conn.request(
            "POST",
            path,
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        data = response.read()
        result: dict[str, Any] = json.loads(data)
        return result
    finally:
        conn.close()


def main() -> int:
    """Entry point for the hook CLI."""
    platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
    return run_hook(tool_requirements_hook, platform)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        output_hook_error(e, context="tool_requirements hook")
        sys.exit(0)
