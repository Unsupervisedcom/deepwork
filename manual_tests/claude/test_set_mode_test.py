"""
MANUAL TEST: Set Mode - Test File (Bidirectional Correspondence)

=== WHAT THIS TESTS ===
This is the TEST file for the set mode test.
It must change together with test_set_mode_source.py.

=== HOW TO TRIGGER ===
Option A: Edit this file alone (without test_set_mode_source.py)
Option B: Edit test_set_mode_source.py alone (without this file)

=== EXPECTED BEHAVIOR ===
- Edit this file alone -> Rule fires, expects source file to also change
- Edit source file alone -> Rule fires, expects this file to also change
- Edit BOTH files -> Rule is satisfied (no fire)

=== RULE LOCATION ===
.deepwork/rules/manual-test-set-mode.md
"""

from test_set_mode_source import Calculator


def test_add():
    """Test the add method."""
    calc = Calculator()
    assert calc.add(2, 3) == 5


def test_subtract():
    """Test the subtract method."""
    calc = Calculator()
    assert calc.subtract(5, 3) == 2


# Edit below this line to trigger the rule
# -------------------------------------------
