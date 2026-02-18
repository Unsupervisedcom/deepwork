---
name: incorporate-learnings
description: Takes investigated issues and incorporates the learnings into the LearningAgent's knowledge base by updating core-knowledge.md, topics, or learnings files.
user-invocable: false
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Incorporate Learnings

Take investigated issues and integrate the lessons learned into the LearningAgent's knowledge base.

## Arguments

`$ARGUMENTS` is the path to the session log folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

## Context

**Agent used**: !`cat $ARGUMENTS/agent_used 2>/dev/null || echo "unknown"`

If `agent_used` is "unknown", stop and report an error — the session folder is missing required metadata.

## Procedure

### Step 1: Find Investigated Issues

List all issue files with status `investigated`:

```bash
grep -l 'status: investigated' $ARGUMENTS/*.issue.yml
```

If no investigated issues are found, report that and skip to Step 5 (still update tracking files).

### Step 2: Read Agent Knowledge Base

Read the current state of the agent's knowledge:

- `.deepwork/learning-agents/<agent-name>/core-knowledge.md`
- `.deepwork/learning-agents/<agent-name>/topics/*.md`
- `.deepwork/learning-agents/<agent-name>/learnings/*.md`

Where `<agent-name>` is from `$ARGUMENTS/agent_used`.

### Step 3: Incorporate Each Issue

For each investigated issue, read the issue file (both `issue_description` and `investigation_report`) and determine the best way to incorporate the learning. Apply options in this priority order:

#### Option D (first priority): Amend existing content

Check first. If a closely related file already exists in the agent's knowledge base that covers the same area, edit that file rather than creating a new one.

Example: Issue "Agent used wrong retry count" when `topics/retry-handling.md` already exists → update the existing topic with the correct information.

#### Option A: Update `core-knowledge.md`

Use when the issue is a **universal one-liner** — something fundamental the agent should always know that can be expressed in 1-2 sentences.

Example: Issue "Agent called a python program directly that only works with `uv run`" → add a bullet to `core-knowledge.md`: "Always use `uv run` when invoking `util.py`."

#### Option B: Add a new topic in `topics/`

Use when the issue reveals a new or existing **conceptual area** needing 1+ paragraphs of reference material that is not always needed, but often enough to track.

```markdown
---
name: <Topic Name>
keywords:
  - <relevant keyword>
last_updated: <today's date YYYY-MM-DD>
---

<Detailed documentation about this topic area...>
```

Example: Issue "Agent didn't understand retry backoff patterns" → create `topics/retry-backoff.md` with documentation on exponential backoff, jitter, and dead letter queues.

#### Option C: Add a new learning in `learnings/`

Use when the **narrative context of how the issue unfolded** is needed to understand the resolution — multi-step debugging sessions, surprising interactions, or subtle misunderstandings.

```markdown
---
name: <Descriptive name of the learning>
last_updated: <today's date YYYY-MM-DD>
summarized_result: |
  <1-3 sentence summary of the key takeaway>
---

## Context
<What was happening when the issue occurred>

## Investigation
<What was discovered during investigation>

## Resolution
<How the issue should be handled going forward>

## Key Takeaway
<The generalizable insight>
```

Example: Issue "Agent spent 20 minutes debugging a permissions error that was actually caused by a stale Docker volume" → create a learning capturing the full debugging narrative and the insight about checking Docker volumes early.

**IMPORTANT**: If you add a `learnings` entry, you may want to also add a brief note to a Topic with reference to the learning too.

#### Option D: Do nothing
If you decide that the issue would have been hard to prevent, or if it seems extremely unlikely that it will be encountered again, forgo any changes and just move on to step 4.

### Step 4: Update Issue Status

For each incorporated issue, use Edit to change `status: investigated` to `status: learned` in the issue file.

### Step 5: Update Session Tracking

Always run this step, even if no issues were incorporated.

1. Delete `needs_learning_as_of_timestamp` if it exists:
   ```bash
   [ -f $ARGUMENTS/needs_learning_as_of_timestamp ] && rm $ARGUMENTS/needs_learning_as_of_timestamp
   ```

2. Write the current timestamp to `learning_last_performed_timestamp`:
   ```bash
   date -u +"%Y-%m-%dT%H:%M:%SZ" > $ARGUMENTS/learning_last_performed_timestamp
   ```

### Step 6: Summary

Output in this format:

```
## Incorporation Summary

- **Issues processed**: <count>
- <issue-filename> → <action taken: updated core-knowledge | created topic <name> | created learning <name> | amended <filename>>
- <issue-filename> → could not incorporate: <reason>
```

## Guardrails

- Do NOT create overly broad or vague learnings — be specific and actionable
- Do NOT duplicate existing knowledge — check before adding
- Do NOT remove existing content unless it is directly contradicted by new evidence
- Keep `core-knowledge.md` concise — move detailed content to topics or learnings
- Use today's date for `last_updated` fields
- Always run Step 5 (update tracking files) even if no issues were incorporated
