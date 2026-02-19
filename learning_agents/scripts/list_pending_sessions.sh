#!/bin/bash
# list_pending_sessions.sh - List session log folders that need learning, grouped by agent
#
# Usage: list_pending_sessions.sh
#
# Finds all session folders containing a needs_learning_as_of_timestamp file,
# groups them by agent name, and outputs a structured list.
#
# Output format:
#   ### "<agent-name>" agent sessions
#   - <session_log_folder_path>
#   - <session_log_folder_path>
#   (blank line between agents)

set -euo pipefail

BASE=".deepwork/tmp/agent_sessions"

if [ ! -d "$BASE" ]; then
    exit 0
fi

# Collect agent:path pairs, sorted by agent name
pairs=()
while read -r f; do
    dir=$(dirname "$f")
    agent=$(cat "$dir/agent_used" 2>/dev/null || echo "unknown")
    pairs+=("$agent|$dir")
done < <(find "$BASE" -name needs_learning_as_of_timestamp 2>/dev/null)

if [ ${#pairs[@]} -eq 0 ]; then
    exit 0
fi

# Sort by agent name
IFS=$'\n' sorted=($(printf '%s\n' "${pairs[@]}" | sort)); unset IFS

# Group and print
current_agent=""
count=0
paths=()

flush_group() {
    if [ -n "$current_agent" ] && [ ${#paths[@]} -gt 0 ]; then
        echo "### \"$current_agent\" agent sessions"
        for p in "${paths[@]}"; do
            echo "- $p"
        done
        echo ""
    fi
}

for pair in "${sorted[@]}"; do
    agent="${pair%%|*}"
    path="${pair#*|}"

    if [ "$agent" != "$current_agent" ]; then
        flush_group
        current_agent="$agent"
        paths=()
    fi
    paths+=("$path")
done
flush_group
