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
trap 'echo "{}"; exit 0' ERR

# ==== Parse input ====
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

if [ -z "$CWD" ]; then
  echo '{}'
  exit 0
fi

# ==== Fetch active sessions ====
STACK_JSON=$(deepwork jobs get-stack --path "$CWD" 2>/dev/null) || {
  echo '{}'
  exit 0
}

# ==== Check for active sessions ====
SESSION_COUNT=$(echo "$STACK_JSON" | jq '(.active_sessions // []) | length')
if [ "$SESSION_COUNT" -eq 0 ]; then
  echo '{}'
  exit 0
fi

# ==== Build markdown context from active sessions ====
CONTEXT="# DeepWork Workflow Context (Restored After Compaction)

You are in the middle of a DeepWork workflow. Use the DeepWork MCP tools to continue.
Call \`finished_step\` with your outputs when you complete the current step.
"

for ((i = 0; i < SESSION_COUNT; i++)); do
  # Extract all fields in a single jq call, null-delimited (no eval)
  {
    IFS= read -r -d '' SESSION_ID
    IFS= read -r -d '' JOB_NAME
    IFS= read -r -d '' WORKFLOW_NAME
    IFS= read -r -d '' GOAL
    IFS= read -r -d '' CURRENT_STEP
    IFS= read -r -d '' INSTANCE_ID
    IFS= read -r -d '' STEP_NUM
    IFS= read -r -d '' TOTAL_STEPS
    IFS= read -r -d '' COMPLETED
    IFS= read -r -d '' COMMON_INFO
    IFS= read -r -d '' STEP_INSTRUCTIONS
  } < <(echo "$STACK_JSON" | jq -r -j --argjson i "$i" '
    .active_sessions[$i] |
    ((.session_id // ""), "\u0000",
     (.job_name // ""), "\u0000",
     (.workflow_name // ""), "\u0000",
     (.goal // ""), "\u0000",
     (.current_step_id // ""), "\u0000",
     (.instance_id // ""), "\u0000",
     (.step_number // ""), "\u0000",
     (.total_steps // ""), "\u0000",
     ((.completed_steps // []) | join(", ")), "\u0000",
     (.common_job_info // ""), "\u0000",
     (.current_step_instructions // ""), "\u0000")
  ')

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

# ==== Output hook response ====
echo "$CONTEXT" | jq -Rs '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: .}}'
