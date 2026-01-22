# Run Should-NOT-Fire Tests

## Objective

Run all "should NOT fire" tests in parallel sub-agents to verify that rules do not fire when their safety conditions are met.

## CRITICAL: Sub-Agent Requirement

**You MUST spawn sub-agents to make all file edits. DO NOT edit the test files yourself.**

Why sub-agents are required:
1. Sub-agents run in isolated contexts where file changes can be detected
2. When a sub-agent completes, the Stop hook **automatically** evaluates rules
3. You (the main agent) check the sub-agent's returned text for **magic strings** to determine if a hook fired
4. If you edit files directly, the hooks won't fire because you're not a completing sub-agent

**NEVER manually run `echo '{}' | python -m deepwork.hooks.rules_check`** - this defeats the purpose of the test. Hooks must fire AUTOMATICALLY when sub-agents return.

## Task

Run all 8 "should NOT fire" tests in **parallel** sub-agents, then check each sub-agent's response for magic strings to determine pass/fail.

### Process

1. **Launch parallel sub-agents for all "should NOT fire" tests**

   Use the Task tool to spawn **ALL of the following sub-agents in a SINGLE message** (parallel execution). Each sub-agent should use a fast model like haiku.

   **CRITICAL: Timeout Prevention**

   Set `max_turns: 5` on each Task tool call to prevent sub-agents from hanging indefinitely. This limits each sub-agent to ~5 API round-trips, which is plenty for these simple edit tasks. If a sub-agent hits the limit, treat it as a timeout/failure.

   **CRITICAL: Magic String Instructions for Sub-Agents**

   Every sub-agent prompt MUST include this instruction:
   > "IMPORTANT: Start your response with exactly `TASK_START: <brief task description>`. Then complete your task. If a DeepWork hook fires and blocks you with a rules message, also include `HOOK_FIRED: <rule name>` in your response."

   **How detection works:**
   - Sub-agent ALWAYS outputs `TASK_START:` at the beginning of their response
   - If a hook fires and blocks them, they get another turn and can output `HOOK_FIRED:`
   - Main agent checks: `TASK_START` present + no `HOOK_FIRED` = hook did NOT fire

   **Sub-agent prompts (launch all 8 in parallel):**

   a. **Trigger/Safety test** - "IMPORTANT: Start your response with exactly `TASK_START: Trigger/Safety test`. Edit `manual_tests/test_trigger_safety_mode/test_trigger_safety_mode.py` to add a comment, AND edit `manual_tests/test_trigger_safety_mode/test_trigger_safety_mode_doc.md` to add a note. Both files must be edited so the rule does NOT fire. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   b. **Set Mode test** - "IMPORTANT: Start your response with exactly `TASK_START: Set Mode test`. Edit `manual_tests/test_set_mode/test_set_mode_source.py` to add a comment, AND edit `manual_tests/test_set_mode/test_set_mode_test.py` to add a test comment. Both files must be edited so the rule does NOT fire. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   c. **Pair Mode (forward) test** - "IMPORTANT: Start your response with exactly `TASK_START: Pair Mode forward test`. Edit `manual_tests/test_pair_mode/test_pair_mode_trigger.py` to add a comment, AND edit `manual_tests/test_pair_mode/test_pair_mode_expected.md` to add a note. Both files must be edited so the rule does NOT fire. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   d. **Pair Mode (reverse) test** - "IMPORTANT: Start your response with exactly `TASK_START: Pair Mode reverse test`. Edit ONLY `manual_tests/test_pair_mode/test_pair_mode_expected.md` to add a note. Only the expected file should be edited - this tests that the pair rule only fires in one direction. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   e. **Multi Safety test** - "IMPORTANT: Start your response with exactly `TASK_START: Multi Safety test`. Edit `manual_tests/test_multi_safety/test_multi_safety.py` to add a comment, AND edit `manual_tests/test_multi_safety/test_multi_safety_changelog.md` to add a note. Both files must be edited so the rule does NOT fire. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   f. **Infinite Block Prompt test** - "IMPORTANT: Start your response with exactly `TASK_START: Infinite Block Prompt test`. Edit `manual_tests/test_infinite_block_prompt/test_infinite_block_prompt.py` to add a comment. Include `<promise>Manual Test: Infinite Block Prompt</promise>` in your response to bypass the infinite block. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   g. **Infinite Block Command test** - "IMPORTANT: Start your response with exactly `TASK_START: Infinite Block Command test`. Edit `manual_tests/test_infinite_block_command/test_infinite_block_command.py` to add a comment. Include `<promise>Manual Test: Infinite Block Command</promise>` in your response to bypass the infinite block. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

   h. **Created Mode test** - "IMPORTANT: Start your response with exactly `TASK_START: Created Mode test`. Modify the EXISTING file `manual_tests/test_created_mode/existing_file.yml` by adding a comment. Do NOT create a new file - only modify the existing one. The created mode rule should NOT fire for modifications. If a DeepWork hook fires and blocks you, also include `HOOK_FIRED: <rule name>` in your response."

