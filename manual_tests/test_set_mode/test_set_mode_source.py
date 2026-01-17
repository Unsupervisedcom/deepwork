"""
MANUAL TEST: Set Mode (Bidirectional Correspondence)

=== WHAT THIS TESTS ===
Tests the "set" detection mode where files must change together:
- This source file and test_set_mode_test.py are in a "set"
- If EITHER file changes, the OTHER must also change
- This is BIDIRECTIONAL (works in both directions)

=== HOW TO TRIGGER ===
Option A: Edit this file alone (without test_set_mode_test.py)
Option B: Edit test_set_mode_test.py alone (without this file)

=== EXPECTED BEHAVIOR ===
- Edit this file alone -> Rule fires, expects test file to also change
- Edit test file alone -> Rule fires, expects this file to also change
- Edit BOTH files -> Rule is satisfied (no fire)

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
