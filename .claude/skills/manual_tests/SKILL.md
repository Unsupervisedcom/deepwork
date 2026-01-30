---
name: manual_tests
description: "Runs all manual hook/rule tests using sub-agents. Use when validating that DeepWork rules fire correctly."
---

# manual_tests Agent

Runs all manual hook/rule tests using sub-agents. Use when validating that DeepWork rules fire correctly.

A workflow for running manual tests that validate DeepWork rules/hooks fire correctly.

The **run_all** workflow tests that rules fire when they should AND do not fire when they shouldn't.
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
1. reset - Ensure clean environment before testing (clears queue, reverts files)
2. run_not_fire_tests - Run all "should NOT fire" tests in PARALLEL sub-agents (6 tests)
3. run_fire_tests - Run all "should fire" tests in SERIAL sub-agents with resets between (6 tests)
4. infinite_block_tests - Run infinite block tests in SERIAL (4 tests - both fire and not-fire)

Reset procedure (see steps/reset.md):
- Reset runs FIRST to ensure a clean environment before any tests
- Each step also calls reset internally when needed (between tests, after completion)
- Reset reverts git changes, removes created files, and clears the rules queue

Test types covered:
- Trigger/Safety mode
- Set mode (bidirectional)
- Pair mode (directional)
- Command action
- Multi safety
- Infinite block (prompt and command) - in dedicated step
- Created mode (new files only)


## Agent Overview

This agent handles the **manual_tests** job with 4 skills.

**Workflows**: run_all
---

## How to Use This Agent

### Workflows
- **run_all**: Run all manual tests: reset, NOT-fire tests, fire tests, and infinite block tests (reset → run_not_fire_tests → run_fire_tests → infinite_block_tests)
  - Start: `reset`

### All Skills
- `reset` - Runs FIRST to ensure clean environment. Also called internally by other steps when they need to revert changes and clear the queue.
- `run_not_fire_tests` - Runs all 6 'should NOT fire' tests in parallel sub-agents. Use to verify rules don't fire when safety conditions are met.
- `run_fire_tests` - Runs all 6 'should fire' tests serially with resets between each. Use after NOT-fire tests to verify rules fire correctly.
- `infinite_block_tests` - Runs all 4 infinite block tests serially. Tests both 'should fire' (no promise) and 'should NOT fire' (with promise) scenarios.

---

## Agent Execution Instructions

When invoked, follow these steps:

### Step 1: Understand Intent

Parse the user's request to determine:
1. Which workflow or skill to execute
2. Any parameters or context provided
3. Whether this is a continuation of previous work

### Step 2: Check Work Branch

Before executing any skill:
1. Check current git branch
2. If on a `deepwork/manual_tests-*` branch: continue using it
3. If on main/master: create new branch `deepwork/manual_tests-[instance]-$(date +%Y%m%d)`

### Step 3: Execute the Appropriate Skill

Navigate to the relevant skill section below and follow its instructions.

### Step 4: Workflow Continuation

After completing a workflow step:
1. Inform the user of completion and outputs created
2. Automatically proceed to the next step if one exists
3. Continue until the workflow is complete or the user intervenes

---

## Skills

### Skill: reset

**Type**: Workflow step 1/4 in **run_all**

**Description**: Runs FIRST to ensure clean environment. Also called internally by other steps when they need to revert changes and clear the queue.




#### Instructions

# Reset Manual Tests Environment

## Objective

Reset the manual tests environment by reverting all file changes and clearing the rules queue.

## Purpose

This step contains all the reset logic that other steps can call when they need to clean up between or after tests. It ensures consistent cleanup across all test steps.

## Reset Commands

Run these commands to reset the environment:

```bash
git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
deepwork rules clear_queue
```

## Command Explanation

