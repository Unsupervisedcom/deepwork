#!/bin/bash
# generate_agent_instructions_for_session.sh - Generate agent instructions from a session folder
#
# Usage: generate_agent_instructions_for_session.sh <session_log_folder>
#
# Reads agent_used from the session folder and passes it to generate_agent_instructions.sh

set -euo pipefail

SESSION_FOLDER="${1:-}"

if [ -z "$SESSION_FOLDER" ]; then
    echo "Usage: generate_agent_instructions_for_session.sh <session_log_folder>" >&2
    exit 1
fi

AGENT=$(cat "$SESSION_FOLDER/agent_used" 2>/dev/null || echo "")
if [ -z "$AGENT" ]; then
    echo "Error: Could not read agent_used from $SESSION_FOLDER" >&2
    exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
exec "$SCRIPT_DIR/generate_agent_instructions.sh" "$AGENT"
