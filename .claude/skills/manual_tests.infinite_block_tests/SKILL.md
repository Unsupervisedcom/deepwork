---
name: manual_tests.infinite_block_tests
description: "Runs all 4 infinite block tests serially. Tests both 'should fire' (no promise) and 'should NOT fire' (with promise) scenarios."
user-invocable: false
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. **Sub-Agents Used**: Did the main agent spawn a sub-agent (using the Task tool) for EACH test? The main agent must NOT edit the test files directly.
            2. **Sub-Agent Config**: Did all sub-agents use `model: "haiku"` and `max_turns: 5`?
            3. **Serial Execution**: Were sub-agents launched ONE AT A TIME (not in parallel)?
            4. **Promise Tests Passed**: Did tests with promise tags complete WITHOUT blocking?
            5. **Non-Promise Tests Blocked**: Did tests without promise tags correctly trigger blocking behavior?
            6. **Reset Between Tests**: Was the reset step called internally after each test?
            7. **Early Termination**: If 2 tests failed, did testing halt immediately with results reported?
            8. **Results Recorded**: Did the main agent track pass/fail status for each test case?

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response OR
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
  SubagentStop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. **Sub-Agents Used**: Did the main agent spawn a sub-agent (using the Task tool) for EACH test? The main agent must NOT edit the test files directly.
            2. **Sub-Agent Config**: Did all sub-agents use `model: "haiku"` and `max_turns: 5`?
            3. **Serial Execution**: Were sub-agents launched ONE AT A TIME (not in parallel)?
            4. **Promise Tests Passed**: Did tests with promise tags complete WITHOUT blocking?
            5. **Non-Promise Tests Blocked**: Did tests without promise tags correctly trigger blocking behavior?
            6. **Reset Between Tests**: Was the reset step called internally after each test?
            7. **Early Termination**: If 2 tests failed, did testing halt immediately with results reported?
            8. **Results Recorded**: Did the main agent track pass/fail status for each test case?

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response OR
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
---

# manual_tests.infinite_block_tests

**Step 4/4** in **manual_tests** workflow

> Runs all manual hook/rule tests using sub-agents. Use when validating that DeepWork rules fire correctly.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/manual_tests.run_fire_tests`

## Instructions

**Goal**: Runs all 4 infinite block tests serially. Tests both 'should fire' (no promise) and 'should NOT fire' (with promise) scenarios.

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
- Expected: Hook fires and BLOCKS with infinite prompt - sub-agent cannot complete until promise is provided (or max_turns reached)
- Result: PASS if hook fired (visible block OR queue entry), FAIL if neither

**Test 4: Infinite Block Command - Should Fire (no promise)**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_command/risky.py` to add a comment. Do NOT include any promise tags."
- Sub-agent config: `model: "haiku"`, `max_turns: 5`
- Expected: Hook fires and command fails - sub-agent cannot complete until promise is provided (or max_turns reached)
- Result: PASS if hook fired (visible block OR queue entry), FAIL if neither

### Results Tracking

Record the result after each test:

| Test Case | Scenario | Expected | Visible Block? | Queue Entry? | Result |
|-----------|----------|----------|:--------------:|:------------:|:------:|
| Infinite Block Prompt | With promise | No block | | | |
| Infinite Block Command | With promise | No block | | | |
| Infinite Block Prompt | No promise | Blocks | | | |
| Infinite Block Command | No promise | Blocks | | | |

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
- **Blocking behavior verified**: Promise tests completed without blocking; non-promise tests were blocked
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Results recorded**: Pass/fail status was recorded for each test run
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after both the "should NOT fire" and "should fire" test steps. It specifically tests infinite blocking behavior which requires serial execution due to the blocking nature of these rules.


### Job Context

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


## Required Inputs


**Files from Previous Steps** - Read these first:
- `fire_results` (from `run_fire_tests`)

## Work Branch

Use branch format: `deepwork/manual_tests-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/manual_tests-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `infinite_block_results`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

Stop hooks will automatically validate your work. The loop continues until all criteria pass.

**Criteria (all must be satisfied)**:
1. **Sub-Agents Used**: Did the main agent spawn a sub-agent (using the Task tool) for EACH test? The main agent must NOT edit the test files directly.
2. **Sub-Agent Config**: Did all sub-agents use `model: "haiku"` and `max_turns: 5`?
3. **Serial Execution**: Were sub-agents launched ONE AT A TIME (not in parallel)?
4. **Promise Tests Passed**: Did tests with promise tags complete WITHOUT blocking?
5. **Non-Promise Tests Blocked**: Did tests without promise tags correctly trigger blocking behavior?
6. **Reset Between Tests**: Was the reset step called internally after each test?
7. **Early Termination**: If 2 tests failed, did testing halt immediately with results reported?
8. **Results Recorded**: Did the main agent track pass/fail status for each test case?


**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 4/4 complete, outputs: infinite_block_results"
3. **Workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/jobs/manual_tests/job.yml`, `.deepwork/jobs/manual_tests/steps/infinite_block_tests.md`