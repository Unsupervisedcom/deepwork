"""
MANUAL TEST: Infinite Block Command Rule (Promise Required)

=== WHAT THIS TESTS ===
Tests a COMMAND-type rule with a command that ALWAYS FAILS - it will ALWAYS
block when the trigger file is edited. This tests whether the promise mechanism
works for command-action rules.

This verifies:
1. The rule correctly blocks when the file is edited (command fails)
2. The promise mechanism should bypass the command entirely
3. The promise must be in the exact format: <promise>Rule Name</promise>

=== TEST CASE 1: Rule SHOULD fire (command fails, infinite block) ===
1. Edit this file (add a comment below the marker)
2. Run: echo '{}' | python -m deepwork.hooks.rules_check
3. Expected: Block with command error - the `false` command always fails

=== TEST CASE 2: Rule should NOT fire (promise provided) ===
1. Edit this file (add a comment below the marker)
2. Create a transcript with: <promise>Manual Test: Infinite Block Command</promise>
3. Run the hook with the transcript
4. Expected: Empty JSON {} (allow) - promise should bypass the command entirely

=== HOW TO TEST WITH PROMISE ===
The promise must be in the conversation transcript. To test:

1. Create a temp transcript file with the promise:
   echo '{"role":"assistant","message":{"content":[{"type":"text","text":"<promise>Manual Test: Infinite Block Command</promise>"}]}}' > /tmp/transcript.jsonl

2. Run with transcript:
   echo '{"transcript_path":"/tmp/transcript.jsonl"}' | python -m deepwork.hooks.rules_check

3. Expected: {} (empty JSON = allow)
   If NOT empty: BUG - promises don't work for command-action rules!

=== RULE LOCATION ===
.deepwork/rules/manual-test-infinite-block-command.md

=== KEY DIFFERENCE FROM PROMPT VERSION ===
- Prompt version: Shows instructions, agent must respond with promise
- Command version: Runs a command that always fails, promise should skip it

If the promise mechanism doesn't work for command rules, this test will reveal
that bug - the command will still run and fail even when a promise is provided.
"""


def restricted_command_operation():
    """An operation that requires explicit acknowledgment to proceed."""
    return "This operation uses a command that always fails"


# Edit below this line to trigger the rule
# -------------------------------------------
# Test edit for command block