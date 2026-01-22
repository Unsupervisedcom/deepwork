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
