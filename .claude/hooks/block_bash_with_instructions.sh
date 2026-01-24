#!/bin/bash
# block_bash_with_instructions.sh - Blocks specific bash commands and provides alternative instructions
#
# This hook intercepts Bash tool use calls and blocks commands that match
# specific patterns, providing alternative instructions to the agent.
#
# Usage: Registered as a PreToolUse hook in .claude/settings.json
#
# Input (stdin): JSON from Claude Code hook system containing tool_name and tool_input
# Output (stdout): JSON response with error message if blocked
# Exit codes:
#   0 - Success (allow action)
#   2 - Blocking error (prevent action with message)

set -e

# =============================================================================
# BLOCKED COMMANDS CONFIGURATION
# =============================================================================
# Format: Each entry is a regex pattern followed by a delimiter (|||) and instructions
# The regex is matched against the full bash command
# Add new blocked commands here:

BLOCKED_COMMANDS=(
    'git[[:space:]]+commit|||All commits must be done via the `/commit` skill. Do not use git commit directly. Instead, run `/commit` to start the commit workflow which includes code review, testing, and linting before committing.'
)

# =============================================================================
# HOOK LOGIC - DO NOT MODIFY BELOW UNLESS NECESSARY
# =============================================================================

# Read stdin into variable
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Exit early if no input
if [ -z "${HOOK_INPUT}" ]; then
    exit 0
fi

# Extract tool_name from input
TOOL_NAME=$(echo "${HOOK_INPUT}" | jq -r '.tool_name // empty' 2>/dev/null)

# Only process Bash tool calls
if [ "${TOOL_NAME}" != "Bash" ]; then
    exit 0
fi

# Extract the command from tool_input
COMMAND=$(echo "${HOOK_INPUT}" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Exit if no command
if [ -z "${COMMAND}" ]; then
    exit 0
fi

# Check each blocked pattern
for entry in "${BLOCKED_COMMANDS[@]}"; do
    # Split entry by delimiter
    pattern="${entry%%|||*}"
    instructions="${entry##*|||}"

    # Check if command matches pattern (using extended regex)
    if echo "${COMMAND}" | grep -qE "${pattern}"; then
        # Output error message as JSON
        cat << EOF
{"error": "${instructions}"}
EOF
        exit 2
    fi
done

# Command is allowed
exit 0
