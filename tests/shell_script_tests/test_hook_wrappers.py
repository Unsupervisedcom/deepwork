"""Tests for the platform hook wrapper shell scripts.

These tests verify that claude_hook.sh and gemini_hook.sh correctly
invoke Python hooks and handle input/output.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def hooks_dir() -> Path:
    """Return the path to the hooks directory."""
    return Path(__file__).parent.parent.parent / "src" / "deepwork" / "hooks"


@pytest.fixture
def src_dir() -> Path:
    """Return the path to the src directory for PYTHONPATH."""
    return Path(__file__).parent.parent.parent / "src"


def run_hook_script(
    script_path: Path,
    python_module: str,
    hook_input: dict,
    platform: str,
    src_dir: Path,
) -> tuple[str, str, int]:
    """
    Run a hook wrapper script with the given input.

    Args:
        script_path: Path to the wrapper script (claude_hook.sh or gemini_hook.sh)
        python_module: Python module to invoke
        hook_input: JSON input to pass via stdin
        platform: Platform identifier for env var
        src_dir: Path to src directory for PYTHONPATH

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    env["DEEPWORK_HOOK_PLATFORM"] = platform

    result = subprocess.run(
        ["bash", str(script_path), python_module],
        capture_output=True,
        text=True,
        input=json.dumps(hook_input),
        env=env,
    )

    return result.stdout, result.stderr, result.returncode


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
        # Create a simple test module that outputs the platform env var
        # We'll use a Python one-liner via -c
        script_path = hooks_dir / "claude_hook.sh"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_dir)

        # We can't easily test this without a real module, so we'll verify
        # the script exists and has the right content
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


class TestRulesCheckHook:
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
