#!/usr/bin/env bash
# post_commit_reminder.sh - Post-commit review reminder hook
#
# Registered as a PostToolUse hook on Bash in hooks.json.
# Delegates to the `deepwork hook post_commit_reminder` Python entry
# point, which inspects the Bash command and (when it is a `git commit`)
# nudges the agent to run the `review` skill if matching review rules
# have not been marked as passed for the committed files.
#
# Always invokes via `uvx deepwork` to match the MCP server invocation
# in plugins/claude/.mcp.json. This avoids a class of PATH-staleness
# bugs where a user-level `deepwork` binary (e.g., `uv tool install
# deepwork`) is older than the hook module it is being asked to run,
# producing "Hook '...' not found" errors on every Bash tool use.
#
# Input (stdin):  JSON from Claude Code PostToolUse hook
# Output (stdout): JSON response for Claude Code (additionalContext for
#                  the agent, or empty {} when nothing to add)
# Exit codes:
#   0 on success, non-zero if uvx/the hook crashes (Claude Code
#   surfaces non-zero as a failed PostToolUse hook)

set -euo pipefail

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | uvx deepwork hook post_commit_reminder
