---
name: learn
description: Runs the learning cycle on all LearningAgent sessions with pending transcripts. Identifies issues, investigates root causes, and incorporates learnings into agent definitions.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash, Task, Skill
---

# Learning Cycle

Process unreviewed LearningAgent session transcripts to identify issues, investigate root causes, and incorporate learnings into agent definitions.

## Arguments

This skill takes no arguments. It automatically discovers all pending sessions.

## Pending Sessions

!`find .deepwork/tmp/agent_sessions -name needs_learning_as_of_timestamp 2>/dev/null`

## Procedure

### Step 1: Find Pending Sessions

Check for pending learning sessions. The dynamic include above lists all `needs_learning_as_of_timestamp` files. If the list is empty (or the `.deepwork/tmp/agent_sessions` directory does not exist), inform the user that there are no pending sessions to learn from and stop.

For each pending file, extract:
- The session folder path (parent directory of `needs_learning_as_of_timestamp`, e.g., `.deepwork/tmp/agent_sessions/sess-abc/agent-123/`)
- The agent name (read the `agent_used` file in that folder)

### Step 2: Process Each Session

For each pending session folder, run the learning cycle in sequence. The Task pseudo-code below shows the parameters to pass to the Task tool:

#### 2a: Identify Issues

```
Task tool call:
  name: "identify-issues"
  subagent_type: general-purpose
  model: sonnet
  prompt: "Run the identify skill on the session folder: .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/
           Use: Skill learning-agents:identify .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/"
```

#### 2b: Investigate and Incorporate

After identification completes, spawn another Task to run investigation and incorporation in sequence:

```
Task tool call:
  name: "investigate-and-incorporate"
  subagent_type: general-purpose
  model: sonnet
  prompt: "Run these two skills in sequence on the session folder: .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/
           1. First: Skill learning-agents:investigate-issues .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/
           2. Then: Skill learning-agents:incorporate-learnings .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/"
```

#### Handling failures

If a sub-skill Task fails for a session, log the failure, skip that session, and continue processing remaining sessions. Do not mark `needs_learning_as_of_timestamp` as resolved for failed sessions.

### Step 3: Summary

Output in this format:

```
## Learning Cycle Summary

- **Sessions processed**: <count>
- **Total issues identified**: <count>
- **Agents updated**: <comma-separated list of agent names>
- **Key learnings**:
  - <agent-name>: <brief learning description>
- **Skipped sessions** (if any): <session path> — <reason>
```

## Guardrails

- Process sessions one at a time to avoid conflicts when multiple sessions involve the same agent
- If a session's transcript cannot be found, skip it and report the issue
- Do NOT modify agent files directly — always delegate to the learning cycle skills
- Use Sonnet model for Task spawns to balance cost and quality
