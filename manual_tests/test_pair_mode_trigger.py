"""
MANUAL TEST: Pair Mode (Directional Correspondence)

=== WHAT THIS TESTS ===
Tests the "pair" detection mode where there's a ONE-WAY relationship:
- This file is the TRIGGER
- test_pair_mode_expected.md is the EXPECTED file
- When THIS file changes, the expected file MUST also change
- But the expected file CAN change independently (no rule fires)

=== HOW TO TRIGGER ===
Edit this file WITHOUT editing test_pair_mode_expected.md

=== HOW TO VERIFY ONE-WAY BEHAVIOR ===
Edit ONLY test_pair_mode_expected.md -> Rule should NOT fire
(This is the key difference from "set" mode)

=== EXPECTED BEHAVIOR ===
- Edit this file alone -> Rule FIRES (trigger without expected)
- Edit expected file alone -> Rule does NOT fire (expected can change alone)
- Edit BOTH files -> Rule is satisfied (no fire)

=== RULE LOCATION ===
.deepwork/rules/manual-test-pair-mode.md
"""


def api_endpoint():
    """
    An API endpoint that requires documentation.

    This simulates an API file where changes require
    documentation updates, but docs can be updated
    independently (for typos, clarifications, etc.)
    """
    return {"status": "ok", "message": "API response"}


# Edit below this line to trigger the rule
# -------------------------------------------
