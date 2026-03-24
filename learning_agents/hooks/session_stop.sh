#!/usr/bin/env bash
# session_stop.sh - Stop hook for session end
#
# Two responsibilities:
# 1. If this session IS a top-level LearningAgent (started with --agent),
#    create session tracking files so /learn can process the transcript.
# 2. Check if any LearningAgents (subagent or top-level) have unprocessed
#    transcripts and suggest running a learning cycle.
#
# Input (stdin): JSON with session info (session_id, transcript_path, agent_type)
# Output (stdout): JSON with optional systemMessage
# Exit: Always 0 (non-blocking)

set -euo pipefail

# ============================================================================
# READ STDIN
# ============================================================================

HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# ============================================================================
# TRACK TOP-LEVEL LEARNING AGENT SESSION
# ============================================================================
# When Claude Code is started with --agent, the hook input includes agent_type.
# If agent_type corresponds to a LearningAgent, create session tracking files
# so /learn can find and process this session's transcript.

if [ -n "$HOOK_INPUT" ]; then
    AGENT_TYPE_RAW=$(echo "$HOOK_INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
    SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
    TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

    if [ -n "$AGENT_TYPE_RAW" ] && [ -n "$SESSION_ID" ]; then
        # Normalize agent name: lowercase, spaces to hyphens
        AGENT_NAME=$(echo "$AGENT_TYPE_RAW" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
        AGENT_DIR=".deepwork/learning-agents/${AGENT_NAME}"

        if [ -d "$AGENT_DIR" ]; then
            SESSION_LOG_DIR=".deepwork/tmp/agent_sessions/${SESSION_ID}/top-level"
            mkdir -p "$SESSION_LOG_DIR"

            # Write timestamp flag
            date -u +"%Y-%m-%dT%H:%M:%SZ" > "${SESSION_LOG_DIR}/needs_learning_as_of_timestamp"

            # Write agent name for later lookup
            echo "$AGENT_NAME" > "${SESSION_LOG_DIR}/agent_used"

            # Symlink transcript — for top-level sessions, transcript_path
            # points directly to the session transcript (not a subagent path)
            if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
                ln -sf "$TRANSCRIPT_PATH" "${SESSION_LOG_DIR}/conversation_transcript.jsonl"
            fi
        fi
    fi
fi

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