- `git reset HEAD manual_tests/` - Unstages files from the index (rules_check uses `git add -A` which stages changes)
- `git checkout -- manual_tests/` - Reverts working tree to match HEAD
- `rm -f manual_tests/test_created_mode/new_config.yml` - Removes any new files created during tests (the created mode test creates this file)
- `deepwork rules clear_queue` - Clears the rules queue so rules can fire again (prevents anti-infinite-loop mechanism from blocking subsequent tests)

## When to Reset

- **After each serial test**: Reset immediately after observing the result to prevent cross-contamination
- **After parallel tests complete**: Reset once all parallel sub-agents have returned
- **On early termination**: Reset before reporting failure results
- **Before starting a new test step**: Ensure clean state

## Quality Criteria

- **All changes reverted**: `git status` shows no changes in `manual_tests/`
- **Queue cleared**: `.deepwork/tmp/rules/queue/` is empty
- **New files removed**: `manual_tests/test_created_mode/new_config.yml` does not exist


#### Outputs

Create these files/directories:
- `clean_environment`
#### Quality Validation

Before completing this skill, verify:
1. **Environment Clean**: Git changes reverted, created files removed, and rules queue cleared

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "reset complete, outputs: clean_environment"
3. **Continue to next skill**: Proceed to `run_not_fire_tests`

---

### Skill: run_not_fire_tests

**Type**: Workflow step 2/4 in **run_all**

**Description**: Runs all 6 'should NOT fire' tests in parallel sub-agents. Use to verify rules don't fire when safety conditions are met.

#### Prerequisites

Before running this skill, ensure these are complete:
- `reset`


#### Input Files

Read these files (from previous steps):
- `clean_environment` (from `reset`)

#### Instructions

# Run Should-NOT-Fire Tests

## Objective

Run all "should NOT fire" tests in parallel sub-agents to verify that rules do not fire when their safety conditions are met.

## CRITICAL: Sub-Agent Requirement

**You MUST spawn sub-agents to make all file edits. DO NOT edit the test files yourself.**

Why sub-agents are required:
1. Sub-agents run in isolated contexts where file changes are detected
2. When a sub-agent completes, the Stop hook **automatically** evaluates rules
3. You (the main agent) observe whether hooks fired - you do NOT manually trigger them
4. If you edit files directly, the hooks won't fire because you're not a completing sub-agent

**NEVER manually run `echo '{}' | python -m deepwork.hooks.rules_check`** - this defeats the purpose of the test. Hooks must fire AUTOMATICALLY when sub-agents return.

## Task

Run all 6 "should NOT fire" tests in **parallel** sub-agents, then verify no blocking hooks fired.

### Process

1. **Launch parallel sub-agents for all "should NOT fire" tests**

   Use the Task tool to spawn **ALL of the following sub-agents in a SINGLE message** (parallel execution).

   **Sub-agent configuration for ALL sub-agents:**
   - `model: "haiku"` - Use the fast model to minimize cost and latency
   - `max_turns: 5` - Prevent sub-agents from hanging indefinitely

   **Sub-agent prompts (launch all 6 in parallel):**

   a. **Trigger/Safety test** - "Edit `manual_tests/test_trigger_safety_mode/feature.py` to add a comment, AND edit `manual_tests/test_trigger_safety_mode/feature_doc.md` to add a note. Both files must be edited so the rule does NOT fire."

   b. **Set Mode test** - "Edit `manual_tests/test_set_mode/module_source.py` to add a comment, AND edit `manual_tests/test_set_mode/module_test.py` to add a test comment. Both files must be edited so the rule does NOT fire."

   c. **Pair Mode (forward) test** - "Edit `manual_tests/test_pair_mode/handler_trigger.py` to add a comment, AND edit `manual_tests/test_pair_mode/handler_expected.md` to add a note. Both files must be edited so the rule does NOT fire."

   d. **Pair Mode (reverse) test** - "Edit ONLY `manual_tests/test_pair_mode/handler_expected.md` to add a note. Only the expected file should be edited - this tests that the pair rule only fires in one direction."

   e. **Multi Safety test** - "Edit `manual_tests/test_multi_safety/core.py` to add a comment, AND edit `manual_tests/test_multi_safety/core_safety_a.md` to add a note. Both files must be edited so the rule does NOT fire."

   f. **Created Mode test** - "Modify the EXISTING file `manual_tests/test_created_mode/existing.yml` by adding a comment. Do NOT create a new file - only modify the existing one. The created mode rule should NOT fire for modifications."

