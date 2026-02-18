#!/bin/bash
# session_stop.sh - Stop hook for session end
#
# Checks if any LearningAgents were used during the session and suggests
# running a learning cycle if there are unprocessed transcripts.
#
# Input (stdin): JSON with session info
# Output (stdout): JSON with optional systemMessage
# Exit: Always 0 (non-blocking)

set -euo pipefail

# ============================================================================
# CHECK FOR PENDING LEARNING
# ============================================================================

if [ ! -d ".deepwork/tmp/agent_sessions" ]; then
    echo '{}'
    exit 0
fi

PENDING_FILES=$(find .deepwork/tmp/agent_sessions -name "needs_learning_as_of_timestamp")

if [ -z "$PENDING_FILES" ]; then
    echo '{}'
    exit 0
fi

# Count unique agents with pending learning
AGENT_COUNT=0
AGENT_NAMES=""
for f in $PENDING_FILES; do
    DIR=$(dirname "$f")
    if [ -f "${DIR}/agent_used" ]; then
        AGENT_NAME=$(cat "${DIR}/agent_used")
        AGENT_NAMES="${AGENT_NAMES} ${AGENT_NAME}"
        AGENT_COUNT=$((AGENT_COUNT + 1))
    fi
done

# Deduplicate agent names
UNIQUE_AGENTS=$(echo "$AGENT_NAMES" | tr ' ' '\n' | sort -u | tr '\n' ' ' | xargs)

if [ "$AGENT_COUNT" -eq 0 ]; then
    echo '{}'
    exit 0
fi

# ============================================================================
# OUTPUT LEARNING SUGGESTION
# ============================================================================

MESSAGE="LearningAgents used this session (${UNIQUE_AGENTS}) have unprocessed transcripts. Consider running '/learning-agents learn' to identify and incorporate learnings."
ESCAPED_MESSAGE=$(echo "$MESSAGE" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ')

cat << EOF
{"systemMessage":"${ESCAPED_MESSAGE}"}
EOF

exit 0
