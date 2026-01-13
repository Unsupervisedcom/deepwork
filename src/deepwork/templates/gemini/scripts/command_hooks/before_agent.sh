#!/bin/bash
# before_agent.sh - BeforeAgent hook for Gemini CLI
#
# This script emulates Claude's per-command hooks in Gemini CLI.
# It's designed to be registered as a global BeforeAgent hook.
#
# What it does:
# 1. Receives the user prompt from Gemini via stdin (JSON format)
# 2. Detects if a slash command was invoked (e.g., /deepwork_jobs:define)
# 3. Looks up the job.yml for that command to find declared hooks
# 4. Stores command state in .deepwork/.command_hook_state.json
# 5. Runs any "before_prompt" hooks defined for the command
#
# Exit codes (per Gemini hook contract):
# - 0: Success (continue normally)
# - 2: Blocking error (stderr shown, operation may be blocked)
# - Other: Non-blocking warning
#
# Usage in .gemini/settings.json:
# {
#   "hooks": {
#     "BeforeAgent": [
#       {
#         "hooks": [{
#           "name": "deepwork-command-hooks",
#           "type": "command",
#           "command": ".gemini/scripts/command_hooks/before_agent.sh"
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

# Check if parse script exists
if [ ! -f "${PARSE_SCRIPT}" ]; then
    echo "Error: parse_command_hooks.py not found at ${PARSE_SCRIPT}" >&2
    exit 0  # Non-blocking - don't fail the session
fi

# Detect slash command from the prompt
# The parse script handles extracting the prompt from Gemini's JSON format
DETECT_RESULT=$(echo "${HOOK_INPUT}" | python3 "${PARSE_SCRIPT}" detect 2>/dev/null || echo '{"slash_command": null}')

# Extract info from detection result
SLASH_COMMAND=$(echo "${DETECT_RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('slash_command') or '')" 2>/dev/null || echo "")
HAS_HOOKS=$(echo "${DETECT_RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print('true' if d.get('has_hooks') else 'false')" 2>/dev/null || echo "false")

# If no slash command detected, nothing to do
if [ -z "${SLASH_COMMAND}" ]; then
    exit 0
fi

# Log detection (useful for debugging)
# echo "[DeepWork] Detected slash command: /${SLASH_COMMAND}" >&2

# If there are before_prompt hooks, run them
if [ "${HAS_HOOKS}" = "true" ]; then
    BEFORE_RESULT=$(python3 "${PARSE_SCRIPT}" run-hooks --event before_prompt 2>/dev/null || echo '{"executed": 0}')

    EXECUTED=$(echo "${BEFORE_RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('executed', 0))" 2>/dev/null || echo "0")
    SUCCESS=$(echo "${BEFORE_RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print('true' if d.get('success', True) else 'false')" 2>/dev/null || echo "true")

    if [ "${EXECUTED}" -gt 0 ]; then
        # Check if there's prompt content to inject
        INJECT_PROMPT=$(echo "${BEFORE_RESULT}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('inject_prompt', ''))" 2>/dev/null || echo "")

        if [ -n "${INJECT_PROMPT}" ]; then
            # Output the prompt injection as JSON (Gemini will include this in context)
            # Using the Gemini hook output format
            echo "{\"message\": \"${INJECT_PROMPT}\"}"
        fi

        if [ "${SUCCESS}" != "true" ]; then
            exit 2  # Blocking error
        fi
    fi
fi

exit 0
