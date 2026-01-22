# Run Should-Fire Tests

## Objective

Run all "should fire" tests in **serial** sub-agents to verify that rules fire correctly when their trigger conditions are met without safety conditions.

## CRITICAL: Sub-Agent Requirement

**You MUST spawn sub-agents to make all file edits. DO NOT edit the test files yourself.**

Why sub-agents are required:
1. Sub-agents run in isolated contexts where file changes can be detected
2. When a sub-agent completes, the Stop hook **automatically** evaluates rules
3. You (the main agent) check the sub-agent's returned text for **magic strings** to determine if a hook fired
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

Run all 8 "should fire" tests in **serial** sub-agents, reverting between each, and verify that blocking hooks fire automatically by checking for magic strings.

### Process

**CRITICAL: Timeout Prevention**

Set `max_turns: 5` on each Task tool call to prevent sub-agents from hanging indefinitely. This limits each sub-agent to ~5 API round-trips. If a sub-agent hits the limit (e.g., stuck in infinite block without providing a promise), this confirms the hook IS firing and blocking them - treat it as test PASSED.

**CRITICAL: Magic String Instructions for Sub-Agents**

Every sub-agent prompt MUST include this instruction:
> "IMPORTANT: Start your response with exactly `TASK_START: <brief task description>`. Then complete your task. If a DeepWork hook fires and blocks you with a rules message, also include `HOOK_FIRED: <rule name>` in your response."

**How detection works:**
- Sub-agent ALWAYS outputs `TASK_START:` at the beginning of their response
- If a hook fires and blocks them, they get another turn and can output `HOOK_FIRED:`
- Main agent checks:
  - `HOOK_FIRED:` present → hook fired (test PASSED)
  - `TASK_START:` present + no `HOOK_FIRED:` → hook did NOT fire (test FAILED)
  - Neither `TASK_START:` nor `HOOK_FIRED:` → timeout (test PASSED - confirms hook is blocking infinitely)

For EACH test below, follow this cycle:

1. **Launch a sub-agent** using the Task tool (use a fast model like haiku, set `max_turns: 5`)
2. **Wait for the sub-agent to complete (or hit max_turns limit)**
3. **Check the sub-agent's response for magic strings**:
   - `HOOK_FIRED:` present = Hook fired successfully (test PASSED)
   - `TASK_START:` present + no `HOOK_FIRED:` = Hook did NOT fire (test FAILED)
   - Neither = Timeout/infinite block (test PASSED - confirms hook is blocking)
4. **If inconclusive, check the queue as a fallback**:
   ```bash
   ls -la .deepwork/tmp/rules/queue/
   cat .deepwork/tmp/rules/queue/*.json 2>/dev/null
   ```
   - If queue entries exist with status "queued", the hook DID fire
   - If queue is empty, the hook did NOT fire at all
5. **Record the result** - pass if hook fired (magic string OR queue entry OR timeout), fail if `TASK_START` present without `HOOK_FIRED`
6. **Revert changes and clear queue** (MANDATORY after each test):
   ```bash
   git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
   deepwork rules clear_queue
   ```
   **Why this command sequence**:
   - `git reset HEAD manual_tests/` - Unstages files from the index (rules_check uses `git add -A` which stages changes)
   - `git checkout -- manual_tests/` - Reverts working tree to match HEAD
   - `rm -f ...` - Removes any new files created during tests
   - `deepwork rules clear_queue` - Clears the rules queue so rules can fire again
7. **Check for early termination**: If **2 tests have now failed**, immediately:
   - Stop running any remaining tests
   - Report the results summary showing which tests passed/failed
   - The job halts here - do NOT proceed with remaining tests
8. **Proceed to the next test** (only if fewer than 2 failures)

**IMPORTANT**: Only launch ONE sub-agent at a time. Wait for it to complete and revert before launching the next.

### Test Cases (run serially)

**Test 1: Trigger/Safety**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Trigger/Safety test`. Edit ONLY `manual_tests/test_trigger_safety_mode/test_trigger_safety_mode.py` to add a comment. Do NOT edit the `_doc.md` file. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires with prompt about updating documentation → sub-agent returns `HOOK_FIRED:`

**Test 2: Set Mode**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Set Mode test`. Edit ONLY `manual_tests/test_set_mode/test_set_mode_source.py` to add a comment. Do NOT edit the `_test.py` file. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires with prompt about updating tests → sub-agent returns `HOOK_FIRED:`