2. **Check the results using magic strings**

   When each sub-agent returns, check their response for magic strings:
   - **If `TASK_START:` present AND no `HOOK_FIRED:`**: The test PASSED - the rule correctly did NOT fire
   - **If `HOOK_FIRED:` present**: The test FAILED - investigate why the rule fired when it shouldn't have
   - **If neither `TASK_START:` nor `HOOK_FIRED:`**: The test is INCONCLUSIVE (timeout or sub-agent didn't follow instructions)

   **Remember**: You determine pass/fail by checking for magic strings in the sub-agent's response. Do NOT run any verification commands manually.

3. **Record the results and check for early termination**

   Track which tests passed and which failed:

   | Test Case | Should NOT Fire | Result |
   |-----------|:---------------:|:------:|
   | Trigger/Safety | Edit both files | |
   | Set Mode | Edit both files | |
   | Pair Mode (forward) | Edit both files | |
   | Pair Mode (reverse) | Edit expected only | |
   | Multi Safety | Edit both files | |
   | Infinite Block Prompt | Promise tag | |
   | Infinite Block Command | Promise tag | |
   | Created Mode | Modify existing | |

   **EARLY TERMINATION**: If **2 tests have failed**, immediately:
   1. Stop running any remaining tests
   2. Revert all changes and clear queue (see step 4)
   3. Report the results summary showing which tests passed/failed
   4. Do NOT proceed to the next step - the job halts here

4. **Revert all changes and clear queue**

   **IMPORTANT**: This step is MANDATORY and must run regardless of whether tests passed or failed.

   Run these commands to clean up:
   ```bash
   git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
   deepwork rules clear_queue
   ```

   **Why this command sequence**:
   - `git reset HEAD manual_tests/` - Unstages files from the index (rules_check uses `git add -A` which stages changes)
   - `git checkout -- manual_tests/` - Reverts working tree to match HEAD
   - `rm -f manual_tests/test_created_mode/new_config.yml` - Removes any new files created during tests
   - `deepwork rules clear_queue` - Clears the rules queue so rules can fire again

## Quality Criteria

- **Sub-agents spawned**: All 8 tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Parallel execution**: All 8 sub-agents were launched in a single message (parallel)
- **Magic string detection**: The main agent checked each sub-agent's response for `TASK_START:` (present) and `HOOK_FIRED:` (absent) - did NOT manually run rules_check
- **Early termination on 2 failures**: If 2 tests failed, testing halted immediately and results were reported
- **Changes reverted and queue cleared**: `git reset HEAD manual_tests/ && git checkout -- manual_tests/` and `deepwork rules clear_queue` was run after tests completed (regardless of pass/fail)
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs first and tests that rules correctly do NOT fire when safety conditions are met. The "should fire" tests run after these complete and the working directory is reverted.
