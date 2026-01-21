"""Tests for rules_check hook module."""

import os
from unittest.mock import patch

from deepwork.core.rules_parser import (
    DetectionMode,
    PairConfig,
    PromptRuntime,
    Rule,
    RuleEvaluationResult,
)
from deepwork.hooks.rules_check import (
    extract_promise_tags,
    format_claude_prompt,
    invoke_claude_headless,
    is_claude_code_remote,
    parse_claude_response,
)


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


class TestFormatClaudePrompt:
    """Tests for format_claude_prompt function."""

    def test_formats_basic_trigger_safety_rule(self) -> None:
        """Test formatting a basic trigger/safety rule for Claude."""
        rule = Rule(
            name="Security Review",
            filename="security-review",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/auth/**/*"],
            safety=[],
            instructions="Review the code for security issues.",
            compare_to="prompt",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["src/auth/login.py"],
        )

        prompt = format_claude_prompt(result)

        assert "Security Review" in prompt
        assert "src/auth/login.py" in prompt
        assert "Review the code for security issues" in prompt
        assert "---RULE_RESULT---" in prompt
        assert 'decision: <"block" or "allow">' in prompt

    def test_formats_set_mode_rule_with_missing_files(self) -> None:
        """Test formatting a set mode rule showing missing files."""
        rule = Rule(
            name="Source/Test Pairing",
            filename="source-test-pairing",
            detection_mode=DetectionMode.SET,
            set_patterns=["src/{path}.py", "tests/{path}_test.py"],
            instructions="Update the corresponding test file.",
            compare_to="base",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["src/auth/login.py"],
            missing_files=["tests/auth/login_test.py"],
        )

        prompt = format_claude_prompt(result)

        assert "Source/Test Pairing" in prompt
        assert "src/auth/login.py" in prompt
        assert "tests/auth/login_test.py" in prompt
        assert "Expected files (not changed)" in prompt
        assert "Update the corresponding test file" in prompt

    def test_formats_pair_mode_rule(self) -> None:
        """Test formatting a pair mode rule."""
        rule = Rule(
            name="API Documentation",
            filename="api-documentation",
            detection_mode=DetectionMode.PAIR,
            pair_config=PairConfig(
                trigger="api/{path}.py",
                expects=["docs/api/{path}.md"],
            ),
            instructions="Update the API documentation.",
            compare_to="base",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["api/users.py"],
            missing_files=["docs/api/users.md"],
        )

        prompt = format_claude_prompt(result)

        assert "API Documentation" in prompt
        assert "api/users.py" in prompt
        assert "docs/api/users.md" in prompt
        assert "Update the API documentation" in prompt

    def test_includes_response_format_instructions(self) -> None:
        """Test that prompt includes response format instructions."""
        rule = Rule(
            name="Test Rule",
            filename="test-rule",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*"],
            safety=[],
            instructions="Check the code.",
            compare_to="base",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["src/main.py"],
        )

        prompt = format_claude_prompt(result)

        assert "Response Format" in prompt
        assert "---RULE_RESULT---" in prompt
        assert "---END_RULE_RESULT---" in prompt
        assert "block" in prompt
        assert "allow" in prompt

    def test_includes_transcript_path_when_provided(self) -> None:
        """Test that prompt includes transcript path when provided."""
        rule = Rule(
            name="Test Rule",
            filename="test-rule",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*"],
            safety=[],
            instructions="Check the code.",
            compare_to="base",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["src/main.py"],
        )

        prompt = format_claude_prompt(result, transcript_path="/tmp/conversation.jsonl")

        assert "Conversation Context" in prompt
        assert "/tmp/conversation.jsonl" in prompt
        assert "transcript" in prompt.lower()

    def test_omits_transcript_section_when_not_provided(self) -> None:
        """Test that prompt omits transcript section when path is None."""
        rule = Rule(
            name="Test Rule",
            filename="test-rule",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*"],
            safety=[],
            instructions="Check the code.",
            compare_to="base",
            prompt_runtime=PromptRuntime.CLAUDE,
        )
        result = RuleEvaluationResult(
            rule=rule,
            should_fire=True,
            trigger_files=["src/main.py"],
        )

        prompt = format_claude_prompt(result, transcript_path=None)

        assert "Conversation Context" not in prompt
        # But instructions and other parts should still be present
        assert "Check the code" in prompt
        assert "---RULE_RESULT---" in prompt


