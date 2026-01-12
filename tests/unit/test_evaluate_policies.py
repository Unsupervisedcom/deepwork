"""Tests for the hooks evaluate_policies module."""

import pytest

from deepwork.hooks.evaluate_policies import extract_promise_tags, format_policy_message
from deepwork.core.policy_parser import Policy


class TestExtractPromiseTags:
    """Tests for extract_promise_tags function."""

    def test_extracts_double_quote_promise(self) -> None:
        """Test extracting promise with double quotes."""
        text = '<promise policy="Update Docs">addressed</promise>'
        result = extract_promise_tags(text)
        assert result == {"Update Docs"}

    def test_extracts_single_quote_promise(self) -> None:
        """Test extracting promise with single quotes."""
        text = "<promise policy='Security Review'>done</promise>"
        result = extract_promise_tags(text)
        assert result == {"Security Review"}

    def test_extracts_multiple_promises(self) -> None:
        """Test extracting multiple promise tags."""
        text = """
        I've addressed the policies.
        <promise policy="Update Docs">done</promise>
        <promise policy="Security Review">checked</promise>
        """
        result = extract_promise_tags(text)
        assert result == {"Update Docs", "Security Review"}

    def test_case_insensitive(self) -> None:
        """Test that promise tag matching is case insensitive."""
        text = '<PROMISE policy="Test Policy">done</PROMISE>'
        result = extract_promise_tags(text)
        assert result == {"Test Policy"}

    def test_returns_empty_set_for_no_promises(self) -> None:
        """Test that empty set is returned when no promises found."""
        text = "This is just some regular text without any promise tags."
        result = extract_promise_tags(text)
        assert result == set()

    def test_multiline_promise_content(self) -> None:
        """Test promise tag with multiline content."""
        text = '''<promise policy="Complex Policy">
        I have addressed this by:
        1. Updating the docs
        2. Running tests
        </promise>'''
        result = extract_promise_tags(text)
        assert result == {"Complex Policy"}


class TestFormatPolicyMessage:
    """Tests for format_policy_message function."""

    def test_formats_single_policy(self) -> None:
        """Test formatting a single policy."""
        policies = [
            Policy(
                name="Test Policy",
                triggers=["src/*"],
                safety=[],
                instructions="Please update the documentation.",
            )
        ]
        result = format_policy_message(policies)

        assert "## Policies Triggered" in result
        assert "### Policy: Test Policy" in result
        assert "Please update the documentation." in result
        assert '<promise policy="Policy Name">' in result

    def test_formats_multiple_policies(self) -> None:
        """Test formatting multiple policies."""
        policies = [
            Policy(
                name="Policy 1",
                triggers=["src/*"],
                safety=[],
                instructions="Do thing 1.",
            ),
            Policy(
                name="Policy 2",
                triggers=["test/*"],
                safety=[],
                instructions="Do thing 2.",
            ),
        ]
        result = format_policy_message(policies)

        assert "### Policy: Policy 1" in result
        assert "### Policy: Policy 2" in result
        assert "Do thing 1." in result
        assert "Do thing 2." in result

    def test_strips_instruction_whitespace(self) -> None:
        """Test that instruction whitespace is stripped."""
        policies = [
            Policy(
                name="Test",
                triggers=["*"],
                safety=[],
                instructions="  \n  Instructions here  \n  ",
            )
        ]
        result = format_policy_message(policies)

        # Should be stripped but present
        assert "Instructions here" in result
