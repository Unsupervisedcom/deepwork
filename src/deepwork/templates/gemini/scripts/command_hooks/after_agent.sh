#!/bin/bash
# after_agent.sh - AfterAgent hook for Gemini CLI
#
# This script emulates Claude's per-command stop_hooks in Gemini CLI.
# It's designed to be registered as a global AfterAgent hook.
#
# What it does:
# 1. Reads the command state saved by before_agent.sh
# 2. If a slash command was invoked and has after_agent hooks, runs them
# 3. Returns appropriate JSON output for Gemini
#
# Exit codes (per Gemini hook contract):
# - 0: Success (output shown/injected)
# - 2: Blocking error (stderr shown, operation may be blocked)
# - Other: Non-blocking warning
#
# Usage in .gemini/settings.json:
# {
#   "hooks": {
#     "AfterAgent": [
#       {
#         "hooks": [{
#           "name": "deepwork-command-hooks",
#           "type": "command",
#           "command": ".gemini/scripts/command_hooks/after_agent.sh"
#         }]
#       }
#     ]
#   }
# }

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSE_SCRIPT="${SCRIPT_DIR}/parse_command_hooks.py"

# Read the hook input JSON from stdin
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Extract transcript_path from the hook input if available
TRANSCRIPT_PATH=""
if [ -n "${HOOK_INPUT}" ]; then
    TRANSCRIPT_PATH=$(echo "${HOOK_INPUT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('transcript_path', '') or d.get('session_transcript', '') or '')" 2>/dev/null || echo "")
fi

# Check if parse script exists
if [ ! -f "${PARSE_SCRIPT}" ]; then
    echo "Error: parse_command_hooks.py not found at ${PARSE_SCRIPT}" >&2
    exit 0  # Non-blocking
fi

# Get current state to check if we have a slash command with hooks
STATE=$(python3 "${PARSE_SCRIPT}" get-state 2>/dev/null || echo '{"slash_command": null}')

SLASH_COMMAND=$(echo "${STATE}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('slash_command') or '')" 2>/dev/null || echo "")

# If no slash command was detected by before_agent, nothing to do
if [ -z "${SLASH_COMMAND}" ]; then
    exit 0
fi

# Check if there are after_agent hooks
AFTER_HOOKS=$(echo "${STATE}" | python3 -c "import sys, json; d=json.load(sys.stdin); hooks=d.get('hooks', {}).get('after_agent', []); print('true' if hooks else 'false')" 2>/dev/null || echo "false")

if [ "${AFTER_HOOKS}" != "true" ]; then
    # No after_agent hooks, clean up state and exit
    python3 "${PARSE_SCRIPT}" clear 2>/dev/null || true
    exit 0
fi

# Run the after_agent hooks
RUN_ARGS="--event after_agent"
if [ -n "${TRANSCRIPT_PATH}" ]; then
    RUN_ARGS="${RUN_ARGS} --transcript-path ${TRANSCRIPT_PATH}"
fi

RESULT=$(python3 "${PARSE_SCRIPT}" run-hooks ${RUN_ARGS} 2>/dev/null || echo '{"executed": 0, "success": true}')

# Extract results
EXECUTED=$(echo "${RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('executed', 0))" 2>/dev/null || echo "0")
SUCCESS=$(echo "${RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print('true' if d.get('success', True) else 'false')" 2>/dev/null || echo "true")
INJECT_PROMPT=$(echo "${RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('inject_prompt', ''))" 2>/dev/null || echo "")

# Build output
OUTPUT=""
if [ -n "${INJECT_PROMPT}" ]; then
    # For prompt-type hooks (quality validation), output the prompt content
    # This will be shown to the agent for self-validation
    #
    # Note: Gemini's AfterAgent hook can return content that gets shown
    # to the user or injected back. We output the validation prompt so
    # the agent can self-assess if quality criteria are met.
    OUTPUT="${INJECT_PROMPT}"
fi

# Clean up state after running hooks
python3 "${PARSE_SCRIPT}" clear 2>/dev/null || true

# Output result
if [ -n "${OUTPUT}" ]; then
    # Output as plain text for Gemini to display
    echo "${OUTPUT}"
fi

if [ "${SUCCESS}" != "true" ]; then
    exit 2  # Blocking error - some hook failed
fi

exit 0
