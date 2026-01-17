"""
MANUAL TEST: Multiple Safety Patterns

=== WHAT THIS TESTS ===
Tests trigger/safety mode with MULTIPLE safety patterns:
- Rule fires when this file is edited
- Rule is suppressed if ANY of the safety files are also edited:
  - test_multi_safety_changelog.md
  - test_multi_safety_version.txt

=== HOW TO TRIGGER ===
Edit this file WITHOUT editing any of the safety files

=== HOW TO SUPPRESS ===
Edit this file AND at least ONE of:
- test_multi_safety_changelog.md
- test_multi_safety_version.txt

=== EXPECTED BEHAVIOR ===
- Edit this file alone -> Rule FIRES
- Edit this file + changelog -> Rule SUPPRESSED
- Edit this file + version -> Rule SUPPRESSED
- Edit this file + both safety files -> Rule SUPPRESSED

=== RULE LOCATION ===
.deepwork/rules/manual-test-multi-safety.md
"""


VERSION = "1.0.0"


def get_version():
    """Return the current version."""
    return VERSION


# Edit below this line to trigger the rule
# -------------------------------------------
