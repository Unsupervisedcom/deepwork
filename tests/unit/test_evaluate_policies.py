"""Tests for the hooks evaluate_policies module."""

from deepwork.core.policy_parser import PolicyV1
from deepwork.hooks.evaluate_policies import extract_promise_tags, format_policy_message


class TestExtractPromiseTags:
    """Tests for extract_promise_tags function."""

    def test_extracts_policy_name_from_promise(self) -> None:
        """Test extracting policy name from promise tag body."""
        text = "<promise>✓ Update Docs</promise>"
        result = extract_promise_tags(text)
        assert result == {"Update Docs"}

    def test_extracts_multiple_promises(self) -> None:
        """Test extracting multiple promise tags."""
        text = """
        I've addressed the policies.
        <promise>✓ Update Docs</promise>
        <promise>✓ Security Review</promise>
        """
        result = extract_promise_tags(text)
        assert result == {"Update Docs", "Security Review"}

    def test_case_insensitive(self) -> None:
        """Test that promise tag matching is case insensitive."""
        text = "<PROMISE>✓ Test Policy</PROMISE>"
        result = extract_promise_tags(text)
        assert result == {"Test Policy"}

    def test_returns_empty_set_for_no_promises(self) -> None:
        """Test that empty set is returned when no promises found."""
        text = "This is just some regular text without any promise tags."
        result = extract_promise_tags(text)
        assert result == set()

    def test_strips_whitespace_from_policy_name(self) -> None:
        """Test that whitespace is stripped from extracted policy names."""
        text = "<promise>✓   Policy With Spaces   </promise>"
        result = extract_promise_tags(text)
        assert result == {"Policy With Spaces"}


class TestFormatPolicyMessage:
    """Tests for format_policy_message function."""

    def test_formats_single_policy(self) -> None:
        """Test formatting a single policy."""
        policies = [
            PolicyV1(
                name="Test Policy",
                triggers=["src/*"],
                safety=[],
                instructions="Please update the documentation.",
            )
        ]
        result = format_policy_message(policies)

        assert "## DeepWork Policies Triggered" in result
        assert "### Policy: Test Policy" in result
        assert "Please update the documentation." in result
        assert "<promise>✓ Policy Name</promise>" in result

    def test_formats_multiple_policies(self) -> None:
        """Test formatting multiple policies."""
        policies = [
            PolicyV1(
                name="Policy 1",
                triggers=["src/*"],
                safety=[],
                instructions="Do thing 1.",
            ),
            PolicyV1(
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
            PolicyV1(
                name="Test",
                triggers=["*"],
                safety=[],
                instructions="  \n  Instructions here  \n  ",
            )
        ]
        result = format_policy_message(policies)

        # Should be stripped but present
        assert "Instructions here" in result
