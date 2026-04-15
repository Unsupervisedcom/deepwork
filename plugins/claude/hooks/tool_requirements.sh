#!/usr/bin/env bash
# tool_requirements.sh - PreToolUse hook for tool requirements enforcement
#
# Fires before every tool call. Delegates to the Python hook which contacts
# the MCP sidecar to check policies.
#
# Input (stdin):  JSON from Claude Code PreToolUse hook
# Output (stdout): JSON with hookSpecificOutput.permissionDecision
# Exit codes:
#   0 - Always (decision encoded in JSON output)

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | deepwork hook tool_requirements
exit $?
