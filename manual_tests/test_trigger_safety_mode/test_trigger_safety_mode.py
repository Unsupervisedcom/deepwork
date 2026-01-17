"""
MANUAL TEST: Trigger/Safety Mode Rule

=== WHAT THIS TESTS ===
Tests the basic trigger/safety detection mode where:
- Rule FIRES when this file is edited alone
- Rule is SUPPRESSED when test_trigger_safety_mode_doc.md is also edited

=== TEST CASE 1: Rule SHOULD fire ===
1. Edit this file (add a comment below the marker)
2. Do NOT edit test_trigger_safety_mode_doc.md
3. Run: echo '{}' | python -m deepwork.hooks.rules_check
4. Expected: "Manual Test: Trigger Safety" appears in output

=== TEST CASE 2: Rule should NOT fire ===
1. Edit this file (add a comment below the marker)
2. ALSO edit test_trigger_safety_mode_doc.md
3. Run: echo '{}' | python -m deepwork.hooks.rules_check
4. Expected: "Manual Test: Trigger Safety" does NOT appear

=== RULE LOCATION ===
.deepwork/rules/manual-test-trigger-safety.md
"""


def example_function():
    """An example function to demonstrate the trigger."""
    return "Hello from trigger safety test"


# Edit below this line to trigger the rule
# -------------------------------------------