**Test 3: Pair Mode**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Pair Mode test`. Edit ONLY `manual_tests/test_pair_mode/test_pair_mode_trigger.py` to add a comment. Do NOT edit the `_expected.md` file. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires with prompt about updating expected output → sub-agent returns `HOOK_FIRED:`

**Test 4: Command Action**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Command Action test`. Edit `manual_tests/test_command_action/test_command_action.txt` to add some text. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Command runs automatically, appending to the log file. NOTE: Command actions don't block, so sub-agent returns only `TASK_START:` - verify by checking the log file was appended to.

**Test 5: Multi Safety**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Multi Safety test`. Edit ONLY `manual_tests/test_multi_safety/test_multi_safety.py` to add a comment. Do NOT edit any of the safety files (`_changelog.md` or `_version.txt`). If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires with prompt about updating safety documentation → sub-agent returns `HOOK_FIRED:`

**Test 6: Infinite Block Prompt**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Infinite Block Prompt test`. Edit `manual_tests/test_infinite_block_prompt/test_infinite_block_prompt.py` to add a comment. Do NOT include any promise tags. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires and BLOCKS with infinite prompt → sub-agent returns `HOOK_FIRED:` or hits timeout

**Test 7: Infinite Block Command**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Infinite Block Command test`. Edit `manual_tests/test_infinite_block_command/test_infinite_block_command.py` to add a comment. Do NOT include any promise tags. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires and command fails → sub-agent returns `HOOK_FIRED:` or hits timeout

**Test 8: Created Mode**
- Sub-agent prompt: "IMPORTANT: Start your response with exactly `TASK_START: Created Mode test`. Create a NEW file `manual_tests/test_created_mode/new_config.yml` with some YAML content. This must be a NEW file, not a modification. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."
- Expected: Hook fires with prompt about new configuration files → sub-agent returns `HOOK_FIRED:`

### Results Tracking

Record the result after each test:

| Test Case | Should Fire | Magic String | Queue Entry? | Result |
|-----------|-------------|:------------:|:------------:|:------:|
| Trigger/Safety | Edit .py only | | | |
| Set Mode | Edit _source.py only | | | |
| Pair Mode | Edit _trigger.py only | | | |
| Command Action | Edit .txt | | | |
| Multi Safety | Edit .py only | | | |
| Infinite Block Prompt | Edit .py (no promise) | | | |
| Infinite Block Command | Edit .py (no promise) | | | |
| Created Mode | Create NEW .yml | | | |

**Magic String Guide:**
- `HOOK_FIRED:` in response → Hook fired successfully (test PASSED)
- `TASK_START:` present + no `HOOK_FIRED:` → Hook did NOT fire (test FAILED, except for Command Action)
- Neither present (timeout) → Hook is blocking infinitely (test PASSED - confirms hook fired)

**Queue Entry Status Guide (fallback):**
- If queue has entry with status "queued" → Hook fired, rule was shown to agent
- If queue has entry with status "passed" → Hook fired, rule was satisfied
- If queue is empty → Hook did NOT fire

## Quality Criteria

- **Sub-agents spawned**: Tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Serial execution**: Sub-agents were launched ONE AT A TIME, not in parallel
- **Git reverted and queue cleared between tests**: `git reset HEAD manual_tests/ && git checkout -- manual_tests/` and `deepwork rules clear_queue` was run after each test
- **Magic string detection**: The main agent checked each sub-agent's response for `TASK_START:` and `HOOK_FIRED:` - did NOT manually run rules_check
- **Hooks fired correctly**: For each test, sub-agent returned `HOOK_FIRED:` or timed out (indicating the rule was triggered)
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Results recorded**: Pass/fail status was recorded for each test run
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs after the "should NOT fire" tests. These tests verify that rules correctly fire when trigger conditions are met without safety conditions. The serial execution with reverts is essential to prevent cross-contamination between tests.
