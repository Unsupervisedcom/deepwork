# LA-REQ-004: Session Tracking and Hooks

## Overview

The learning-agents plugin uses hooks to automatically track when LearningAgents are invoked during Claude Code sessions. The PostToolUse hook on the Task tool creates session tracking files for subagent sessions. The Stop hook creates session tracking files for top-level agent sessions (started with `claude --agent <name>`) and checks for unprocessed sessions, suggesting running the learning cycle.

## Requirements

### LA-REQ-004.1: PostToolUse Hook Trigger

The PostToolUse hook MUST fire after every use of the `Task` tool. The hook matcher in `hooks.json` MUST be set to `"Task"`.

### LA-REQ-004.2: Post-Task Input Parsing

The `post_task.sh` hook MUST read JSON from stdin containing `session_id`, `tool_input`, and `tool_response` fields. If stdin is empty or not provided (terminal is interactive), the hook MUST output `{}` and exit 0.

### LA-REQ-004.3: Session ID Extraction

The hook MUST extract `session_id` from the hook input JSON via `.session_id`. If `session_id` is missing or empty, the hook MUST output `{}` and exit 0.

### LA-REQ-004.4: Agent Name Extraction

The hook MUST extract the agent name from `.tool_input.name` in the hook input JSON. If the agent name is missing or empty, the hook MUST output `{}` and exit 0.

### LA-REQ-004.5: Agent ID Extraction

The hook MUST extract the agent ID from `.tool_response.agentId` (falling back to `.tool_response.agent_id`) in the hook input JSON. If the agent ID is missing or empty, the hook MUST output `{}` and exit 0.

### LA-REQ-004.6: LearningAgent Detection

The hook MUST check whether `.deepwork/learning-agents/<agent-name>/` exists. If the directory does NOT exist, the Task was not for a LearningAgent and the hook MUST output `{}` and exit 0 without creating any files.

### LA-REQ-004.7: Session Directory Creation

When a LearningAgent is detected, the hook MUST create the directory `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/` (including all parent directories).

### LA-REQ-004.8: Needs Learning Timestamp File

The hook MUST create a `needs_learning_as_of_timestamp` file in the session directory containing a single ISO 8601 UTC timestamp (format: `YYYY-MM-DDTHH:MM:SSZ`). This file serves as a flag indicating that the session transcript has not yet been processed for learnings.

### LA-REQ-004.9: Agent Used File

The hook MUST create an `agent_used` file in the session directory containing the agent name (matching the folder name under `.deepwork/learning-agents/`). This links the session's agent ID back to the LearningAgent definition.

### LA-REQ-004.10: Post-Task Reminder Message

After creating session tracking files, the hook MUST output a JSON `systemMessage` containing the content of `${CLAUDE_PLUGIN_ROOT}/doc/learning_agent_post_task_reminder.md`. If the reminder file does not exist, the hook MUST output `{}`.

### LA-REQ-004.11: Post-Task Reminder Content

The post-task reminder MUST instruct the user to:
- Resume the same task rather than starting a new one if they need more from the same agent
- Report issues via `/learning-agents report_issue` or by resuming the conversation if the agent made a mistake

### LA-REQ-004.12: Stop Hook Trigger

The Stop hook MUST fire at session end. The hook matcher in `hooks.json` MUST be set to an empty string (`""`) so it triggers for all stop events.

### LA-REQ-004.13: Stop Hook -- No Sessions Directory

If `.deepwork/tmp/agent_sessions` does not exist, the stop hook MUST output `{}` and exit 0.

### LA-REQ-004.14: Stop Hook -- Pending Session Detection

The stop hook MUST search for all `needs_learning_as_of_timestamp` files under `.deepwork/tmp/agent_sessions/`. If none are found, it MUST output `{}` and exit 0.

### LA-REQ-004.15: Stop Hook -- Agent Name Resolution

For each pending session found, the stop hook MUST read the corresponding `agent_used` file to determine which agent was used. It MUST deduplicate agent names before including them in the suggestion message.

### LA-REQ-004.16: Stop Hook -- Learning Suggestion Message

When pending sessions exist, the stop hook MUST output a JSON `systemMessage` that:
- Lists the unique agent names that were used
- Suggests running `/learning-agents learn` to process the transcripts

### LA-REQ-004.17: Session Directory Location

All session tracking files MUST be stored under `.deepwork/tmp/agent_sessions/`. The `.deepwork/tmp/` directory is intended for transient working files and MAY be gitignored.

### LA-REQ-004.18: Timestamp File Update Semantics

The `needs_learning_as_of_timestamp` file MUST be overwritten (not appended) each time the same agent is used in the same session. The timestamp reflects the most recent invocation.

### LA-REQ-004.19: Stop Hook -- Top-Level Agent Input Parsing

The `session_stop.sh` hook MUST read JSON from stdin containing `session_id`, `transcript_path`, and optionally `agent_type` fields. If stdin is empty or not provided (terminal is interactive), the hook MUST skip the top-level tracking phase and proceed to the pending learning check.

### LA-REQ-004.20: Stop Hook -- Top-Level Agent Detection

If the hook input contains a non-empty `agent_type` field and a non-empty `session_id`, the hook MUST normalize the agent name (lowercase, spaces to hyphens) and check whether `.deepwork/learning-agents/<agent-name>/` exists. If the directory does NOT exist, the hook MUST skip session tracking for this session.

### LA-REQ-004.21: Stop Hook -- Top-Level Session Directory

When a top-level LearningAgent session is detected, the hook MUST create the directory `.deepwork/tmp/agent_sessions/<session_id>/top-level/` (including all parent directories). The fixed name `top-level` distinguishes these from subagent sessions which use an `agent_id`.

### LA-REQ-004.22: Stop Hook -- Top-Level Tracking Files

For top-level LearningAgent sessions, the hook MUST create:
1. A `needs_learning_as_of_timestamp` file containing a single ISO 8601 UTC timestamp
2. An `agent_used` file containing the normalized agent name

### LA-REQ-004.23: Stop Hook -- Top-Level Transcript Symlink

For top-level LearningAgent sessions, the hook MUST create a `conversation_transcript.jsonl` symlink pointing to the `transcript_path` from the hook input. The symlink MUST only be created if the transcript file exists at hook execution time.
