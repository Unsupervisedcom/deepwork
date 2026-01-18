"""Tests for rules_check hook module."""

import pytest

from deepwork.hooks.rules_check import extract_promise_tags


class TestExtractPromiseTags:
    """Tests for extract_promise_tags function."""

    def test_extracts_simple_promise(self) -> None:
        """Test extracting a simple promise tag."""
        text = "I've reviewed this. <promise>Rule Name</promise>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_extracts_promise_with_checkmark(self) -> None:
        """Test extracting promise tag with checkmark prefix."""
        text = "Done. <promise>✓ Rule Name</promise>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_extracts_promise_with_checkmark_no_space(self) -> None:
        """Test extracting promise tag with checkmark but no space."""
        text = "<promise>✓Rule Name</promise>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_extracts_multiple_promises(self) -> None:
        """Test extracting multiple promise tags."""
        text = """
        <promise>Rule One</promise>
        <promise>✓ Rule Two</promise>
        <promise>Rule Three</promise>
        """
        result = extract_promise_tags(text)
        assert result == {"Rule One", "Rule Two", "Rule Three"}

    def test_case_insensitive_tag(self) -> None:
        """Test that promise tags are case-insensitive."""
        text = "<PROMISE>Rule Name</PROMISE>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_preserves_rule_name_case(self) -> None:
        """Test that rule name case is preserved."""
        text = "<promise>Architecture Documentation Accuracy</promise>"
        result = extract_promise_tags(text)
        assert result == {"Architecture Documentation Accuracy"}

    def test_handles_whitespace_in_tag(self) -> None:
        """Test handling of whitespace around rule name."""
        text = "<promise>  Rule Name  </promise>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_handles_newlines_in_tag(self) -> None:
        """Test handling of newlines in promise tag."""
        text = "<promise>\n  Rule Name\n</promise>"
        result = extract_promise_tags(text)
        assert result == {"Rule Name"}

    def test_returns_empty_set_for_no_promises(self) -> None:
        """Test that empty set is returned when no promises exist."""
        text = "No promises here."
        result = extract_promise_tags(text)
        assert result == set()

    def test_handles_empty_string(self) -> None:
        """Test handling of empty string."""
        result = extract_promise_tags("")
        assert result == set()

    def test_real_world_command_error_promise(self) -> None:
        """Test promise format shown in command error output."""
        # This is the exact format shown to agents when a command rule fails
        text = "<promise>✓ Manual Test: Infinite Block Command</promise>"
        result = extract_promise_tags(text)
        assert result == {"Manual Test: Infinite Block Command"}

    def test_mixed_formats_in_same_text(self) -> None:
        """Test extracting both checkmark and non-checkmark promises."""
        text = """
        <promise>Rule Without Checkmark</promise>
        <promise>✓ Rule With Checkmark</promise>
        """
        result = extract_promise_tags(text)
        assert result == {"Rule Without Checkmark", "Rule With Checkmark"}

    def test_promise_with_special_characters_in_name(self) -> None:
        """Test promise with special characters in rule name."""
        text = "<promise>Source/Test Pairing</promise>"
        result = extract_promise_tags(text)
        assert result == {"Source/Test Pairing"}

    def test_promise_embedded_in_markdown(self) -> None:
        """Test promise tag embedded in markdown text."""
        text = """
        I've reviewed the documentation and it's accurate.

        <promise>Architecture Documentation Accuracy</promise>
        <promise>README Accuracy</promise>

        The changes were purely cosmetic.
        """
        result = extract_promise_tags(text)
        assert result == {"Architecture Documentation Accuracy", "README Accuracy"}
