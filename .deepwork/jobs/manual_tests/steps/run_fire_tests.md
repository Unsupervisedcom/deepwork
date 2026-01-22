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
