"""
MANUAL TEST: Set Mode (Bidirectional Correspondence)

=== WHAT THIS TESTS ===
Tests the "set" detection mode where files must change together:
- This source file and test_set_mode_test.py are in a "set"
- If EITHER file changes, the OTHER must also change
- This is BIDIRECTIONAL (works in both directions)

=== TEST CASE 1: Rule SHOULD fire ===
1. Edit this file (add a comment below the marker)
2. Do NOT edit test_set_mode_test.py
3. Run: echo '{}' | deepwork hook deepwork.hooks.rules_check
4. Expected: "Manual Test: Set Mode" appears in output

=== TEST CASE 2: Rule should NOT fire ===
1. Edit this file (add a comment below the marker)
2. ALSO edit test_set_mode_test.py
3. Run: echo '{}' | deepwork hook deepwork.hooks.rules_check
4. Expected: "Manual Test: Set Mode" does NOT appear

=== RULE LOCATION ===
.deepwork/rules/manual-test-set-mode.md
"""


class Calculator:
    """A simple calculator for testing set mode."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b


# Edit below this line to trigger the rule
# -------------------------------------------
