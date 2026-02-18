#!/bin/bash
# post_task.sh - PostToolUse hook for Task tool
#
# Detects when a LearningAgent is used via Task and creates session tracking
# files so the learning cycle can process the transcript later.
#
# Input (stdin): JSON with tool_input, tool_response, session_id
# Output (stdout): JSON with optional hookSpecificOutput.additionalContext
# Exit: Always 0 (non-blocking)

set -euo pipefail

# ============================================================================
# READ STDIN
# ============================================================================

HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

if [ -z "$HOOK_INPUT" ]; then
    echo '{}'
    exit 0
fi

# ============================================================================
# EXTRACT FIELDS
# ============================================================================

# Extract session_id
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
if [ -z "$SESSION_ID" ]; then
    echo '{}'
    exit 0
fi

# Extract agent name from tool_input.name (the name parameter passed to Task)
# Normalize: lowercase and replace spaces with hyphens to match directory naming
# (e.g., "Consistency Reviewer" -> "consistency-reviewer")
AGENT_NAME_RAW=$(echo "$HOOK_INPUT" | jq -r '.tool_input.name // empty' 2>/dev/null)
if [ -z "$AGENT_NAME_RAW" ]; then
    echo '{}'
    exit 0
fi
AGENT_NAME=$(echo "$AGENT_NAME_RAW" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# Extract agent_id from tool_response
AGENT_ID=$(echo "$HOOK_INPUT" | jq -r '.tool_response.agentId // .tool_response.agent_id // empty' 2>/dev/null)
if [ -z "$AGENT_ID" ]; then
    echo '{}'
    exit 0
fi

# ============================================================================
# CHECK IF THIS IS A LEARNING AGENT
# ============================================================================

AGENT_DIR=".deepwork/learning-agents/${AGENT_NAME}"
if [ ! -d "$AGENT_DIR" ]; then
    echo '{}'
    exit 0
fi

# ============================================================================
# CREATE SESSION TRACKING FILES
# ============================================================================

SESSION_DIR=".deepwork/tmp/agent_sessions/${SESSION_ID}/${AGENT_ID}"
mkdir -p "$SESSION_DIR"

# Write timestamp flag
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${SESSION_DIR}/needs_learning_as_of_timestamp"

# Write agent name for later lookup
echo "$AGENT_NAME" > "${SESSION_DIR}/agent_used"

# ============================================================================
# OUTPUT POST-TASK REMINDER
# ============================================================================

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REMINDER=""
if [ -f "${PLUGIN_ROOT}/doc/learning_agent_post_task_reminder.md" ]; then
    REMINDER=$(cat "${PLUGIN_ROOT}/doc/learning_agent_post_task_reminder.md" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ')
fi

if [ -n "$REMINDER" ]; then
    cat << EOF
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"${REMINDER}"}}
EOF
else
    echo '{}'
fi

exit 0
