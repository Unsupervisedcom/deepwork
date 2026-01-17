"""Tests for hook shell scripts and JSON format compliance.

# ******************************************************************************
# ***                         CRITICAL CONTRACT TESTS                        ***
# ******************************************************************************
#
# These tests verify the EXACT format required by Claude Code hooks as
# documented in: doc/platforms/claude/hooks_system.md
#
# DO NOT MODIFY these tests without first consulting the official Claude Code
# documentation at: https://docs.anthropic.com/en/docs/claude-code/hooks
#
# Hook Contract Summary:
#   - Exit code 0: Success, stdout parsed as JSON
#   - Exit code 2: Blocking error, stderr shown (NOT used for JSON format)
#   - Allow response: {} (empty JSON object)
#   - Block response: {"decision": "block", "reason": "..."}
#
# CRITICAL: Hooks using JSON output format MUST return exit code 0.
# The "decision" field in the JSON controls blocking behavior, NOT the exit code.
#
# ******************************************************************************

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
import subprocess
import tempfile
from pathlib import Path

import pytest
from git import Repo

from .conftest import run_shell_script


# =============================================================================
# Helper Functions
# =============================================================================


def run_rules_hook_script(
    script_path: Path,
    cwd: Path,
    hook_input: dict | None = None,
) -> tuple[str, str, int]:
    """Run a rules hook script and return its output."""
    return run_shell_script(script_path, cwd, hook_input=hook_input)


def run_platform_wrapper_script(
    script_path: Path,
    python_module: str,
    hook_input: dict,
    src_dir: Path,
) -> tuple[str, str, int]:
    """
    Run a platform hook wrapper script with the given input.

    Args:
        script_path: Path to the wrapper script (claude_hook.sh or gemini_hook.sh)
        python_module: Python module to invoke
        hook_input: JSON input to pass via stdin
        src_dir: Path to src directory for PYTHONPATH

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)

    result = subprocess.run(
        ["bash", str(script_path), python_module],
        capture_output=True,
        text=True,
        input=json.dumps(hook_input),
        env=env,
    )

    return result.stdout, result.stderr, result.returncode


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


# ******************************************************************************
# *** DO NOT EDIT THIS FUNCTION! ***
# As documented in doc/platforms/claude/hooks_system.md, Stop hooks must return:
#   - {} (empty object) to allow
#   - {"decision": "block", "reason": "..."} to block
# Any other format will cause undefined behavior in Claude Code.
# ******************************************************************************
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


# =============================================================================
# Platform Wrapper Script Tests
# =============================================================================


class TestClaudeHookWrapper:
    """Tests for claude_hook.sh wrapper script."""

    def test_script_exists_and_is_executable(self, hooks_dir: Path) -> None:
        """Test that the Claude hook script exists and is executable."""
        script_path = hooks_dir / "claude_hook.sh"
        assert script_path.exists(), "claude_hook.sh should exist"
        assert os.access(script_path, os.X_OK), "claude_hook.sh should be executable"

    def test_usage_error_without_module(self, hooks_dir: Path, src_dir: Path) -> None:
        """Test that script shows usage error when no module provided."""
        script_path = hooks_dir / "claude_hook.sh"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_dir)

        result = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_sets_platform_environment_variable(self, hooks_dir: Path, src_dir: Path) -> None:
        """Test that the script sets DEEPWORK_HOOK_PLATFORM correctly."""
        script_path = hooks_dir / "claude_hook.sh"
        content = script_path.read_text()
        assert 'DEEPWORK_HOOK_PLATFORM="claude"' in content


class TestGeminiHookWrapper:
    """Tests for gemini_hook.sh wrapper script."""

    def test_script_exists_and_is_executable(self, hooks_dir: Path) -> None:
        """Test that the Gemini hook script exists and is executable."""
        script_path = hooks_dir / "gemini_hook.sh"
        assert script_path.exists(), "gemini_hook.sh should exist"
        assert os.access(script_path, os.X_OK), "gemini_hook.sh should be executable"

    def test_usage_error_without_module(self, hooks_dir: Path, src_dir: Path) -> None:
        """Test that script shows usage error when no module provided."""
        script_path = hooks_dir / "gemini_hook.sh"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_dir)

        result = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_sets_platform_environment_variable(self, hooks_dir: Path, src_dir: Path) -> None:
        """Test that the script sets DEEPWORK_HOOK_PLATFORM correctly."""
        script_path = hooks_dir / "gemini_hook.sh"
        content = script_path.read_text()
        assert 'DEEPWORK_HOOK_PLATFORM="gemini"' in content


