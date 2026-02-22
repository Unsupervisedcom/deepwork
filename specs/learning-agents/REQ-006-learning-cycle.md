# REQ-006: Learning Cycle Orchestration

## Overview

The learning cycle (`/learning-agents learn`) is the top-level orchestrator that discovers all pending sessions and runs the three-phase learning process (identify, investigate, incorporate) on each. It delegates actual work to sub-skills via Task tool spawns.

## Requirements

### REQ-006.1: Skill Invocation

The learning cycle MUST be invocable via `/learning-agents learn`. Arguments after `learn` MUST be ignored.

### REQ-006.2: Automatic Session Discovery

The skill MUST automatically discover all pending sessions by searching for `needs_learning_as_of_timestamp` files under `.deepwork/tmp/agent_sessions/`. The skill MUST NOT require the user to specify which sessions to process.

### REQ-006.3: No Pending Sessions

If no `needs_learning_as_of_timestamp` files are found (or the `.deepwork/tmp/agent_sessions` directory does not exist), the skill MUST inform the user that there are no pending sessions and stop.

### REQ-006.4: Session Metadata Extraction

For each pending session, the skill MUST extract:
- The session folder path (parent directory of `needs_learning_as_of_timestamp`)
- The agent name (from the `agent_used` file in that folder)

### REQ-006.5: Three-Phase Processing

For each pending session, the skill MUST run the learning cycle in three sequential phases:
1. **Identify**: Spawn a Task to run the `identify` skill on the session folder
2. **Investigate**: Spawn a Task to run the `investigate-issues` skill on the session folder
3. **Incorporate**: Spawn a Task to run the `incorporate-learnings` skill on the session folder

The investigate and incorporate phases MAY be combined into a single Task invocation, but they MUST execute in that order.

### REQ-006.6: Task Tool Usage for Sub-Skills

The identify phase MUST be run as a separate Task invocation. The investigate and incorporate phases MUST be run as a combined Task invocation (investigate first, then incorporate). All Task spawns MUST use the `learning-agents:identify`, `learning-agents:investigate-issues`, and `learning-agents:incorporate-learnings` skills respectively.

### REQ-006.7: Sub-Task Model Selection

Task spawns for learning cycle sub-skills MUST use the Sonnet model to balance cost and quality.

### REQ-006.8: Sequential Session Processing

Sessions MUST be processed one at a time (sequentially, not in parallel) to avoid conflicts when multiple sessions involve the same agent.

### REQ-006.9: Failure Handling

If a sub-skill Task fails for a session, the skill MUST:
- Log the failure
- Skip that session
- Continue processing remaining sessions
- NOT mark `needs_learning_as_of_timestamp` as resolved for the failed session

### REQ-006.10: Missing Transcript Handling

If a session's transcript cannot be found, the skill MUST skip that session and report the issue in the final summary.

### REQ-006.11: Summary Output

Upon completion, the skill MUST output a summary containing:
- Total sessions processed
- Total issues identified
- List of agents updated
- Key learnings per agent
- Any skipped sessions with reasons

### REQ-006.12: No Direct Agent Modification

The `learn` skill MUST NOT modify agent files directly. All agent knowledge base changes MUST be delegated to the learning cycle sub-skills (identify, investigate-issues, incorporate-learnings).

### REQ-006.13: Dynamic Pending Session List

The skill MUST use a dynamic include (`!` backtick `find` command) to list pending sessions at invocation time, ensuring it always has the current state of pending sessions.