2. **Observe the results**

   When each sub-agent returns:
   - **If no blocking hook fired**: Preliminary pass - proceed to queue verification
   - **If a blocking hook fired**: The test FAILED - investigate why the rule fired when it shouldn't have

   **Remember**: You are OBSERVING whether hooks fired automatically. Do NOT run any verification commands manually during sub-agent execution.

3. **Verify no queue entries** (CRITICAL for "should NOT fire" tests)

   After ALL sub-agents have completed, verify the rules queue is empty:
   ```bash
   ls -la .deepwork/tmp/rules/queue/
   cat .deepwork/tmp/rules/queue/*.json 2>/dev/null
   ```

   - **If queue is empty**: All tests PASSED - rules correctly did not fire
   - **If queue has entries**: Tests FAILED - rules fired when they shouldn't have. Check which rule fired and investigate.

   This verification is essential because some rules may fire without visible blocking but still create queue entries.

4. **Record the results and check for early termination**

   Track which tests passed and which failed:

   | Test Case | Should NOT Fire | Visible Block? | Queue Entry? | Result |
   |-----------|:---------------:|:--------------:|:------------:|:------:|
   | Trigger/Safety | Edit both files | | | |
   | Set Mode | Edit both files | | | |
   | Pair Mode (forward) | Edit both files | | | |
   | Pair Mode (reverse) | Edit expected only | | | |
   | Multi Safety | Edit both files | | | |
   | Created Mode | Modify existing | | | |

   **Result criteria**: PASS only if NO visible block AND NO queue entry. FAIL if either occurred.

   **EARLY TERMINATION**: If **2 tests have failed**, immediately:
   1. Stop running any remaining tests
   2. Reset (see step 5)
   3. Report the results summary showing which tests passed/failed
   4. Do NOT proceed to the next step - the job halts here

5. **Reset** (MANDATORY - call the reset step internally)

   **IMPORTANT**: This step is MANDATORY and must run regardless of whether tests passed or failed.

   Follow the reset step instructions. Run these commands to clean up:
   ```bash
   git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
   deepwork rules clear_queue
   ```

   See [reset.md](reset.md) for detailed explanation of these commands.

## Quality Criteria

- **Sub-agents spawned**: All 6 tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Correct sub-agent config**: All sub-agents used `model: "haiku"` and `max_turns: 5`
- **Parallel execution**: All 6 sub-agents were launched in a single message (parallel)
- **Hooks observed (not triggered)**: The main agent observed hook behavior without manually running rules_check
- **Queue verified empty**: After all sub-agents completed, the rules queue was checked and confirmed empty (no queue entries = rules did not fire)
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Reset performed**: Reset step was followed after tests completed (regardless of pass/fail)
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after the reset step (which ensures a clean environment) and tests that rules correctly do NOT fire when safety conditions are met. The "should fire" tests run after these complete. Infinite block tests are handled in a separate step.


#### Outputs

Create these files/directories:
- `not_fire_results`
#### Quality Validation

