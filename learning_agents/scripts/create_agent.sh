#!/bin/bash
# create_agent.sh - Create a new LearningAgent scaffold
#
# Usage: create_agent.sh <agent-name>
#
# Creates:
#   .deepwork/learning-agents/<agent-name>/core-knowledge.md
#   .deepwork/learning-agents/<agent-name>/topics/.gitkeep
#   .deepwork/learning-agents/<agent-name>/learnings/.gitkeep
#   .deepwork/learning-agents/<agent-name>/additional_learning_guidelines/
#   .claude/agents/<agent-name>.md

set -euo pipefail

AGENT_NAME="${1:-}"

if [ -z "$AGENT_NAME" ]; then
    echo "Usage: create_agent.sh <agent-name>" >&2
    exit 1
fi

AGENT_DIR=".deepwork/learning-agents/${AGENT_NAME}"
CLAUDE_AGENT_FILE=".claude/agents/${AGENT_NAME}.md"

# ============================================================================
# CREATE LEARNING AGENT DIRECTORY
# ============================================================================

if [ -d "$AGENT_DIR" ]; then
    echo "Agent directory already exists: ${AGENT_DIR}" >&2
else
    mkdir -p "${AGENT_DIR}/topics" "${AGENT_DIR}/learnings" "${AGENT_DIR}/additional_learning_guidelines"

    # Create .gitkeep files for empty directories
    touch "${AGENT_DIR}/topics/.gitkeep"
    touch "${AGENT_DIR}/learnings/.gitkeep"

    # Create empty additional learning guideline files
    touch "${AGENT_DIR}/additional_learning_guidelines/issue_identification.md"
    touch "${AGENT_DIR}/additional_learning_guidelines/issue_investigation.md"
    touch "${AGENT_DIR}/additional_learning_guidelines/learning_from_issues.md"

    # Create README for additional learning guidelines
    cat > "${AGENT_DIR}/additional_learning_guidelines/README.md" << 'ALG_README'
# Additional Learning Guidelines

These files let you customize how the learning cycle works for this agent. Each file is automatically included in the corresponding learning skill. Leave empty to use default behavior, or add markdown instructions to guide the process.

## Files

- **issue_identification.md** — Included during the `identify` step. Use this to tell the reviewer what kinds of issues matter most for this agent, what to ignore, or domain-specific signals of mistakes.

- **issue_investigation.md** — Included during the `investigate-issues` step. Use this to guide root cause analysis — e.g., common root causes in this domain, which parts of the agent's knowledge to check first, or investigation heuristics.

- **learning_from_issues.md** — Included during the `incorporate-learnings` step. Use this to guide how learnings are integrated — e.g., preferences for topics vs learnings, naming conventions, or areas of core-knowledge that should stay concise.
ALG_README

    # Create core-knowledge.md with TODO placeholder
    cat > "${AGENT_DIR}/core-knowledge.md" << 'CORE_KNOWLEDGE'
TODO: Complete current knowledge of this domain.
Written in second person ("You should...") because this text
becomes the agent's system instructions. Structure it as:
1. Identity statement ("You are an expert on...")
2. Core concepts and terminology
3. Common patterns and best practices
4. Pitfalls to avoid
5. Decision frameworks
CORE_KNOWLEDGE

    echo "Created agent directory: ${AGENT_DIR}"
fi

# ============================================================================
# CREATE CLAUDE CODE AGENT FILE
# ============================================================================

if [ -f "$CLAUDE_AGENT_FILE" ]; then
    echo "Claude agent file already exists: ${CLAUDE_AGENT_FILE}" >&2
else
    mkdir -p "$(dirname "$CLAUDE_AGENT_FILE")"

    # Use quoted heredoc to keep backticks/dollars literal, then sed in agent name
    cat > "$CLAUDE_AGENT_FILE" << 'AGENT_MD'
---
name: TODO
description: "TODO"
---

# Core Knowledge

!`cat .deepwork/learning-agents/__AGENT__/core-knowledge.md`

# Topics

Located in `.deepwork/learning-agents/__AGENT__/topics/`

!`for f in .deepwork/learning-agents/__AGENT__/topics/*.md; do [ -f "$f" ] || continue; desc=$(awk '/^---/{c++; next} c==1 && /^name:/{sub(/^name: *"?/,""); sub(/"$/,""); print; exit}' "$f"); echo "- $(basename "$f"): $desc"; done`

# Learnings

Learnings are incident post-mortems from past agent sessions capturing mistakes, root causes, and generalizable insights. Review them before starting work to avoid repeating past mistakes. Located in `.deepwork/learning-agents/__AGENT__/learnings/`.
AGENT_MD

    # Replace placeholder with actual agent name (use .bak for GNU/BSD sed portability)
    sed -i.bak "s/__AGENT__/${AGENT_NAME}/g" "$CLAUDE_AGENT_FILE"
    rm -f "${CLAUDE_AGENT_FILE}.bak"

    echo "Created Claude agent file: ${CLAUDE_AGENT_FILE}"
fi

echo "Agent scaffold created for: ${AGENT_NAME}"
