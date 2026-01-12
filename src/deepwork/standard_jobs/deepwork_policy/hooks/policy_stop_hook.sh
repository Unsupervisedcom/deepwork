#!/bin/bash
# policy_stop_hook.sh - Evaluates policies when the agent stops
#
# This script is called as a Claude Code Stop hook. It:
# 1. Gets the list of files changed during the session
# 2. Evaluates policies from .deepwork.policy.yml
# 3. Checks for <promise> tags in the conversation transcript
# 4. Returns JSON to block stop if policies need attention
# 5. Resets the work tree baseline for the next iteration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if policy file exists
if [ ! -f .deepwork.policy.yml ]; then
    # No policies defined, nothing to do
    exit 0
fi

# Read the hook input JSON from stdin
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Extract transcript_path from the hook input JSON using jq
# Claude Code passes: {"session_id": "...", "transcript_path": "...", ...}
TRANSCRIPT_PATH=""
if [ -n "${HOOK_INPUT}" ]; then
    TRANSCRIPT_PATH=$(echo "${HOOK_INPUT}" | jq -r '.transcript_path // empty' 2>/dev/null || echo "")
fi

# Get changed files
changed_files=$("${SCRIPT_DIR}/get_changed_files.sh" 2>/dev/null || echo "")

# If no files changed, nothing to evaluate
if [ -z "${changed_files}" ]; then
    # Reset baseline for next iteration
    "${SCRIPT_DIR}/capture_work_tree.sh" 2>/dev/null || true
    exit 0
fi

# Extract conversation text from the JSONL transcript
# The transcript is JSONL format - each line is a JSON object
# We need to extract the text content from assistant messages
conversation_context=""
if [ -n "${TRANSCRIPT_PATH}" ] && [ -f "${TRANSCRIPT_PATH}" ]; then
    # Extract text content from all assistant messages in the transcript
    # Each line is a JSON object; we extract .message.content[].text for assistant messages
    conversation_context=$(cat "${TRANSCRIPT_PATH}" | \
        grep -E '"role"\s*:\s*"assistant"' | \
        jq -r '.message.content // [] | map(select(.type == "text")) | map(.text) | join("\n")' 2>/dev/null | \
        tr -d '\0' || echo "")
fi

# Call the Python evaluator
# The Python module handles:
# - Parsing the policy file
# - Matching changed files against triggers/safety patterns
# - Checking for promise tags in the conversation context
# - Generating appropriate JSON output
result=$(echo "${conversation_context}" | python -m deepwork.hooks.evaluate_policies \
    --policy-file .deepwork.policy.yml \
    --changed-files "${changed_files}" \
    2>/dev/null || echo '{}')

# Reset the work tree baseline for the next iteration
"${SCRIPT_DIR}/capture_work_tree.sh" 2>/dev/null || true

# Output the result (JSON for Claude Code hooks)
echo "${result}"