class TestParseClaudeResponse:
    """Tests for parse_claude_response function."""

    def test_parses_allow_decision(self) -> None:
        """Test parsing an allow decision."""
        output = """
I've reviewed the code and it looks good.

---RULE_RESULT---
decision: allow
reason: Code follows security best practices
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "allow"
        assert reason == "Code follows security best practices"

    def test_parses_block_decision(self) -> None:
        """Test parsing a block decision."""
        output = """
There are security issues in the code.

---RULE_RESULT---
decision: block
reason: Found hardcoded credentials on line 42
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "block"
        assert reason == "Found hardcoded credentials on line 42"

    def test_parses_quoted_decision(self) -> None:
        """Test parsing decision with quotes."""
        output = """
---RULE_RESULT---
decision: "allow"
reason: All tests pass
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "allow"
        assert reason == "All tests pass"

    def test_parses_single_quoted_decision(self) -> None:
        """Test parsing decision with single quotes."""
        output = """
---RULE_RESULT---
decision: 'block'
reason: Missing test coverage
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "block"
        assert reason == "Missing test coverage"

    def test_defaults_to_block_when_no_result_block(self) -> None:
        """Test defaults to block when no result block found."""
        output = "I reviewed the code but forgot to include the result block."

        decision, reason = parse_claude_response(output)

        assert decision == "block"
        assert "did not return a structured response" in reason

    def test_defaults_to_block_for_empty_output(self) -> None:
        """Test defaults to block for empty output."""
        decision, reason = parse_claude_response("")

        assert decision == "block"
        assert "did not return a structured response" in reason

    def test_handles_invalid_decision_value(self) -> None:
        """Test handles invalid decision value by defaulting to block."""
        output = """
---RULE_RESULT---
decision: maybe
reason: Not sure about this
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        # Invalid decision should default to block
        assert decision == "block"

    def test_case_insensitive_decision(self) -> None:
        """Test that decision parsing is case-insensitive."""
        output = """
---RULE_RESULT---
decision: ALLOW
reason: Everything looks good
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "allow"
        assert reason == "Everything looks good"

    def test_handles_multiline_reason(self) -> None:
        """Test handling of reason that spans context before end marker."""
        output = """
---RULE_RESULT---
decision: block
reason: Multiple issues found including security vulnerabilities
---END_RULE_RESULT---
"""
        decision, reason = parse_claude_response(output)

        assert decision == "block"
        assert "Multiple issues found" in reason

    def test_parses_result_embedded_in_longer_output(self) -> None:
        """Test parsing result block embedded in longer output."""
        output = """
I've completed the security review of the authentication code.

Here are my findings:
1. The password hashing uses bcrypt which is good
2. Input validation is properly implemented
3. No SQL injection vulnerabilities found

Overall, the code follows security best practices.

---RULE_RESULT---
decision: allow
reason: Code passes security review - no vulnerabilities found
---END_RULE_RESULT---

Let me know if you need any clarification.
"""
        decision, reason = parse_claude_response(output)

        assert decision == "allow"
        assert "passes security review" in reason


