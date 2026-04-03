#!/usr/bin/env bash
# startup_context.sh - Inject Claude Code session and agent IDs into context
#
# Runs on SessionStart and SubagentStart to provide agents with their
# CLAUDE_CODE_SESSION_ID (and CLAUDE_CODE_AGENT_ID for sub-agents).
# These IDs are used by MCP tools to locate persistent workflow state.
#
# Input (stdin):  JSON from Claude Code hook (contains .session_id, optionally .agent_id)
# Output (stdout): JSON with hookSpecificOutput.additionalContext, or empty {}
# Exit codes:
#   0 - Always (failures produce empty {} response)

set -euo pipefail
trap 'echo "{}"; exit 0' ERR

# ==== Parse input ====
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

if [ -z "$SESSION_ID" ]; then
  echo '{}'
  exit 0
fi

EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name // "SessionStart"')
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')

# ==== Build context string ====
CTX="CLAUDE_CODE_SESSION_ID=$SESSION_ID"
if [ -n "$AGENT_ID" ]; then
  CTX="${CTX}"$'\n'"CLAUDE_CODE_AGENT_ID=$AGENT_ID"
fi

# Inject DeepPlan trigger for planning mode
DEEPPLAN_MSG="When you enter plan mode and begin working on a plan, start the DeepWork workflow create_deep_plan (job: deepplan) via start_workflow before doing anything else. The workflow will guide you through structured planning. Its instructions supersede the default planning phases."
CTX="${CTX}"$'\n'"${DEEPPLAN_MSG}"

# ==== Output hook response ====
jq -n --arg ctx "$CTX" --arg event "$EVENT_NAME" \
  '{ hookSpecificOutput: { hookEventName: $event, additionalContext: $ctx } }'
