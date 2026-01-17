#!/bin/bash
# rules_stop_hook.sh - Evaluates rules when the agent stops
#
# This script is called as a Claude Code Stop hook. It:
# 1. Evaluates rules from .deepwork/rules/
# 2. Computes changed files based on each rule's compare_to setting
# 3. Checks for <promise> tags in the conversation transcript
# 4. Returns JSON to block stop if rules need attention

set -e

# Check if rules directory exists with .md files
RULES_DIR=".deepwork/rules"

if [ ! -d "${RULES_DIR}" ]; then
    # No rules directory, nothing to do
    exit 0
fi

# Check if there are any .md files
if ! ls "${RULES_DIR}"/*.md 1>/dev/null 2>&1; then
    # No rule files, nothing to do
    exit 0
fi

# Read the hook input JSON from stdin
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Call the Python rules evaluator via the cross-platform wrapper
# The wrapper reads JSON input and handles transcript extraction
# Note: exit code 2 means "block" which is valid (not an error), so capture it
result=$(echo "${HOOK_INPUT}" | DEEPWORK_HOOK_PLATFORM=claude DEEPWORK_HOOK_EVENT=Stop python -m deepwork.hooks.rules_check 2>/dev/null) || true

# If no output (error case), provide empty JSON as fallback
if [ -z "${result}" ]; then
    result='{}'
fi

# Output the result (JSON for Claude Code hooks)
echo "${result}"
