#!/bin/bash
# Post-commit reminder hook
# Triggers after Bash tool uses that contain "git commit" to remind
# the agent to run the review skill.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -q 'git commit'; then
  cat << 'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Remember to run the `review` skill (`/review`) to review the changes you just committed."}}
EOF
fi
