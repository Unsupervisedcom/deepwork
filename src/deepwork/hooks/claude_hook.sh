#!/bin/bash
# claude_hook.sh - Claude Code hook wrapper
#
# This script wraps Python hooks to work with Claude Code's hook system.
# It handles input/output normalization so Python hooks can be written once
# and work on any supported platform.
#
# Usage:
#   claude_hook.sh <hook_name>
#
# Example:
#   claude_hook.sh rules_check
#
# The hook is run via the deepwork CLI, which works regardless of how
# deepwork was installed (pipx, uv, nix flake, etc.).
#
# Environment variables set by Claude Code:
#   CLAUDE_PROJECT_DIR - Absolute path to project root
#
# Input (stdin): JSON from Claude Code hook system
# Output (stdout): JSON response for Claude Code
# Exit codes:
#   0 - Success (allow action)
#   2 - Blocking error (prevent action)

set -e

# Get the hook name to run
HOOK_NAME="${1:-}"

if [ -z "${HOOK_NAME}" ]; then
    echo "Usage: claude_hook.sh <hook_name>" >&2
    echo "Example: claude_hook.sh rules_check" >&2
    exit 1
fi

# Read stdin into variable
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Set platform environment variable for the hook
export DEEPWORK_HOOK_PLATFORM="claude"

# Run the hook via deepwork CLI
# This works regardless of how deepwork was installed (pipx, uv, nix flake, etc.)
echo "${HOOK_INPUT}" | deepwork hook "${HOOK_NAME}"
exit_code=$?

exit ${exit_code}