Before completing this skill, verify:
1. **Sub-Agents Used**: Did the main agent spawn sub-agents (using the Task tool) to make the file edits? The main agent must NOT edit the test files directly.
2. **Sub-Agent Config**: Did all sub-agents use `model: "haiku"` and `max_turns: 5`?
3. **Parallel Execution**: Were all 6 sub-agents launched in parallel (in a single message with multiple Task tool calls)?
4. **Hooks Observed**: Did the main agent observe that no blocking hooks fired when the sub-agents returned? The hooks fire AUTOMATICALLY - the agent must NOT manually run the rules_check command.
5. **Queue Verified Empty**: After all sub-agents completed, was the rules queue checked and confirmed empty (no entries = rules did not fire)?
6. **Early Termination**: If 2 tests failed, did testing halt immediately with results reported?
7. **Reset Performed**: Was the reset step called internally after tests completed (or after early termination)?

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "run_not_fire_tests complete, outputs: not_fire_results"
3. **Continue to next skill**: Proceed to `run_fire_tests`

---

### Skill: run_fire_tests

**Type**: Workflow step 3/4 in **run_all**

**Description**: Runs all 6 'should fire' tests serially with resets between each. Use after NOT-fire tests to verify rules fire correctly.

#### Prerequisites

Before running this skill, ensure these are complete:
- `run_not_fire_tests`


#### Input Files

Read these files (from previous steps):
- `not_fire_results` (from `run_not_fire_tests`)

#### Instructions

# Run Should-Fire Tests

## Objective

Run all "should fire" tests in **serial** sub-agents to verify that rules fire correctly when their trigger conditions are met without safety conditions.

## CRITICAL: Sub-Agent Requirement

**You MUST spawn sub-agents to make all file edits. DO NOT edit the test files yourself.**

Why sub-agents are required:
1. Sub-agents run in isolated contexts where file changes are detected
2. When a sub-agent completes, the Stop hook **automatically** evaluates rules
3. You (the main agent) observe whether hooks fired - you do NOT manually trigger them
4. If you edit files directly, the hooks won't fire because you're not a completing sub-agent

**NEVER manually run `echo '{}' | python -m deepwork.hooks.rules_check`** - this defeats the purpose of the test. Hooks must fire AUTOMATICALLY when sub-agents return.

## CRITICAL: Serial Execution

**These tests MUST run ONE AT A TIME, with resets between each.**

Why serial execution is required:
- These tests edit ONLY the trigger file (not the safety)
- If multiple sub-agents run in parallel, sub-agent A's hook will see changes from sub-agent B
- This causes cross-contamination: A gets blocked by rules triggered by B's changes
- Run one test, observe the hook, reset, then run the next

## Task

Run all 6 "should fire" tests in **serial** sub-agents, resetting between each, and verify that blocking hooks fire automatically.

### Process

For EACH test below, follow this cycle:

1. **Launch a sub-agent** using the Task tool with:
   - `model: "haiku"` - Use the fast model to minimize cost and latency
   - `max_turns: 5` - Prevent sub-agents from hanging indefinitely
2. **Wait for the sub-agent to complete**
3. **Observe whether the hook fired automatically** - you should see a blocking prompt or command output
4. **If no visible blocking occurred, check the queue**:
   ```bash
   ls -la .deepwork/tmp/rules/queue/
   cat .deepwork/tmp/rules/queue/*.json 2>/dev/null
   ```
   - If queue entries exist with status "queued", the hook DID fire but blocking wasn't visible
   - If queue is empty, the hook did NOT fire at all
   - Record the queue status along with the result
5. **Record the result** - pass if hook fired (visible block OR queue entry), fail if neither
6. **Reset** (MANDATORY after each test) - follow the reset step instructions:
   ```bash
   git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
   deepwork rules clear_queue
   ```
   See [reset.md](reset.md) for detailed explanation of these commands.
7. **Check for early termination**: If **2 tests have now failed**, immediately:
   - Stop running any remaining tests
   - Report the results summary showing which tests passed/failed
   - The job halts here - do NOT proceed with remaining tests
8. **Proceed to the next test** (only if fewer than 2 failures)

**IMPORTANT**: Only launch ONE sub-agent at a time. Wait for it to complete and reset before launching the next.

### Test Cases (run serially)

