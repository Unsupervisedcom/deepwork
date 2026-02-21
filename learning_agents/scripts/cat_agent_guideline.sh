#!/bin/bash
# cat_agent_guideline.sh - Print an agent's additional learning guideline file
#
# Usage: cat_agent_guideline.sh <session_log_folder> <guideline_name>
#
# Reads agent_used from the session folder, then cats the corresponding
# guideline file from .deepwork/learning-agents/<agent>/additional_learning_guidelines/<guideline>.md
#
# Example:
#   cat_agent_guideline.sh .deepwork/tmp/agent_sessions/sess-1/agent-1/ issue_identification

set -euo pipefail

SESSION_FOLDER="${1:-}"
GUIDELINE="${2:-}"

if [ -z "$SESSION_FOLDER" ] || [ -z "$GUIDELINE" ]; then
    echo "Usage: cat_agent_guideline.sh <session_log_folder> <guideline_name>" >&2
    exit 1
fi

AGENT=$(cat "$SESSION_FOLDER/agent_used" 2>/dev/null || echo "")
if [ -z "$AGENT" ]; then
    exit 0
fi

FILE=".deepwork/learning-agents/${AGENT}/additional_learning_guidelines/${GUIDELINE}.md"
if [ -f "$FILE" ]; then
    cat "$FILE"
fi
