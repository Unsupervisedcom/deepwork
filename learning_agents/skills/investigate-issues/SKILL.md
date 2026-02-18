---
name: investigate-issues
description: Investigates identified issues in a LearningAgent session by reading the transcript, determining root causes, and updating issue files with investigation reports.
user-invocable: false
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Edit
---

# Investigate Issues

Research identified issues from a LearningAgent session to determine their root causes.

## Arguments

`$ARGUMENTS` is the path to the session log folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

## Context

**Agent used**: !`cat $ARGUMENTS/agent_used 2>/dev/null || echo "unknown"`

**Agent core knowledge**:
!`cat .deepwork/learning-agents/$(cat $ARGUMENTS/agent_used 2>/dev/null)/core-knowledge.md 2>/dev/null`

## Procedure

### Step 1: Find Identified Issues

List all issue files with status `identified`:

```bash
grep -l 'status: identified' $ARGUMENTS/*.issue.yml
```

If no identified issues are found, report that and stop.

### Step 2: Locate the Transcript

Extract the session_id from `$ARGUMENTS` by taking the second-to-last path component (e.g., from `.deepwork/tmp/agent_sessions/abc123/agent456/`, the session_id is `abc123`).

Use Glob to find the transcript file by substituting the actual extracted session_id:
```
~/.claude/projects/**/sessions/<extracted_session_id>/*.jsonl
```

If no transcript file is found, report the missing path and stop. Do not proceed to investigate without transcript evidence.

### Step 3: Investigate Each Issue

For each issue file with status `identified`:

1. **Read the issue file** to understand what went wrong
2. **Search the transcript** for relevant sections — grep for keywords from `issue_description` or locate lines near timestamps in `seen_at_timestamps`
3. **Determine root cause** using this taxonomy:
   - **Knowledge gap**: Missing or incomplete content in `core-knowledge.md`
   - **Missing documentation**: A topic file does not exist or lacks needed detail
   - **Incorrect instruction**: An existing instruction leads the agent to wrong behavior
   - **Missing runtime context**: Information that should have been injected at runtime was absent
4. **Write the investigation report** explaining:
   - Specific evidence from the transcript (reference line numbers)
   - The root cause analysis
   - What knowledge gap or instruction deficiency led to the issue

### Step 4: Update Issue Files

For each investigated issue, use Edit to update the issue file:

1. Change `status: identified` to `status: investigated`
2. Add the `investigation_report` field with your findings:

```yaml
status: investigated
seen_at_timestamps:
  - "2025-01-15T14:32:00Z"
issue_description: |
  <original description>
investigation_report: |
  <Your root cause analysis.
  Include specific line numbers from the transcript as evidence.
  Explain why the agent behaved incorrectly.
  Identify what knowledge gap or instruction deficiency caused the issue.>
```

### Step 5: Summary

Output in this format for each issue:

```
**Issue**: <filename>
**Root cause**: <one sentence>
**Recommended update type**: <expertise update | new topic | new learning | instruction fix>
```

## Guardrails

- Do NOT modify the agent's knowledge base — that is the incorporate step's job
- Do NOT change the `issue_description` — only add the `investigation_report`
- Do NOT skip issues — investigate every `identified` issue in the folder
- Be specific about evidence — reference transcript line numbers
- Focus on actionable root causes, not blame
