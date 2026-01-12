#!/bin/bash
# policy_stop_hook.sh - Evaluates policies when the agent stops
#
# This script is called as a Claude Code Stop hook. It:
# 1. Gets the list of files changed during the session
# 2. Evaluates policies from .deepwork.policy.yml
# 3. Checks for <promise> tags in the agent's response
# 4. Returns JSON to continue if policies need attention
# 5. Resets the work tree baseline for the next iteration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if policy file exists
if [ ! -f .deepwork.policy.yml ]; then
    # No policies defined, nothing to do
    exit 0
fi

# Get changed files
changed_files=$("${SCRIPT_DIR}/get_changed_files.sh" 2>/dev/null || echo "")

# If no files changed, nothing to evaluate
if [ -z "${changed_files}" ]; then
    # Reset baseline for next iteration
    "${SCRIPT_DIR}/capture_work_tree.sh" 2>/dev/null || true
    exit 0
fi

# Call Python module to evaluate policies
# The Python module handles:
# - Parsing the policy file
# - Matching changed files against triggers/safety patterns
# - Checking for promise tags in stdin (the conversation context)
# - Generating appropriate JSON output

# Read the conversation context from stdin (if available)
conversation_context=""
if [ -t 0 ]; then
    # No stdin available
    conversation_context=""
else
    conversation_context=$(cat)
fi

# Call the Python evaluator
result=$(echo "${conversation_context}" | python -m deepwork.hooks.evaluate_policies \
    --policy-file .deepwork.policy.yml \
    --changed-files "${changed_files}" \
    2>/dev/null || echo '{}')

# Reset the work tree baseline for the next iteration
"${SCRIPT_DIR}/capture_work_tree.sh" 2>/dev/null || true

# Output the result (JSON for Claude Code hooks)
echo "${result}"
