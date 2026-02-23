# LA-REQ-007: Issue Identification

## Overview

The `identify` skill reads a session transcript and surfaces actionable issues where a LearningAgent made mistakes, had knowledge gaps, or underperformed. It creates issue files for each problem found.

## Requirements

### LA-REQ-007.1: Skill Visibility

The `identify` skill MUST NOT be directly invocable by the user (`user-invocable: false`). It MUST only be invoked programmatically by the `learn` skill via a Task.

### LA-REQ-007.2: Input Argument

The skill MUST accept a single argument: the path to the session/agent_id folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

### LA-REQ-007.3: Agent Context Loading

The skill MUST dynamically load:
- The agent name from `$ARGUMENTS/agent_used`
- The last learning timestamp from `$ARGUMENTS/learning_last_performed_timestamp` (if it exists)
- Additional identification guidelines from `.deepwork/learning-agents/<agent-name>/additional_learning_guidelines/issue_identification.md`

### LA-REQ-007.4: Transcript Location

The skill MUST extract the `session_id` from the `$ARGUMENTS` path by taking the second-to-last path component. It MUST then use Glob to find the transcript file at `~/.claude/projects/**/sessions/<session_id>/*.jsonl`.

### LA-REQ-007.5: Missing Transcript

If no transcript file is found, the skill MUST report the error (including the session_id and Glob pattern used) and stop without creating any issue files.

### LA-REQ-007.6: Transcript Format

The skill MUST parse the transcript as JSONL (one JSON object per line). Each line has a `type` field. The skill MUST focus on `type: "assistant"` messages and `type: "tool_result"` entries to evaluate agent behavior.

### LA-REQ-007.7: Incremental Processing

If `learning_last_performed_timestamp` exists, the skill MUST skip transcript lines that occurred before that timestamp. Only interactions since the last learning cycle MUST be analyzed.

### LA-REQ-007.8: Agent Focus

The skill MUST focus on interactions involving the agent identified in the `agent_used` file. It SHOULD NOT analyze interactions with other agents.

### LA-REQ-007.9: Issue Categories

The skill MUST look for these categories of problems:
1. Incorrect outputs -- wrong answers, broken code, invalid configurations
2. Knowledge gaps -- the agent did not know something it should have
3. Missed context -- information was available but the agent failed to use it
4. Poor judgment -- questionable decisions or suboptimal approaches
5. Pattern failures -- repeated errors suggesting a systemic issue

### LA-REQ-007.10: Trivial Issue Filtering

The skill MUST skip trivial issues including:
- Minor formatting differences
- Environmental issues (network timeouts, tool failures)
- Issues already covered by existing learnings in the agent's knowledge base

### LA-REQ-007.11: Issue Reporting via Sub-Skill

For each issue identified, the skill MUST invoke the `report-issue` skill once per issue, passing the session folder path and a one-sentence description of the problem.

### LA-REQ-007.12: No Duplicate Issues

The skill MUST NOT create duplicate issue files for the same problem.

### LA-REQ-007.13: No Root Cause Investigation

The skill MUST NOT investigate root causes. Root cause analysis is the responsibility of the `investigate-issues` skill.

### LA-REQ-007.14: No Knowledge Base Modification

The skill MUST NOT modify the agent's knowledge base (core-knowledge.md, topics, or learnings).

### LA-REQ-007.15: Summary Output

The skill MUST output a summary containing:
- Session ID
- Agent name
- Count of issues found
- A table listing each issue with its category and a brief description
- Or a message indicating no actionable issues were found

### LA-REQ-007.16: Allowed Tools

The skill MUST only use the following tools: Read, Grep, Glob, Skill.
