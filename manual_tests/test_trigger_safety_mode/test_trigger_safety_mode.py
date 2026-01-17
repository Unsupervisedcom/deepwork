"""
MANUAL TEST: Trigger/Safety Mode Rule

=== WHAT THIS TESTS ===
Tests the basic trigger/safety detection mode where:
- Rule FIRES when this file is edited
- Rule is SUPPRESSED when test_trigger_safety_mode_doc.md is also edited

=== HOW TO TRIGGER ===
1. Edit this file (add/remove a line, change a comment, etc.)
2. Do NOT edit test_trigger_safety_mode_doc.md
3. The rule "Manual Test: Trigger Safety" should fire
4. To suppress the rule: also edit test_trigger_safety_mode_doc.md

=== EXPECTED BEHAVIOR ===
- Edit this file alone -> Rule fires with prompt about updating documentation
- Edit this file + doc file -> Rule is suppressed (safety pattern matched)

=== RULE LOCATION ===
.deepwork/rules/manual-test-trigger-safety.md
"""


def example_function():
    """An example function to demonstrate the trigger."""
    return "Hello from trigger safety test"


# Edit below this line to trigger the rule
# -------------------------------------------
