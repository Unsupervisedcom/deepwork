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

**These tests MUST run ONE AT A TIME, with git reverts between each.**

Why serial execution is required:
- These tests edit ONLY the trigger file (not the safety)
- If multiple sub-agents run in parallel, sub-agent A's hook will see changes from sub-agent B
- This causes cross-contamination: A gets blocked by rules triggered by B's changes
- Run one test, observe the hook, revert, then run the next

## Task

Run all 8 "should fire" tests in **serial** sub-agents, reverting between each, and verify that blocking hooks fire automatically.

### Process

For EACH test below, follow this cycle:

1. **Launch a sub-agent** using the Task tool (use a fast model like haiku)
2. **Wait for the sub-agent to complete**
3. **Observe whether the hook fired automatically** - you should see a blocking prompt or command output
4. **Record the result** - pass if hook fired, fail if it didn't
5. **Revert changes**: `git checkout -- manual_tests/`
6. **Proceed to the next test**

**IMPORTANT**: Only launch ONE sub-agent at a time. Wait for it to complete and revert before launching the next.

### Test Cases (run serially)

**Test 1: Trigger/Safety**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_trigger_safety_mode/feature.py` to add a comment. Do NOT edit the `_doc.md` file."
- Expected: Hook fires with prompt about updating documentation

**Test 2: Set Mode**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_set_mode/module_source.py` to add a comment. Do NOT edit the `_test.py` file."
- Expected: Hook fires with prompt about updating tests

**Test 3: Pair Mode**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_pair_mode/handler_trigger.py` to add a comment. Do NOT edit the `_expected.md` file."
- Expected: Hook fires with prompt about updating expected output

**Test 4: Command Action**
- Sub-agent prompt: "Edit `manual_tests/test_command_action/input.txt` to add some text."
- Expected: Command runs automatically, appending to the log file (this rule always runs, no safety condition)

**Test 5: Multi Safety**
- Sub-agent prompt: "Edit ONLY `manual_tests/test_multi_safety/core.py` to add a comment. Do NOT edit any of the safety files (`_safety_a.md`, `_safety_b.md`, or `_safety_c.md`)."
- Expected: Hook fires with prompt about updating safety documentation

**Test 6: Infinite Block Prompt**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_prompt/dangerous.py` to add a comment. Do NOT include any promise tags."
- Expected: Hook fires and BLOCKS with infinite prompt - sub-agent cannot complete until promise is provided

**Test 7: Infinite Block Command**
- Sub-agent prompt: "Edit `manual_tests/test_infinite_block_command/risky.py` to add a comment. Do NOT include any promise tags."
- Expected: Hook fires and command fails - sub-agent cannot complete until promise is provided

**Test 8: Created Mode**
- Sub-agent prompt: "Create a NEW file `manual_tests/test_created_mode/new_config.yml` with some YAML content. This must be a NEW file, not a modification."
- Expected: Hook fires with prompt about new configuration files

### Results Tracking

Record the result after each test:

| Test Case | Should Fire | Hook Fired? | Result |
|-----------|-------------|:-----------:|:------:|
| Trigger/Safety | Edit .py only | | |
| Set Mode | Edit _source.py only | | |
| Pair Mode | Edit _trigger.py only | | |
| Command Action | Edit .txt | | |
| Multi Safety | Edit .py only | | |
| Infinite Block Prompt | Edit .py (no promise) | | |
| Infinite Block Command | Edit .py (no promise) | | |
| Created Mode | Create NEW .yml | | |

## Quality Criteria

- **Sub-agents spawned**: All 8 tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Serial execution**: Sub-agents were launched ONE AT A TIME, not in parallel
- **Git reverted between tests**: `git checkout -- manual_tests/` was run after each test
- **Hooks observed (not triggered)**: The main agent observed hook behavior without manually running rules_check - hooks fired AUTOMATICALLY
- **Blocking behavior verified**: For each test, the appropriate blocking hook fired automatically when the sub-agent returned
- **Results recorded**: Pass/fail status was recorded for each test
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after the "should NOT fire" tests. These tests verify that rules correctly fire when trigger conditions are met without safety conditions. The serial execution with reverts is essential to prevent cross-contamination between tests.
