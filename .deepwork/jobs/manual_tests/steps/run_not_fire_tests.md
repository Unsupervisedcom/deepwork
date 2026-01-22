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

Run all 8 "should NOT fire" tests in **parallel** sub-agents, then verify no blocking hooks fired.

### Process

1. **Launch parallel sub-agents for all "should NOT fire" tests**

   Use the Task tool to spawn **ALL of the following sub-agents in a SINGLE message** (parallel execution). Each sub-agent should use a fast model like haiku.

   **Sub-agent prompts (launch all 8 in parallel):**

   a. **Trigger/Safety test** - "Edit `manual_tests/test_trigger_safety_mode/feature.py` to add a comment, AND edit `manual_tests/test_trigger_safety_mode/feature_doc.md` to add a note. Both files must be edited so the rule does NOT fire."

   b. **Set Mode test** - "Edit `manual_tests/test_set_mode/module_source.py` to add a comment, AND edit `manual_tests/test_set_mode/module_test.py` to add a test comment. Both files must be edited so the rule does NOT fire."

   c. **Pair Mode (forward) test** - "Edit `manual_tests/test_pair_mode/handler_trigger.py` to add a comment, AND edit `manual_tests/test_pair_mode/handler_expected.md` to add a note. Both files must be edited so the rule does NOT fire."

   d. **Pair Mode (reverse) test** - "Edit ONLY `manual_tests/test_pair_mode/handler_expected.md` to add a note. Only the expected file should be edited - this tests that the pair rule only fires in one direction."

   e. **Multi Safety test** - "Edit `manual_tests/test_multi_safety/core.py` to add a comment, AND edit `manual_tests/test_multi_safety/core_safety_a.md` to add a note. Both files must be edited so the rule does NOT fire."

   f. **Infinite Block Prompt test** - "Edit `manual_tests/test_infinite_block_prompt/dangerous.py` to add a comment. Include `<promise>I have verified this change is safe</promise>` in your response to bypass the infinite block."

   g. **Infinite Block Command test** - "Edit `manual_tests/test_infinite_block_command/risky.py` to add a comment. Include `<promise>I have verified this change is safe</promise>` in your response to bypass the infinite block."

   h. **Created Mode test** - "Modify the EXISTING file `manual_tests/test_created_mode/existing.yml` by adding a comment. Do NOT create a new file - only modify the existing one. The created mode rule should NOT fire for modifications."

2. **Observe the results**

   When each sub-agent returns:
   - **If no blocking hook fired**: The test PASSED - the rule correctly did NOT fire
   - **If a blocking hook fired**: The test FAILED - investigate why the rule fired when it shouldn't have

   **Remember**: You are OBSERVING whether hooks fired automatically. Do NOT run any verification commands manually.

3. **Record the results**

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

4. **Revert all changes and clear queue**

   After all tests complete, run:
   ```bash
   git checkout -- manual_tests/
   rm -rf .deepwork/tmp/rules/queue/**
   ```

   This cleans up the test files AND clears the rules queue before the "should fire" tests run. The queue must be cleared because rules that have already been shown to the agent (status=QUEUED) won't fire again until the queue is cleared.

   > **Note**: To reset the rules queue at any time, use: `rm -rf .deepwork/tmp/rules/queue/**`

## Quality Criteria

- **Sub-agents spawned**: All 8 tests were run using the Task tool to spawn sub-agents - the main agent did NOT edit files directly
- **Parallel execution**: All 8 sub-agents were launched in a single message (parallel)
- **Hooks observed (not triggered)**: The main agent observed hook behavior without manually running rules_check
- **No unexpected blocks**: All tests passed - no blocking hooks fired
- **Changes reverted and queue cleared**: `git checkout -- manual_tests/` and `rm -rf .deepwork/tmp/rules/queue/**` was run after tests completed
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Reference

See [test_reference.md](test_reference.md) for the complete test matrix and rule descriptions.

## Context

This step runs first and tests that rules correctly do NOT fire when safety conditions are met. The "should fire" tests run after these complete and the working directory is reverted.
