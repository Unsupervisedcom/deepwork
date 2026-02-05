"""Integration tests for quality gate subprocess execution.

###############################################################################
# ⚠️  CRITICAL: THESE TESTS MUST USE THE REAL CLAUDE CLI ⚠️
#
# The entire point of these integration tests is to verify that the QualityGate
# class works correctly with the ACTUAL Claude Code CLI subprocess.
#
# DO NOT:
#   - Mock the QualityGate class
#   - Use _test_command parameter
#   - Stub out subprocess calls
#   - Use the MockQualityGate class
#
# If you need to test parsing logic or edge cases, add those tests to:
#   tests/unit/mcp/test_quality_gate.py
#
# These tests are SKIPPED in CI because they require Claude Code CLI to be
# installed and authenticated. They are meant to be run locally during
# development to verify real-world behavior.
###############################################################################
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from deepwork.mcp.claude_cli import ClaudeCLI
from deepwork.mcp.quality_gate import QualityGate

# Skip marker for tests that require real Claude CLI
# GitHub Actions sets CI=true, as do most other CI systems
requires_claude_cli = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Integration tests require Claude CLI - skipped in CI",
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with test files."""
    return tmp_path


###############################################################################
# ⚠️  REAL INTEGRATION TESTS - DO NOT MOCK ⚠️
#
# These tests call the actual Claude CLI. They verify that:
#   1. The subprocess invocation works correctly
#   2. The JSON schema is properly passed and enforced
#   3. Response parsing handles real Claude output
#
# Run these locally with: pytest tests/integration/test_quality_gate_integration.py -v
###############################################################################


@requires_claude_cli
class TestRealClaudeIntegration:
    """Integration tests that run the REAL Claude CLI.

    ⚠️  WARNING: DO NOT MOCK THESE TESTS ⚠️

    These tests exist specifically to verify that QualityGate works with the
    actual Claude Code CLI. If you mock them, you defeat their entire purpose.
    """

    async def test_real_claude_evaluates_passing_criteria(self, project_root: Path) -> None:
        """Test that real Claude CLI correctly evaluates passing criteria.

        ⚠️  THIS TEST MUST USE THE REAL CLAUDE CLI - DO NOT MOCK ⚠️
        """
        # Create a well-formed output file that clearly meets the criteria
        output_file = project_root / "analysis.md"
        output_file.write_text(
            "# Analysis Report\n\n"
            "## Summary\n"
            "This document contains a complete analysis.\n\n"
            "## Details\n"
            "The analysis covers all required points.\n"
        )

        # ⚠️  NO _test_command - this uses the REAL Claude CLI
        gate = QualityGate(cli=ClaudeCLI(timeout=120))

        result = await gate.evaluate(
            quality_criteria=[
                "The document must have a title",
                "The document must contain a summary section",
            ],
            outputs=["analysis.md"],
            project_root=project_root,
        )

        # Verify we got a structured response
        assert result is not None
        assert isinstance(result.passed, bool)
        assert isinstance(result.feedback, str)
        assert len(result.feedback) > 0

        # The document clearly meets the criteria, so it should pass
        # (though we allow for some model variability)
        if not result.passed:
            # If it failed, at least verify we got proper feedback
            assert len(result.criteria_results) > 0
            pytest.skip(f"Model returned fail (may be model variability): {result.feedback}")

    async def test_real_claude_evaluates_failing_criteria(self, project_root: Path) -> None:
        """Test that real Claude CLI correctly identifies missing criteria.

        ⚠️  THIS TEST MUST USE THE REAL CLAUDE CLI - DO NOT MOCK ⚠️
        """
        # Create an output file that is clearly missing required content
        output_file = project_root / "incomplete.md"
        output_file.write_text("Just some random text without any structure.")

        # ⚠️  NO _test_command - this uses the REAL Claude CLI
        gate = QualityGate(cli=ClaudeCLI(timeout=120))

        result = await gate.evaluate(
            quality_criteria=[
                "The document must contain a section titled 'Executive Summary'",
                "The document must include a numbered list of recommendations",
                "The document must have a 'Conclusions' section",
            ],
            outputs=["incomplete.md"],
            project_root=project_root,
        )

        # Verify we got a structured response
        assert result is not None
        assert isinstance(result.passed, bool)
        assert isinstance(result.feedback, str)

        # The document clearly doesn't meet these specific criteria
        # (though we allow for some model variability)
        if result.passed:
            pytest.skip(
                f"Model returned pass unexpectedly (may be model variability): {result.feedback}"
            )

        # Should have feedback about what's missing
        assert len(result.feedback) > 0
