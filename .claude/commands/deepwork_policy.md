---
description: Policy enforcement for AI agent sessions
---

# deepwork_policy

You are executing the **deepwork_policy** job. Policy enforcement for AI agent sessions

Manages policies that automatically trigger when certain files change during an AI agent session.
Policies help ensure that code changes follow team guidelines, documentation is updated,
and architectural decisions are respected.

Policies are defined in a `.deepwork.policy.yml` file at the root of your project. Each policy
specifies:
- Trigger patterns: Glob patterns for files that, when changed, should trigger the policy
- Safety patterns: Glob patterns for files that, if also changed, mean the policy doesn't need to fire
- Instructions: What the agent should do when the policy triggers

Example use cases:
- Update installation docs when configuration files change
- Require security review when authentication code is modified
- Ensure API documentation stays in sync with API code
- Remind developers to update changelogs


## Available Steps

This job has 1 step(s):

### define
**Define Policy**: Create or update policy entries in .deepwork.policy.yml
- Command: `_deepwork_policy.define`

## Instructions

Determine what the user wants to do and route to the appropriate step.

1. **Analyze user intent** from the text that follows `/deepwork_policy`

2. **Match intent to a step**:
   - define: Create or update policy entries in .deepwork.policy.yml

3. **Invoke the matched step** using the Skill tool:
   ```
   Skill: <step_command_name>
   ```

4. **If intent is ambiguous**, ask the user which step they want:
   - Present the available steps as numbered options
   - Use AskUserQuestion to let them choose

**Critical**: You MUST invoke the step using the Skill tool. Do not copy/paste the step's instructions. The Skill tool invocation ensures the step's quality validation hooks fire.

## Context Files

- Job definition: `.deepwork/jobs/deepwork_policy/job.yml`