class TestIsClaudeCodeRemote:
    """Tests for is_claude_code_remote function."""

    def test_returns_true_when_env_var_is_true(self) -> None:
        """Test returns True when CLAUDE_CODE_REMOTE=true."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "true"}):
            assert is_claude_code_remote() is True

    def test_returns_true_when_env_var_is_TRUE(self) -> None:
        """Test returns True when CLAUDE_CODE_REMOTE=TRUE (case insensitive)."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "TRUE"}):
            assert is_claude_code_remote() is True

    def test_returns_false_when_env_var_is_false(self) -> None:
        """Test returns False when CLAUDE_CODE_REMOTE=false."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            assert is_claude_code_remote() is False

    def test_returns_false_when_env_var_not_set(self) -> None:
        """Test returns False when CLAUDE_CODE_REMOTE is not set."""
        env = os.environ.copy()
        env.pop("CLAUDE_CODE_REMOTE", None)
        with patch.dict(os.environ, env, clear=True):
            assert is_claude_code_remote() is False

    def test_returns_false_when_env_var_is_empty(self) -> None:
        """Test returns False when CLAUDE_CODE_REMOTE is empty."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": ""}):
            assert is_claude_code_remote() is False


class TestInvokeClaudeHeadlessFallback:
    """Tests for invoke_claude_headless fallback behavior in remote environments."""

    def test_returns_fallback_prompt_in_remote_environment(self) -> None:
        """Test returns fallback prompt when in Claude Code Remote environment."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "true"}):
            decision, reason, fallback = invoke_claude_headless(
                "Test prompt content", "Test Rule"
            )

            assert decision == "block"
            assert "manual evaluation" in reason
            assert fallback is not None
            assert "Cannot run `claude` command" in fallback
            assert "Claude Code Web" in fallback
            assert "Test prompt content" in fallback

    def test_no_fallback_in_local_environment(self) -> None:
        """Test no fallback when not in remote environment (but may fail if claude not installed)."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            # Mock subprocess to simulate claude not found
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()
                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "block"
                assert "not found" in reason
                assert fallback is None  # No fallback, actual error


class TestInvokeClaudeHeadlessExecution:
    """Tests for invoke_claude_headless subprocess execution."""

    def test_successful_allow_decision(self) -> None:
        """Test successful execution with allow decision."""
        mock_output = """
I've reviewed the code.

---RULE_RESULT---
decision: allow
reason: Code looks good
---END_RULE_RESULT---
"""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = mock_output
                mock_run.return_value.stderr = ""

                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "allow"
                assert reason == "Code looks good"
                assert fallback is None

    def test_successful_block_decision(self) -> None:
        """Test successful execution with block decision."""
        mock_output = """
Found issues in the code.

---RULE_RESULT---
decision: block
reason: Security vulnerability detected
---END_RULE_RESULT---
"""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = mock_output
                mock_run.return_value.stderr = ""

                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "block"
                assert reason == "Security vulnerability detected"
                assert fallback is None

    def test_nonzero_exit_code(self) -> None:
        """Test handling of non-zero exit code from Claude."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = "API rate limit exceeded"

                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "block"
                assert "execution failed" in reason
                assert "rate limit" in reason
                assert fallback is None

    def test_timeout_handling(self) -> None:
        """Test handling of subprocess timeout."""
        import subprocess

        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd=["claude"], timeout=300
                )

                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "block"
                assert "timed out" in reason
                assert "Test Rule" in reason
                assert fallback is None

    def test_generic_exception_handling(self) -> None:
        """Test handling of generic exceptions."""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.side_effect = OSError("Permission denied")

                decision, reason, fallback = invoke_claude_headless(
                    "Test prompt", "Test Rule"
                )

                assert decision == "block"
                assert "Error invoking Claude" in reason
                assert "Permission denied" in reason
                assert fallback is None

    def test_calls_claude_with_correct_arguments(self) -> None:
        """Test that Claude is called with the correct command-line arguments."""
        mock_output = """
---RULE_RESULT---
decision: allow
reason: OK
---END_RULE_RESULT---
"""
        with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "false"}):
            with patch("deepwork.hooks.rules_check.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = mock_output
                mock_run.return_value.stderr = ""

                invoke_claude_headless("My test prompt", "Test Rule")

                mock_run.assert_called_once()
                call_args = mock_run.call_args
                cmd = call_args[0][0]

                assert cmd[0] == "claude"
                assert "--print" in cmd
                assert "--dangerously-skip-permissions" in cmd
                assert "-p" in cmd
                assert "My test prompt" in cmd
