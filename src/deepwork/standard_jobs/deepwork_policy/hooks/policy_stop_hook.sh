#!/bin/bash
# policy_stop_hook.sh - Evaluates policies when the agent stops
#
# This script is called as a Claude Code Stop hook. It:
# 1. Evaluates policies from .deepwork/policies/ (v2) or .deepwork.policy.yml (v1)
# 2. Computes changed files based on each policy's compare_to setting
# 3. Checks for <promise> tags in the conversation transcript
# 4. Returns JSON to block stop if policies need attention

set -e

# Determine which policy system to use
USE_V2=false
V1_POLICY_FILE=".deepwork.policy.yml"
V2_POLICY_DIR=".deepwork/policies"

if [ -d "${V2_POLICY_DIR}" ]; then
    # Check if there are any .md files in the v2 directory
    if ls "${V2_POLICY_DIR}"/*.md 1>/dev/null 2>&1; then
        USE_V2=true
    fi
fi

# If no v2 policies and no v1 policy file, nothing to do
if [ "${USE_V2}" = false ] && [ ! -f "${V1_POLICY_FILE}" ]; then
    exit 0
fi

# Read the hook input JSON from stdin
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

if [ "${USE_V2}" = true ]; then
    # Use v2 policy system via cross-platform wrapper
    # The wrapper reads JSON input and handles transcript extraction
    result=$(echo "${HOOK_INPUT}" | DEEPWORK_HOOK_PLATFORM=claude DEEPWORK_HOOK_EVENT=Stop python -m deepwork.hooks.policy_check 2>/dev/null || echo '{}')
else
    # Use v1 policy system - extract conversation context for evaluate_policies

    # Extract transcript_path from the hook input JSON using jq
    # Claude Code passes: {"session_id": "...", "transcript_path": "...", ...}
    TRANSCRIPT_PATH=""
    if [ -n "${HOOK_INPUT}" ]; then
        TRANSCRIPT_PATH=$(echo "${HOOK_INPUT}" | jq -r '.transcript_path // empty' 2>/dev/null || echo "")
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

    # Call the Python v1 evaluator
    result=$(echo "${conversation_context}" | python -m deepwork.hooks.evaluate_policies \
        --policy-file "${V1_POLICY_FILE}" \
        2>/dev/null || echo '{}')
fi

# Output the result (JSON for Claude Code hooks)
echo "${result}"
