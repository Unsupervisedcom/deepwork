#!/bin/bash
# post_compact.sh - Post-compaction context restoration hook
#
# Restores DeepWork workflow context after Claude Code compacts its context.
# Registered as a SessionStart hook with matcher "compact" in hooks.json.
#
# Input (stdin):  JSON from Claude Code SessionStart hook (contains .cwd)
# Output (stdout): JSON with hookSpecificOutput.additionalContext, or empty {}
# Exit codes:
#   0 - Always (failures produce empty {} response)

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

if [ -z "$CWD" ]; then
  echo '{}'
  exit 0
fi

# Get active workflow sessions
STACK_JSON=$(deepwork jobs get-stack --path "$CWD" 2>/dev/null) || {
  echo '{}'
  exit 0
}

# Check if there are active sessions
SESSION_COUNT=$(echo "$STACK_JSON" | jq '.active_sessions | length // 0')
if [ "$SESSION_COUNT" -eq 0 ]; then
  echo '{}'
  exit 0
fi

# Build markdown context from active sessions
CONTEXT="# DeepWork Workflow Context (Restored After Compaction)

You are in the middle of a DeepWork workflow. Use the DeepWork MCP tools to continue.
Call \`finished_step\` with your outputs when you complete the current step.
"

for i in $(seq 0 $((SESSION_COUNT - 1))); do
  # Extract all fields in a single jq call, null-delimited
  eval "$(echo "$STACK_JSON" | jq -r --argjson i "$i" '
    .active_sessions[$i] |
    @sh "SESSION_ID=\(.session_id)",
    @sh "JOB_NAME=\(.job_name)",
    @sh "WORKFLOW_NAME=\(.workflow_name)",
    @sh "GOAL=\(.goal)",
    @sh "CURRENT_STEP=\(.current_step_id)",
    @sh "INSTANCE_ID=\(.instance_id // "")",
    @sh "STEP_NUM=\(.step_number // "")",
    @sh "TOTAL_STEPS=\(.total_steps // "")",
    @sh "COMPLETED=\(.completed_steps | join(", "))",
    @sh "COMMON_INFO=\(.common_job_info // "")",
    @sh "STEP_INSTRUCTIONS=\(.current_step_instructions // "")"
  ')"

  STEP_LABEL="$CURRENT_STEP"
  if [ -n "$STEP_NUM" ] && [ -n "$TOTAL_STEPS" ]; then
    STEP_LABEL="$CURRENT_STEP (step $STEP_NUM of $TOTAL_STEPS)"
  fi

  CONTEXT="$CONTEXT
## Active Session: $SESSION_ID
- **Workflow**: ${JOB_NAME}/${WORKFLOW_NAME}
- **Goal**: $GOAL
- **Current Step**: $STEP_LABEL"

  if [ -n "$INSTANCE_ID" ]; then
    CONTEXT="$CONTEXT
- **Instance**: $INSTANCE_ID"
  fi

  if [ -n "$COMPLETED" ]; then
    CONTEXT="$CONTEXT
- **Completed Steps**: $COMPLETED"
  fi

  if [ -n "$COMMON_INFO" ]; then
    CONTEXT="$CONTEXT

### Common Job Info
$COMMON_INFO"
  fi

  if [ -n "$STEP_INSTRUCTIONS" ]; then
    CONTEXT="$CONTEXT

### Current Step Instructions
$STEP_INSTRUCTIONS"
  fi

  CONTEXT="$CONTEXT
"
done

# Output hook response with additionalContext
# Use jq to properly escape the markdown for JSON
echo "$CONTEXT" | jq -Rs '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: .}}'
