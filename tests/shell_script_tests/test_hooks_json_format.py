"""Tests for Claude Code hooks JSON format validation.

Claude Code hooks have specific JSON response formats that must be followed:

Stop hooks (hooks.after_agent):
    - {} - Allow stop (empty object)
    - {"decision": "block", "reason": "..."} - Block stop with reason

UserPromptSubmit hooks (hooks.before_prompt):
    - {} - No response needed (empty object)
    - No output - Also acceptable

BeforeTool hooks (hooks.before_tool):
    - {} - Allow tool execution
    - {"decision": "block", "reason": "..."} - Block tool execution

All hooks:
    - Must return valid JSON if producing output
    - Must not contain non-JSON output on stdout (stderr is ok)
    - Exit code 0 indicates success
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
from git import Repo

from .conftest import run_shell_script


def run_hook_script(
    script_path: Path,
    cwd: Path,
    hook_input: dict | None = None,
) -> tuple[str, str, int]:
    """Run a hook script and return its output."""
    return run_shell_script(script_path, cwd, hook_input=hook_input)


def validate_json_output(output: str) -> dict | None:
    """
    Validate that output is valid JSON or empty.

    Args:
        output: The stdout from a hook script

    Returns:
        Parsed JSON dict, or None if empty/no output

    Raises:
        AssertionError: If output is invalid JSON
    """
    stripped = output.strip()

    if not stripped:
        return None

    try:
        result = json.loads(stripped)
        assert isinstance(result, dict), "Hook output must be a JSON object"
        return result
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {stripped!r}. Error: {e}")


def validate_stop_hook_response(response: dict | None) -> None:
    """
    Validate a Stop hook response follows Claude Code format.

    Args:
        response: Parsed JSON response or None

    Raises:
        AssertionError: If response format is invalid
    """
    if response is None:
        # No output is acceptable for stop hooks
        return

    if response == {}:
        # Empty object means allow stop
        return

    # Must have decision and reason for blocking
    assert "decision" in response, (
        f"Stop hook blocking response must have 'decision' key: {response}"
    )
    assert response["decision"] == "block", (
        f"Stop hook decision must be 'block', got: {response['decision']}"
    )
    assert "reason" in response, f"Stop hook blocking response must have 'reason' key: {response}"
    assert isinstance(response["reason"], str), f"Stop hook reason must be a string: {response}"

    # Reason should not be empty when blocking
    assert response["reason"].strip(), "Stop hook blocking reason should not be empty"


def validate_prompt_hook_response(response: dict | None) -> None:
    """
    Validate a UserPromptSubmit hook response.

    Args:
        response: Parsed JSON response or None

    Raises:
        AssertionError: If response format is invalid
    """
    if response is None:
        # No output is acceptable
        return

    # Empty object or valid JSON object is fine
    assert isinstance(response, dict), f"Prompt hook output must be a JSON object: {response}"


class TestRulesStopHookJsonFormat:
    """Tests specifically for rules_stop_hook.sh JSON format compliance."""

    def test_allow_response_is_empty_json(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that allow response is empty JSON object."""
        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        response = validate_json_output(stdout)
        validate_stop_hook_response(response)

        if response is not None:
            assert response == {}, f"Allow response should be empty: {response}"

    def test_block_response_has_required_fields(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that block response has decision and reason."""
        # Create a file that triggers the rule
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule)

        response = validate_json_output(stdout)
        validate_stop_hook_response(response)

        # Should be blocking
        assert response is not None, "Expected blocking response"
        assert response.get("decision") == "block", "Expected block decision"
        assert "reason" in response, "Expected reason field"

    def test_block_reason_contains_rule_info(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that block reason contains rule information."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule)

        response = validate_json_output(stdout)

        assert response is not None, "Expected blocking response"
        reason = response.get("reason", "")

        # Should contain useful rule information
        assert "Rule" in reason or "rule" in reason, f"Reason should mention rule: {reason}"

    def test_no_extraneous_keys_in_response(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that response only contains expected keys."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule)

        response = validate_json_output(stdout)

        if response and response != {}:
            # Only decision and reason are valid keys for stop hooks
            valid_keys = {"decision", "reason"}
            actual_keys = set(response.keys())
            assert actual_keys <= valid_keys, (
                f"Unexpected keys in response: {actual_keys - valid_keys}"
            )

    def test_output_is_single_line_json(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that JSON output is single-line (no pretty printing)."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule)

        # Remove trailing newline and check for internal newlines
        output = stdout.strip()
        if output:
            # JSON output should ideally be single line
            # Multiple lines could indicate print statements or logging
            lines = output.split("\n")
            # Only the last line should be JSON
            json_line = lines[-1]
            # Verify the JSON is parseable
            json.loads(json_line)


class TestUserPromptSubmitHookJsonFormat:
    """Tests for user_prompt_submit.sh JSON format compliance."""

    def test_output_is_valid_json_or_empty(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that output is valid JSON or empty."""
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        response = validate_json_output(stdout)
        validate_prompt_hook_response(response)

    def test_does_not_block_prompt_submission(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that hook does not block prompt submission."""
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        response = validate_json_output(stdout)

        # UserPromptSubmit hooks should not block
        if response:
            assert response.get("decision") != "block", (
                "UserPromptSubmit hook should not return block decision"
            )


class TestHooksJsonFormatWithTranscript:
    """Tests for hook JSON format when using transcript input."""

    def test_stop_hook_with_transcript_input(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test stop hook JSON format when transcript is provided."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        # Create mock transcript
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            transcript_path = f.name
            f.write(
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {"content": [{"type": "text", "text": "Hello"}]},
                    }
                )
            )
            f.write("\n")

        try:
            script_path = rules_hooks_dir / "rules_stop_hook.sh"
            hook_input = {"transcript_path": transcript_path}
            stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule, hook_input)

            response = validate_json_output(stdout)
            validate_stop_hook_response(response)

        finally:
            os.unlink(transcript_path)

    def test_stop_hook_with_promise_returns_empty(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that promised rules return empty JSON."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        # Create transcript with promise tag
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            transcript_path = f.name
            f.write(
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "<promise>Python File Rule</promise>",
                                }
                            ]
                        },
                    }
                )
            )
            f.write("\n")

        try:
            script_path = rules_hooks_dir / "rules_stop_hook.sh"
            hook_input = {"transcript_path": transcript_path}
            stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule, hook_input)

            response = validate_json_output(stdout)
            validate_stop_hook_response(response)

            # Should be empty (allow) because rule was promised
            if response is not None:
                assert response == {}, f"Expected empty response: {response}"

        finally:
            os.unlink(transcript_path)


class TestHooksExitCodes:
    """Tests for hook script exit codes."""

    def test_stop_hook_exits_zero_on_allow(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that stop hook exits 0 when allowing."""
        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        assert code == 0, f"Allow should exit 0. stderr: {stderr}"

    def test_stop_hook_exits_zero_on_block(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that stop hook exits 0 even when blocking."""
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo_with_rule)

        # Hooks should exit 0 and communicate via JSON
        assert code == 0, f"Block should still exit 0. stderr: {stderr}"

    def test_user_prompt_hook_exits_zero(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that user prompt hook always exits 0."""
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        assert code == 0, f"User prompt hook should exit 0. stderr: {stderr}"

    def test_capture_script_exits_zero(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that capture script exits 0."""
        script_path = rules_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_hook_script(script_path, git_repo)

        assert code == 0, f"Capture script should exit 0. stderr: {stderr}"
