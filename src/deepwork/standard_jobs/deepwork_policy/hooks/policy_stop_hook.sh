#!/bin/bash
# policy_stop_hook.sh - Evaluates policies when the agent stops
#
# This script is called as a Claude Code Stop hook. It:
# 1. Evaluates policies from .deepwork/policies/
# 2. Computes changed files based on each policy's compare_to setting
# 3. Checks for <promise> tags in the conversation transcript
# 4. Returns JSON to block stop if policies need attention

set -e

# Check if policies directory exists with .md files
POLICY_DIR=".deepwork/policies"

if [ ! -d "${POLICY_DIR}" ]; then
    # No policies directory, nothing to do
    exit 0
fi

# Check if there are any .md files
if ! ls "${POLICY_DIR}"/*.md 1>/dev/null 2>&1; then
    # No policy files, nothing to do
    exit 0
fi

# Read the hook input JSON from stdin
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Call the Python policy evaluator via the cross-platform wrapper
# The wrapper reads JSON input and handles transcript extraction
# Note: exit code 2 means "block" which is valid (not an error), so capture it
result=$(echo "${HOOK_INPUT}" | DEEPWORK_HOOK_PLATFORM=claude DEEPWORK_HOOK_EVENT=Stop python -m deepwork.hooks.policy_check 2>/dev/null) || true

# If no output (error case), provide empty JSON as fallback
if [ -z "${result}" ]; then
    result='{}'
fi

# Output the result (JSON for Claude Code hooks)
echo "${result}"