**Test 1: Trigger/Safety**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_trigger_safety_mode/feature.py` to add a comment. Do NOT edit the `_doc.md` file."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires with prompt about updating documentation

**Test 2: Set Mode**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_set_mode/module_source.py` to add a comment. Do NOT edit the `_test.py` file."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires with prompt about updating tests

**Test 3: Pair Mode**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_pair_mode/handler_trigger.py` to add a comment. Do NOT edit the `_expected.md` file."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires with prompt about updating expected output

**Test 4: Command Action**
- Sub-agent prompt: "Edit `manual_tests/test_command_action/input.txt` to add some text."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Command runs automatically, appending to the log file (this rule always runs, no safety condition)

**Test 5: Multi Safety**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_multi_safety/core.py` to add a comment. Do NOT edit any of the safety files (`_safety_a.md`, `_safety_b.md`, or `_safety_c.md`)."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires with prompt about updating safety documentation

**Test 6: Created Mode**
- Sub-agent prompt: "Create a NEW file `manual_tests/test_created_mode/new_config.yml` with some YAML content. This must be a NEW file, not a modification."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires with prompt about new configuration files

### Results Tracking

Record the result after each test:

| Test Case | Should Fire | Visible Block? | Queue Entry? | Result |
|-----------|-------------|:--------------:|:------------:|:------:|
| Trigger/Safety | Edit .py only | | | |
| Set Mode | Edit _source.py only | | | |
| Pair Mode | Edit _trigger.py only | | | |
| Command Action | Edit .txt | | | |
| Multi Safety | Edit .py only | | | |
| Created Mode | Create NEW .yml | | | |

**Queue Entry Status Guide:**
- If queue has entry with status "queued" -> Hook fired, rule was shown to agent
- If queue has entry with status "passed" -> Hook fired, rule was satisfied
- If queue is empty -> Hook did NOT fire

## Quality Criteria

- **Sub-agents spawned**: Tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Correct sub-agent config**: All sub-agents used `model: "haiku"` and `max_turns: 5`
- **Serial execution**: Sub-agents were launched ONE AT A TIME, not in parallel
- **Reset between tests**: Reset step was followed after each test
- **Hooks fired automatically**: The main agent observed the blocking hooks firing automatically when each sub-agent returned - the agent did NOT manually run rules_check
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Results recorded**: Pass/fail status was recorded for each test case
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after the "should NOT fire" tests. These tests verify that rules correctly fire when trigger conditions are met without safety conditions. The serial execution with resets is essential to prevent cross-contamination between tests. Infinite block tests are handled in a separate step.


#### Outputs

Create these files/directories:
- `fire_results`
#### Quality Validation

Before completing this skill, verify:
1. **Sub-Agents Used**: Did the main agent spawn a sub-agent (using the Task tool) for EACH test? The main agent must NOT edit the test files directly.
2. **Sub-Agent Config**: Did all sub-agents use `model: "haiku"` and `max_turns: 5`?
3. **Serial Execution**: Were sub-agents launched ONE AT A TIME (not in parallel) to prevent cross-contamination?
4. **Hooks Fired Automatically**: Did the main agent observe the blocking hooks firing automatically when each sub-agent returned? The agent must NOT manually run the rules_check command.
5. **Reset Between Tests**: Was the reset step called internally after each test to revert files and prevent cross-contamination?
6. **Early Termination**: If 2 tests failed, did testing halt immediately with results reported?
7. **Results Recorded**: Did the main agent track pass/fail status for each test case?

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "run_fire_tests complete, outputs: fire_results"
3. **Continue to next skill**: Proceed to `infinite_block_tests`

---

### Skill: infinite_block_tests

**Type**: Workflow step 4/4 in **run_all**

**Description**: Runs all 4 infinite block tests serially. Tests both 'should fire' (no promise) and 'should NOT fire' (with promise) scenarios.

#### Prerequisites

Before running this skill, ensure these are complete:
- `run_fire_tests`


#### Input Files

Read these files (from previous steps):
- `fire_results` (from `run_fire_tests`)

#### Instructions

