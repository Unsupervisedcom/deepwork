"""
MANUAL TEST: Infinite Block Rule (Promise Required)

=== WHAT THIS TESTS ===
Tests a rule with NO safety file option - it will ALWAYS block when the
trigger file is edited. The only way to proceed is to provide a promise
in the correct format.

This verifies:
1. The rule correctly blocks when the file is edited
2. The promise mechanism works to bypass the block
3. The promise must be in the exact format: <promise>Rule Name</promise>

=== TEST CASE 1: Rule SHOULD fire (infinite block) ===
1. Edit this file (add a comment below the marker)
2. Run: echo '{}' | python -m deepwork.hooks.rules_check
3. Expected: "Manual Test: Infinite Block" appears in output with decision="block"
4. The block message should explain that a promise is required

=== TEST CASE 2: Rule should NOT fire (promise provided) ===
1. Edit this file (add a comment below the marker)
2. Create a transcript with: <promise>Manual Test: Infinite Block</promise>
3. Run the hook with the transcript
4. Expected: Empty JSON {} (allow) - promise bypasses the block

=== HOW TO TEST WITH PROMISE ===
The promise must be in the conversation transcript. To test:

1. Create a temp transcript file with the promise:
   echo '{"role":"assistant","message":{"content":[{"type":"text","text":"<promise>Manual Test: Infinite Block</promise>"}]}}' > /tmp/transcript.jsonl

2. Run with transcript:
   echo '{"transcript_path":"/tmp/transcript.jsonl"}' | python -m deepwork.hooks.rules_check

3. Expected: {} (empty JSON = allow)

=== RULE LOCATION ===
.deepwork/rules/manual-test-infinite-block.md

=== KEY DIFFERENCE FROM OTHER TESTS ===
Other tests have a "safety" file that can be edited to suppress the rule.
This test has NO safety option - the ONLY way to proceed is with a promise.
This simulates scenarios where the agent must explicitly acknowledge a
constraint before proceeding.
"""


def restricted_operation():
    """An operation that requires explicit acknowledgment to proceed."""
    return "This operation always requires a promise to proceed"


# Edit below this line to trigger the rule
# -------------------------------------------
