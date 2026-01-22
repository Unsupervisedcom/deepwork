---
name: manual_tests
description: "Runs all manual hook/rule tests using sub-agents. Use when validating that DeepWork rules fire correctly."
---

# manual_tests

**Multi-step workflow**: Runs all manual hook/rule tests using sub-agents. Use when validating that DeepWork rules fire correctly.

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for running manual tests that validate DeepWork rules/hooks fire correctly.

This job tests that rules fire when they should AND do not fire when they shouldn't.
Each test is run in a SUB-AGENT (not the main agent) because:
1. Sub-agents run in isolated contexts where file changes can be detected
2. The Stop hook automatically evaluates rules when each sub-agent completes
3. The main agent can observe whether hooks fired without triggering them manually

CRITICAL: All tests MUST run in sub-agents. The main agent MUST NOT make the file
edits itself - it spawns sub-agents to make edits, then observes whether the hooks
fired automatically when those sub-agents returned.

Sub-agent configuration:
- All sub-agents should use `model: "haiku"` to minimize cost and latency
- All sub-agents should use `max_turns: 5` to prevent hanging indefinitely

Steps:
1. run_not_fire_tests - Run all "should NOT fire" tests in PARALLEL sub-agents (6 tests)
2. run_fire_tests - Run all "should fire" tests in SERIAL sub-agents with resets between (6 tests)
3. infinite_block_tests - Run infinite block tests in SERIAL (4 tests - both fire and not-fire)

Reset procedure (see steps/reset.md):
- Each step calls the reset procedure internally when needed
- Reset reverts git changes, removes created files, and clears the rules queue

Test types covered:
- Trigger/Safety mode
- Set mode (bidirectional)
- Pair mode (directional)
- Command action
- Multi safety
- Infinite block (prompt and command) - in dedicated step
- Created mode (new files only)


## Available Steps

1. **reset** - Utility step containing reset instructions. Called internally by other steps when they need to revert changes and clear the queue.
2. **run_not_fire_tests** - Runs all 6 'should NOT fire' tests in parallel sub-agents. Use to verify rules don't fire when safety conditions are met.
3. **run_fire_tests** - Runs all 6 'should fire' tests serially with resets between each. Use after NOT-fire tests to verify rules fire correctly. (requires: run_not_fire_tests)
4. **infinite_block_tests** - Runs all 4 infinite block tests serially. Tests both 'should fire' (no promise) and 'should NOT fire' (with promise) scenarios. (requires: run_fire_tests)

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/manual_tests` to determine user intent:
- "reset" or related terms → start at `manual_tests.reset`
- "run_not_fire_tests" or related terms → start at `manual_tests.run_not_fire_tests`
- "run_fire_tests" or related terms → start at `manual_tests.run_fire_tests`
- "infinite_block_tests" or related terms → start at `manual_tests.infinite_block_tests`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: manual_tests.reset
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available steps as numbered options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in the workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/manual_tests/job.yml`