# Run Infinite Block Tests

## Objective

Run all infinite block tests in **serial** to verify that infinite blocking rules work correctly - both firing when they should AND not firing when bypassed with a promise tag.

## CRITICAL: Sub-Agent Requirement

**You MUST spawn sub-agents to make all file edits. DO NOT edit the test files yourself.**

Why sub-agents are required:
1. Sub-agents run in isolated contexts where file changes are detected
2. When a sub-agent completes, the Stop hook **automatically** evaluates rules
3. You (the main agent) observe whether hooks fired - you do NOT manually trigger them
4. If you edit files directly, the hooks won't fire because you're not a completing sub-agent

**NEVER manually run `echo '{}' | python -m deepwork.hooks.rules_check`** - this defeats the purpose of the test. Hooks must fire AUTOMATICALLY when sub-agents return.

## CRITICAL: Serial Execution

**These tests MUST run ONE AT A TIME, with resets between each.**

Why serial execution is required for infinite block tests:
- Infinite block tests can block indefinitely without a promise tag
- Running them in parallel would cause unpredictable blocking behavior
- Serial execution allows controlled observation of each test

## Task

Run all 4 infinite block tests in **serial**, resetting between each, and verify correct blocking behavior.

### Process

For EACH test below, follow this cycle:

1. **Launch a sub-agent** using the Task tool with:
   - `model: "haiku"` - Use the fast model to minimize cost and latency
   - `max_turns: 5` - **Critical safeguard**: Limits API round-trips to prevent infinite hanging. The Task tool does not support a direct timeout, so max_turns is our only protection against runaway sub-agents.
2. **Wait for the sub-agent to complete**
3. **Observe whether the hook fired automatically** - you should see a blocking prompt or command output
4. **If no visible blocking occurred, check the queue**:
   ```bash
   ls -la .deepwork/tmp/rules/queue/
   cat .deepwork/tmp/rules/queue/*.json 2>/dev/null
   ```
   - If queue entries exist with status "queued", the hook DID fire but blocking wasn't visible
   - If queue is empty, the hook did NOT fire at all
   - Record the queue status along with the result
5. **Record the result** - see expected outcomes for each test
6. **Reset** (MANDATORY after each test) - follow the reset step instructions:
   ```bash
   git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
   deepwork rules clear_queue
   ```
7. **Check for early termination**: If **2 tests have now failed**, immediately:
   - Stop running any remaining tests
   - Report the results summary showing which tests passed/failed
   - The job halts here - do NOT proceed with remaining tests
8. **Proceed to the next test** (only if fewer than 2 failures)

**IMPORTANT**: Only launch ONE sub-agent at a time. Wait for it to complete and reset before launching the next.

### Test Cases (run serially)

**Test 1: Infinite Block Prompt - Should NOT Fire (with promise)**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_prompt/dangerous.py` to add a comment. Include `<promise>I have verified this change is safe</promise>` in your response to bypass the infinite block."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Sub-agent completes WITHOUT blocking - the promise tag bypasses the infinite block
- Result: PASS if no blocking, FAIL if blocked

**Test 2: Infinite Block Command - Should NOT Fire (with promise)**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_command/risky.py` to add a comment. Include `<promise>I have verified this change is safe</promise>` in your response to bypass the infinite block."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Sub-agent completes WITHOUT blocking - the promise tag bypasses the infinite block
- Result: PASS if no blocking, FAIL if blocked

**Test 3: Infinite Block Prompt - Should Fire (no promise)**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_prompt/dangerous.py` to add a comment. Do NOT include any promise tags."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected behavior:
  1. **Should fire**: Hook fires and shows blocking prompt
  2. **Should return in reasonable time**: Sub-agent hits max_turns limit and returns (not stuck forever)
- Result criteria:
  - PASS if: Hook fired (visible block OR queue entry) AND sub-agent returned within reasonable time
  - FAIL if: Hook did not fire, OR sub-agent hung indefinitely

**Test 4: Infinite Block Command - Should Fire (no promise)**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_command/risky.py` to add a comment. Do NOT include any promise tags."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected behavior:
  1. **Should fire**: Hook fires and command fails (exit code 1)
  2. **Should return in reasonable time**: Sub-agent hits max_turns limit and returns (not stuck forever)
