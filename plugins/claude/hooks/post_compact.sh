#!/bin/bash
# Post-compaction context restoration hook
# Fires on SessionStart with matcher "compact" to inject active
# DeepWork workflow context after Claude Code compacts its context.

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
SESSION_COUNT=$(echo "$STACK_JSON" | jq '.active_sessions | length')
if [ "$SESSION_COUNT" -eq 0 ] 2>/dev/null; then
  echo '{}'
  exit 0
fi

# Build markdown context from active sessions
CONTEXT="# DeepWork Workflow Context (Restored After Compaction)

You are in the middle of a DeepWork workflow. Use the DeepWork MCP tools to continue.
Call \`finished_step\` with your outputs when you complete the current step.
"

for i in $(seq 0 $((SESSION_COUNT - 1))); do
  SESSION_ID=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].session_id")
  JOB_NAME=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].job_name")
  WORKFLOW_NAME=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].workflow_name")
  GOAL=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].goal")
  CURRENT_STEP=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].current_step_id")
  INSTANCE_ID=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].instance_id // empty")
  STEP_NUM=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].step_number // empty")
  TOTAL_STEPS=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].total_steps // empty")
  COMPLETED=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].completed_steps | join(\", \")")
  COMMON_INFO=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].common_job_info // empty")
  STEP_INSTRUCTIONS=$(echo "$STACK_JSON" | jq -r ".active_sessions[$i].current_step_instructions // empty")

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
