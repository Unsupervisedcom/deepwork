#!/usr/bin/env bash
# deepschema_write.sh - DeepSchema write hook
#
# Registered as a PostToolUse hook on Write/Edit in hooks.json.
# Delegates to the `deepwork hook deepschema_write` Python entry point,
# which validates the written file against applicable DeepSchemas.
#
# Always invokes via `uvx deepwork` to match the MCP server invocation
# in plugins/claude/.mcp.json. This avoids a class of PATH-staleness
# bugs where a user-level `deepwork` binary (e.g., `uv tool install
# deepwork`) is older than the hook module it is being asked to run,
# producing "Hook '...' not found" errors on every tool use.
#
# Input (stdin):  JSON from Claude Code PostToolUse hook
# Output (stdout): JSON response for Claude Code (allow/block + context)
# Exit codes:
#   0 on success, non-zero if uvx/the hook crashes (Claude Code
#   surfaces non-zero as a failed PostToolUse hook)

set -euo pipefail

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | uvx deepwork hook deepschema_write
