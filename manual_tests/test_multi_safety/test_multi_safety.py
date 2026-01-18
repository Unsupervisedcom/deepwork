"""
MANUAL TEST: Multiple Safety Patterns

=== WHAT THIS TESTS ===
Tests trigger/safety mode with MULTIPLE safety patterns:
- Rule fires when this file is edited alone
- Rule is suppressed if ANY of the safety files are also edited:
  - test_multi_safety_changelog.md
  - test_multi_safety_version.txt

=== TEST CASE 1: Rule SHOULD fire ===
1. Edit this file (add a comment below the marker)
2. Do NOT edit any safety files
3. Run: echo '{}' | python -m deepwork.hooks.rules_check
4. Expected: "Manual Test: Multi Safety" appears in output

=== TEST CASE 2: Rule should NOT fire (changelog edited) ===
1. Edit this file (add a comment below the marker)
2. ALSO edit test_multi_safety_changelog.md
3. Run: echo '{}' | python -m deepwork.hooks.rules_check
4. Expected: "Manual Test: Multi Safety" does NOT appear

=== TEST CASE 3: Rule should NOT fire (version edited) ===
1. Edit this file (add a comment below the marker)
2. ALSO edit test_multi_safety_version.txt
3. Run: echo '{}' | python -m deepwork.hooks.rules_check
4. Expected: "Manual Test: Multi Safety" does NOT appear

=== RULE LOCATION ===
.deepwork/rules/manual-test-multi-safety.md
"""

VERSION = "1.0.0"


def get_version():
    """Return the current version."""
    return VERSION


# Edit below this line to trigger the rule
# -------------------------------------------