# =============================================================================
# Rules Hook Script Tests
# =============================================================================


class TestRulesStopHook:
    """Tests for rules_stop_hook.sh JSON format compliance."""

    def test_allow_response_is_empty_json(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that allow response is empty JSON object."""
        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

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
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule)

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
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule)

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
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule)

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
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule)

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


class TestUserPromptSubmitHook:
    """Tests for user_prompt_submit.sh JSON format compliance."""

    def test_output_is_valid_json_or_empty(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that output is valid JSON or empty."""
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

        response = validate_json_output(stdout)
        validate_prompt_hook_response(response)

    def test_does_not_block_prompt_submission(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that hook does not block prompt submission."""
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

        response = validate_json_output(stdout)

        # UserPromptSubmit hooks should not block
        if response:
            assert response.get("decision") != "block", (
                "UserPromptSubmit hook should not return block decision"
            )


class TestHooksWithTranscript:
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
            stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule, hook_input)

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
            stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule, hook_input)

            response = validate_json_output(stdout)
            validate_stop_hook_response(response)

            # Should be empty (allow) because rule was promised
            if response is not None:
                assert response == {}, f"Expected empty response: {response}"

        finally:
            os.unlink(transcript_path)


# ******************************************************************************
# ***                    DO NOT EDIT THESE EXIT CODE TESTS!                  ***
# ******************************************************************************
#
# As documented in doc/platforms/claude/hooks_system.md:
#
#   | Exit Code | Meaning         | Behavior                          |
#   |-----------|-----------------|-----------------------------------|
#   | 0         | Success         | stdout parsed as JSON             |
#   | 2         | Blocking error  | stderr shown, operation blocked   |
#   | Other     | Warning         | stderr logged, continues          |
#
# CRITICAL: Hooks using JSON output format MUST return exit code 0.
# The "decision" field in the JSON controls blocking behavior, NOT the exit code.
#
# Example valid outputs:
#   Exit 0 + stdout: {}                                      -> Allow
#   Exit 0 + stdout: {"decision": "block", "reason": "..."}  -> Block
#   Exit 0 + stdout: {"decision": "deny", "reason": "..."}   -> Block (Gemini)
#
# See: https://docs.anthropic.com/en/docs/claude-code/hooks
# ******************************************************************************


class TestHookExitCodes:
    """Tests for hook script exit codes.

    CRITICAL: These tests verify the documented Claude Code hook contract.
    All hooks MUST exit 0 when using JSON output format.
    """

    def test_stop_hook_exits_zero_on_allow(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that stop hook exits 0 when allowing.

        DO NOT CHANGE THIS TEST - it verifies the documented hook contract.
        """
        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

        assert code == 0, f"Allow should exit 0. stderr: {stderr}"

    def test_stop_hook_exits_zero_on_block(
        self, rules_hooks_dir: Path, git_repo_with_rule: Path
    ) -> None:
        """Test that stop hook exits 0 even when blocking.

        DO NOT CHANGE THIS TEST - it verifies the documented hook contract.
        Blocking is communicated via JSON {"decision": "block"}, NOT via exit code.
        """
        py_file = git_repo_with_rule / "test.py"
        py_file.write_text("# Python file\n")
        repo = Repo(git_repo_with_rule)
        repo.index.add(["test.py"])

        script_path = rules_hooks_dir / "rules_stop_hook.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo_with_rule)

        # Hooks should exit 0 and communicate via JSON
        assert code == 0, f"Block should still exit 0. stderr: {stderr}"

    def test_user_prompt_hook_exits_zero(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that user prompt hook always exits 0.

        DO NOT CHANGE THIS TEST - it verifies the documented hook contract.
        """
        script_path = rules_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

        assert code == 0, f"User prompt hook should exit 0. stderr: {stderr}"

    def test_capture_script_exits_zero(self, rules_hooks_dir: Path, git_repo: Path) -> None:
        """Test that capture script exits 0.

        DO NOT CHANGE THIS TEST - it verifies the documented hook contract.
        """
        script_path = rules_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_rules_hook_script(script_path, git_repo)

        assert code == 0, f"Capture script should exit 0. stderr: {stderr}"


# =============================================================================
# Integration Tests
# =============================================================================


class TestHookWrapperIntegration:
    """Integration tests for hook wrappers with actual Python hooks."""

    @pytest.fixture
    def test_hook_module(self, tmp_path: Path) -> tuple[Path, str]:
        """Create a temporary test hook module."""
        module_dir = tmp_path / "test_hooks"
        module_dir.mkdir(parents=True)

        # Create __init__.py
        (module_dir / "__init__.py").write_text("")

        # Create the hook module
        hook_code = '''
"""Test hook module."""
import os
import sys

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    run_hook,
)


def test_hook(hook_input: HookInput) -> HookOutput:
    """Test hook that blocks for after_agent events."""
    if hook_input.event == NormalizedEvent.AFTER_AGENT:
        return HookOutput(decision="block", reason="Test block reason")
    return HookOutput()


def main() -> None:
    platform_str = os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude")
    try:
        platform = Platform(platform_str)
    except ValueError:
        platform = Platform.CLAUDE

    exit_code = run_hook(test_hook, platform)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
'''
        (module_dir / "test_hook.py").write_text(hook_code)

        return tmp_path, "test_hooks.test_hook"

    def test_claude_wrapper_with_stop_event(
        self,
        hooks_dir: Path,
        src_dir: Path,
        test_hook_module: tuple[Path, str],
    ) -> None:
        """Test Claude wrapper processes Stop event correctly."""
        tmp_path, module_name = test_hook_module
        script_path = hooks_dir / "claude_hook.sh"

        hook_input = {
            "session_id": "test123",
            "hook_event_name": "Stop",
            "cwd": "/project",
        }

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{src_dir}:{tmp_path}"

        result = subprocess.run(
            ["bash", str(script_path), module_name],
            capture_output=True,
            text=True,
            input=json.dumps(hook_input),
            env=env,
        )

        # Exit code 0 even when blocking - the JSON decision field controls behavior
        assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"

        output = json.loads(result.stdout.strip())
        assert output["decision"] == "block"
        assert "Test block reason" in output["reason"]

    def test_gemini_wrapper_with_afteragent_event(
        self,
        hooks_dir: Path,
        src_dir: Path,
        test_hook_module: tuple[Path, str],
    ) -> None:
        """Test Gemini wrapper processes AfterAgent event correctly."""
        tmp_path, module_name = test_hook_module
        script_path = hooks_dir / "gemini_hook.sh"

        hook_input = {
            "session_id": "test456",
            "hook_event_name": "AfterAgent",
            "cwd": "/project",
        }

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{src_dir}:{tmp_path}"

        result = subprocess.run(
            ["bash", str(script_path), module_name],
            capture_output=True,
            text=True,
            input=json.dumps(hook_input),
            env=env,
        )

        # Exit code 0 even when blocking - the JSON decision field controls behavior
        assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"

        output = json.loads(result.stdout.strip())
        # Gemini should get "deny" instead of "block"
        assert output["decision"] == "deny"
        assert "Test block reason" in output["reason"]

    def test_non_blocking_event(
        self,
        hooks_dir: Path,
        src_dir: Path,
        test_hook_module: tuple[Path, str],
    ) -> None:
        """Test that non-blocking events return exit code 0."""
        tmp_path, module_name = test_hook_module
        script_path = hooks_dir / "claude_hook.sh"

        # SessionStart is not blocked by the test hook
        hook_input = {
            "session_id": "test789",
            "hook_event_name": "SessionStart",
            "cwd": "/project",
        }

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{src_dir}:{tmp_path}"

        result = subprocess.run(
            ["bash", str(script_path), module_name],
            capture_output=True,
            text=True,
            input=json.dumps(hook_input),
            env=env,
        )

        assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output == {} or output.get("decision", "") not in ("block", "deny")


# =============================================================================
# Python Module Tests
# =============================================================================


class TestRulesCheckModule:
    """Tests for the rules_check hook module."""

    def test_module_imports(self) -> None:
        """Test that the rules_check module can be imported."""
        from deepwork.hooks import rules_check

        assert hasattr(rules_check, "main")
        assert hasattr(rules_check, "rules_check_hook")

    def test_hook_function_returns_output(self) -> None:
        """Test that rules_check_hook returns a HookOutput."""
        from deepwork.hooks.rules_check import rules_check_hook
        from deepwork.hooks.wrapper import HookInput, HookOutput, NormalizedEvent, Platform

        # Create a minimal hook input
        hook_input = HookInput(
            platform=Platform.CLAUDE,
            event=NormalizedEvent.BEFORE_PROMPT,  # Not after_agent, so no blocking
            session_id="test",
        )

        output = rules_check_hook(hook_input)

        assert isinstance(output, HookOutput)
        # Should not block for before_prompt event
        assert output.decision != "block"
