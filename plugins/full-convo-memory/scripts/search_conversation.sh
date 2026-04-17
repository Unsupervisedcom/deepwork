#!/usr/bin/env bash
# search_conversation.sh — search the current Claude Code session's jsonl
# transcript using jq. Compaction-summary messages are dropped automatically;
# everything else is passed through to jq verbatim.
#
# Usage:
#   search_conversation.sh [--log-file <path>] <jq-args...>
#
# Log-file resolution (first match wins):
#   1. --log-file <path>                             (explicit override)
#   2. sub-agent     : ~/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID/subagents/agent-$CLAUDE_CODE_AGENT_ID.jsonl
#   3. top-level     : ~/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID.jsonl
#   4. fallback      : most-recently-modified *.jsonl directly in ~/.claude/projects/<encoded-cwd>/
#
# <encoded-cwd> is $PWD with every '/' replaced by '-' (leading '-' preserved).

set -u -o pipefail

usage() {
    cat >&2 <<'EOF'
Usage: search_conversation.sh [--log-file <path>] <jq-args...>

Pre-filters the current Claude Code session's jsonl transcript to drop
compaction-summary entries, then runs `jq <jq-args...>` on the result.

Examples:
  search_conversation.sh 'select(.type == "user")'
  search_conversation.sh -r 'select((.message.content | tostring) | test("plan mode"; "i")) | .timestamp'
  search_conversation.sh --log-file /tmp/session.jsonl 'select(.type == "assistant")'

Any flags and filters accepted by jq are passed through verbatim.
EOF
}

# --- parse optional --log-file override ------------------------------------
LOG_FILE=""
if [ "${1:-}" = "--log-file" ]; then
    if [ $# -lt 2 ]; then
        echo "error: --log-file requires a path argument" >&2
        exit 2
    fi
    LOG_FILE="$2"
    shift 2
fi

# --- require at least one jq arg (guard against dumping the whole file) ----
if [ $# -eq 0 ]; then
    usage
    exit 2
fi

# --- require jq ------------------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    echo "error: jq is required but not found on PATH" >&2
    exit 127
fi

# --- resolve the log file --------------------------------------------------
encode_cwd() {
    printf '%s' "$1" | sed 's|/|-|g'
}

if [ -z "$LOG_FILE" ]; then
    ENCODED_CWD=$(encode_cwd "$PWD")
    PROJECT_DIR="$HOME/.claude/projects/$ENCODED_CWD"

    if [ -n "${CLAUDE_CODE_AGENT_ID:-}" ] && [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
        CANDIDATE="$PROJECT_DIR/$CLAUDE_CODE_SESSION_ID/subagents/agent-$CLAUDE_CODE_AGENT_ID.jsonl"
        [ -f "$CANDIDATE" ] && LOG_FILE="$CANDIDATE"
    fi

    if [ -z "$LOG_FILE" ] && [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
        CANDIDATE="$PROJECT_DIR/$CLAUDE_CODE_SESSION_ID.jsonl"
        [ -f "$CANDIDATE" ] && LOG_FILE="$CANDIDATE"
    fi

    if [ -z "$LOG_FILE" ] && [ -d "$PROJECT_DIR" ]; then
        # Most-recently-modified top-level *.jsonl in the project dir (no recursion).
        CANDIDATE=$(find "$PROJECT_DIR" -maxdepth 1 -type f -name '*.jsonl' -print0 2>/dev/null \
            | xargs -0 ls -t 2>/dev/null \
            | head -n 1)
        [ -n "$CANDIDATE" ] && [ -f "$CANDIDATE" ] && LOG_FILE="$CANDIDATE"
    fi
fi

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
    cat >&2 <<EOF
error: could not resolve session transcript file.
  checked --log-file       : ${LOG_FILE:-<none>}
  CLAUDE_CODE_SESSION_ID   : ${CLAUDE_CODE_SESSION_ID:-<unset>}
  CLAUDE_CODE_AGENT_ID     : ${CLAUDE_CODE_AGENT_ID:-<unset>}
  project dir              : $HOME/.claude/projects/$(encode_cwd "$PWD")

Pass --log-file <path> to override.
EOF
    exit 1
fi

# --- run the pipeline ------------------------------------------------------
# Drop compaction-summary messages first, then apply the caller's jq args.
# We ignore the exit code of the pre-filter's jq so a single malformed line
# doesn't suppress all output; the user's jq exit code is what matters.
jq -c 'select(.isCompactSummary != true)' "$LOG_FILE" | jq "$@"
USER_JQ_EXIT=$?

# Trailing pointer line — always printed so the caller sees the exact path.
printf '\nIf you want a more semantic search of the history, start an Explore agent and tell it what to look for in %s\n' "$LOG_FILE"

exit "$USER_JQ_EXIT"