- Result criteria:
  - PASS if: Hook fired (visible block OR queue entry) AND sub-agent returned within reasonable time
  - FAIL if: Hook did not fire, OR sub-agent hung indefinitely

### Results Tracking

Record the result after each test:

| Test Case | Scenario | Should Fire? | Returned in Time? | Visible Block? | Queue Entry? | Result |
|-----------|----------|:------------:|:-----------------:|:--------------:|:------------:|:------:|
| Infinite Block Prompt | With promise | No | Yes | | | |
| Infinite Block Command | With promise | No | Yes | | | |
| Infinite Block Prompt | No promise | Yes | Yes | | | |
| Infinite Block Command | No promise | Yes | Yes | | | |

**Result criteria:**
- **"Should NOT fire" tests (with promise)**: PASS if no blocking AND no queue entry AND returned quickly
- **"Should fire" tests (no promise)**: PASS if hook fired (visible block OR queue entry) AND returned in reasonable time (max_turns limit)

**Queue Entry Status Guide:**
- If queue has entry with status "queued" -> Hook fired, rule was shown to agent
- If queue has entry with status "passed" -> Hook fired, rule was satisfied
- If queue is empty -> Hook did NOT fire

## Quality Criteria

- **Sub-agents spawned**: Tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Correct sub-agent config**: All sub-agents used `model: "haiku"` and `max_turns: 5`
- **Serial execution**: Sub-agents were launched ONE AT A TIME, not in parallel
- **Reset between tests**: Reset step was followed after each test
- **Hooks observed (not triggered)**: The main agent observed hook behavior without manually running rules_check - hooks fired AUTOMATICALLY
- **"Should NOT fire" tests verified**: Promise tests completed without blocking and no queue entries
- **"Should fire" tests verified**: Non-promise tests fired (visible block OR queue entry) AND returned in reasonable time (not hung indefinitely)
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Results recorded**: Pass/fail status was recorded for each test run
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after both the "should NOT fire" and "should fire" test steps. It specifically tests infinite blocking behavior which requires serial execution due to the blocking nature of these rules.


#### Outputs

Create these files/directories:
- `infinite_block_results`
#### Quality Validation

Before completing this skill, verify:
1. **Sub-Agents Used**: Each test run via Task tool with `model: "haiku"` and `max_turns: 5`
2. **Serial Execution**: Sub-agents launched ONE AT A TIME with reset between each
3. **Promise Tests**: Completed WITHOUT blocking (promise bypassed the rule)
4. **No-Promise Tests**: Hook fired AND sub-agent returned in reasonable time (not hung)

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "run_all workflow complete, outputs: infinite_block_results"
3. Consider creating a PR to merge the work branch

---

## Guardrails

- **Never skip prerequisites**: Always verify required steps are complete before running a skill
- **Never produce partial outputs**: Complete all required outputs before marking a skill done
- **Always use the work branch**: Never commit directly to main/master
- **Follow quality criteria**: Use sub-agent review when quality criteria are specified
- **Ask for clarification**: If user intent is unclear, ask before proceeding

## Context Files

- Job definition: `.deepwork/jobs/manual_tests/job.yml`
- reset instructions: `.deepwork/jobs/manual_tests/steps/reset.md`
- run_not_fire_tests instructions: `.deepwork/jobs/manual_tests/steps/run_not_fire_tests.md`
- run_fire_tests instructions: `.deepwork/jobs/manual_tests/steps/run_fire_tests.md`
- infinite_block_tests instructions: `.deepwork/jobs/manual_tests/steps/infinite_block_tests.md`
