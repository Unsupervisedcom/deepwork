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
from pathlib import Path

import pytest

# =============================================================================
# Helper Functions
# =============================================================================


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


