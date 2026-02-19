#!/bin/bash
# generate_agent_instructions.sh - Generate dynamic agent instructions for a LearningAgent
#
# Usage: generate_agent_instructions.sh <agent-name>
#
# Accepts either directory-style name (e.g., "consistency-reviewer")
# or title-case name (e.g., "Consistency Reviewer") and outputs the
# full markdown body for the agent's Claude Code agent file.
#
# Looks for the agent directory in .deepwork/learning-agents/<agent-name>/

set -euo pipefail

AGENT_INPUT="${1:-}"

if [ -z "$AGENT_INPUT" ]; then
    echo "Usage: generate_agent_instructions.sh <agent-name>" >&2
    exit 1
fi

# Normalize: convert title case to directory-style (lowercase, spaces to hyphens)
AGENT_NAME=$(echo "$AGENT_INPUT" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

AGENT_DIR=".deepwork/learning-agents/${AGENT_NAME}"

if [ ! -d "$AGENT_DIR" ]; then
    echo "Error: Agent directory not found: ${AGENT_DIR}" >&2
    exit 1
fi

# --- Core Knowledge ---
echo "# Core Knowledge"
echo ""
if [ -f "${AGENT_DIR}/core-knowledge.md" ]; then
    cat "${AGENT_DIR}/core-knowledge.md"
else
    echo "_No core knowledge file found._"
fi
echo ""

# --- Topics ---
echo "# Topics"
echo ""
echo "Located in \`${AGENT_DIR}/topics/\`"
echo ""
for f in "${AGENT_DIR}/topics/"*.md; do
    [ -f "$f" ] || continue
    desc=$(awk '/^---/{c++; next} c==1 && /^name:/{sub(/^name: *"?/,""); sub(/"$/,""); print; exit}' "$f")
    echo "- $(basename "$f"): $desc"
done
echo ""

# --- Learnings ---
echo "# Learnings"
echo ""
echo "Learnings are incident post-mortems from past agent sessions capturing mistakes, root causes, and generalizable insights. Review them before starting work to avoid repeating past mistakes. Located in \`${AGENT_DIR}/learnings/\`."
