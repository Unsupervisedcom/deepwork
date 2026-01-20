"""
MANUAL TEST: Infinite Block Command Rule

=== WHAT THIS TESTS ===
Tests a COMMAND-type rule with a command that ALWAYS FAILS - it will ALWAYS
block when the trigger file is edited.

This verifies:
1. The rule correctly blocks when the file is edited (command fails)
2. The error output includes guidance on how to skip using a promise
3. Without guidance in the output, the agent cannot know how to proceed

=== TEST CASE 1: Rule SHOULD fire (command fails, infinite block) ===
1. Edit this file (add a comment below the marker)
2. Run: echo '{}' | python -m deepwork.hooks.rules_check
3. Expected: Block with command error AND promise skip instructions

=== TEST CASE 2: Rule should NOT fire (promise provided) ===
1. Edit this file (add a comment below the marker)
2. Provide a promise (format shown in command error output)
3. Expected: Empty JSON {} (allow) - promise bypasses the command entirely

=== RULE LOCATION ===
.deepwork/rules/manual-test-infinite-block-command.md

=== KEY DIFFERENCE FROM PROMPT VERSION ===
- Prompt version: Shows instructions in the rule's markdown body
- Command version: Must show instructions alongside command error output

If the command error output does NOT include promise skip instructions,
this is a bug - the agent has no way to know how to proceed.
"""


def restricted_command_operation():
    """An operation that requires explicit acknowledgment to proceed."""
    return "This operation uses a command that always fails"


# Edit below this line to trigger the rule
# -------------------------------------------
# Test edit for command block
