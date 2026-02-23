#!/bin/bash
# Post-commit reminder hook
# Triggers after Bash tool uses that contain "git commit" to remind
# the agent to run the review skill.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -q 'git commit'; then
  cat << 'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"You **MUST** use AskUserQuestion tool to offer to the user to run the `review` skill to review the changes you just committed if you have not run a review recently."}}
EOF
fi
