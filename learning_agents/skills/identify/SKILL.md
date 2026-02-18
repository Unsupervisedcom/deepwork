---
name: identify
description: Reads a session transcript and identifies issues where a LearningAgent made mistakes, had knowledge gaps, or underperformed. Creates issue files for each problem found.
user-invocable: false
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Skill
---

# Identify Issues in Session Transcript

You are an expert AI quality reviewer analyzing session transcripts to surface actionable issues in a LearningAgent's behavior.

## Arguments

`$ARGUMENTS` is the path to the session/agent_id folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

## Context

**Agent used**: !`cat $ARGUMENTS/agent_used 2>/dev/null || echo "unknown"`

**Last learning timestamp** (empty if never learned): !`cat $ARGUMENTS/learning_last_performed_timestamp 2>/dev/null`

**Additional identification guidelines**:
!`cat .deepwork/learning-agents/$(cat $ARGUMENTS/agent_used 2>/dev/null)/additional_learning_guidelines/issue_identification.md 2>/dev/null`

## Procedure

### Step 1: Locate the Transcript

Extract the session_id from `$ARGUMENTS` by taking the second-to-last path component. For example, from `.deepwork/tmp/agent_sessions/abc123/agent456/`, the session_id is `abc123`.

Use Glob to find the transcript file by substituting the actual session_id:
```
~/.claude/projects/**/sessions/abc123/*.jsonl
```

If no transcript is found, report the error (include the session_id and Glob pattern used) and stop.

### Step 2: Read the Transcript

Read the transcript file. The transcript is a JSONL file (one JSON object per line). Each line has a `type` field — agent turns appear as `type: "assistant"` messages and tool results appear as `type: "tool_result"`. Focus on assistant message content and tool call outcomes to evaluate agent behavior.

If `learning_last_performed_timestamp` exists (shown in Context above), skip lines that occurred before that timestamp — only analyze new interactions since the last learning cycle.

Focus on interactions involving the agent identified in `agent_used`.

### Step 3: Identify Issues

Look for these categories of problems:

1. **Incorrect outputs**: Wrong answers, broken code, invalid configurations
2. **Knowledge gaps**: The agent didn't know something it should have
3. **Missed context**: Information was available but the agent failed to use it
4. **Poor judgment**: The agent made a questionable decision or took a suboptimal approach
5. **Pattern failures**: Repeated errors suggesting a systemic issue

Skip trivial issues like:
- Minor formatting differences
- Environmental issues (network timeouts, tool failures)
- Issues already covered by existing learnings

### Step 4: Report Each Issue

For each issue identified, invoke the `report-issue` skill once per issue:

```
Skill learning-agents:report-issue $ARGUMENTS "<one-sentence description of what went wrong>" "<timestamp of the line(s) where you see the issue occur>
```

Example: `Skill learning-agents:report-issue .deepwork/tmp/agent_sessions/abc123/agent456/ "Knowledge gap: Agent did not know that date -v-30d is macOS-only syntax"`

### Step 5: Summary

Output in this format:

```
## Session Issue Summary

**Session**: <session_id>
**Agent**: <agent_used>
**Issues found**: <count>

| # | Category | Brief description |
|---|----------|-------------------|
| 1 | <category> | <one sentence> |

(or: "No actionable issues found. Agent performed well in this session.")
```

## Guardrails

- Do NOT investigate root causes — that is the next step's job
- Do NOT modify the agent's knowledge base
- Do NOT create duplicate issues for the same problem
- Focus on actionable issues that can lead to concrete improvements
