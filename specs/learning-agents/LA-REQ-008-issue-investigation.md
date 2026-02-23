# LA-REQ-008: Issue Investigation

## Overview

The `investigate-issues` skill researches identified issues in a LearningAgent session by reading the transcript, determining root causes, and updating issue files with investigation reports.

## Requirements

### LA-REQ-008.1: Skill Visibility

The `investigate-issues` skill MUST NOT be directly invocable by the user (`user-invocable: false`). It MUST only be invoked programmatically by the `learn` skill via a Task.

### LA-REQ-008.2: Input Argument

The skill MUST accept a single argument: the path to the session log folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

### LA-REQ-008.3: Agent Context Loading

The skill MUST dynamically load:
- The agent name from `$ARGUMENTS/agent_used`
- The agent's core knowledge from `.deepwork/learning-agents/<agent-name>/core-knowledge.md`
- Additional investigation guidelines from `.deepwork/learning-agents/<agent-name>/additional_learning_guidelines/issue_investigation.md`

### LA-REQ-008.4: Issue Discovery

The skill MUST find all issue files with `status: identified` in the session folder by searching for `*.issue.yml` files containing `status: identified`.

### LA-REQ-008.5: No Identified Issues

If no issue files with status `identified` are found, the skill MUST report that finding and stop.

### LA-REQ-008.6: Transcript Location

The skill MUST locate the session transcript using the same mechanism as the identify skill (extract session_id from the path, glob for `~/.claude/projects/**/sessions/<session_id>/*.jsonl`).

### LA-REQ-008.7: Missing Transcript

If no transcript file is found, the skill MUST report the missing path and stop. It MUST NOT proceed to investigate without transcript evidence.

### LA-REQ-008.8: Investigation Process

For each identified issue, the skill MUST:
1. Read the issue file to understand the reported problem
2. Search the transcript for relevant sections using keywords from `issue_description` or timestamps from `seen_at_timestamps`
3. Determine the root cause
4. Write an investigation report

### LA-REQ-008.9: Root Cause Taxonomy

The skill MUST classify root causes using this taxonomy:
- **Knowledge gap**: Missing or incomplete content in `core-knowledge.md`
- **Missing documentation**: A topic file does not exist or lacks needed detail
- **Incorrect instruction**: An existing instruction leads the agent to wrong behavior
- **Missing runtime context**: Information that should have been injected at runtime was absent

### LA-REQ-008.10: Investigation Report Requirements

The investigation report MUST include:
- Specific evidence from the transcript with line number references
- Root cause analysis explaining why the agent behaved incorrectly
- Identification of the knowledge gap or instruction deficiency that caused the issue

### LA-REQ-008.11: Status Update

For each investigated issue, the skill MUST update the issue file to change `status: identified` to `status: investigated`.

### LA-REQ-008.12: Investigation Report Field Addition

For each investigated issue, the skill MUST add an `investigation_report` field to the issue file containing the root cause analysis.

### LA-REQ-008.13: Issue Description Preservation

The skill MUST NOT modify the `issue_description` field. Only the `investigation_report` field MUST be added and the `status` field updated.

### LA-REQ-008.14: Complete Processing

The skill MUST NOT skip any identified issues. Every issue file with `status: identified` in the folder MUST be investigated.

### LA-REQ-008.15: No Knowledge Base Modification

The skill MUST NOT modify the agent's knowledge base. Knowledge base updates are the responsibility of the `incorporate-learnings` skill.

### LA-REQ-008.16: Summary Output

For each investigated issue, the skill MUST output:
- The issue filename
- A one-sentence root cause summary
- The recommended update type (expertise update, new topic, new learning, or instruction fix)

### LA-REQ-008.17: Allowed Tools

The skill MUST only use the following tools: Read, Grep, Glob, Edit.
