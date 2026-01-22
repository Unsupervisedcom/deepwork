"""Tests for command executor (CMD-5.x from test_scenarios.md)."""

from pathlib import Path

from deepwork.core.command_executor import (
    CommandResult,
    all_commands_succeeded,
    execute_command,
    format_command_errors,
    run_command_action,
    substitute_command_variables,
)
from deepwork.core.rules_parser import CommandAction


class TestSubstituteCommandVariables:
    """Tests for command variable substitution."""

    def test_single_file_substitution(self) -> None:
        """Substitute {file} variable."""
        result = substitute_command_variables(
            "ruff format {file}",
            file="src/main.py",
        )
        assert result == "ruff format src/main.py"

    def test_multiple_files_substitution(self) -> None:
        """Substitute {files} variable."""
        result = substitute_command_variables(
            "eslint --fix {files}",
            files=["a.js", "b.js", "c.js"],
        )
        assert result == "eslint --fix a.js b.js c.js"

    def test_repo_root_substitution(self) -> None:
        """Substitute {repo_root} variable."""
        result = substitute_command_variables(
            "cd {repo_root} && pytest",
            repo_root=Path("/home/user/project"),
        )
        assert result == "cd /home/user/project && pytest"

    def test_all_variables(self) -> None:
        """Substitute all variables together."""
        result = substitute_command_variables(
            "{repo_root}/scripts/process.sh {file} {files}",
            file="main.py",
            files=["a.py", "b.py"],
            repo_root=Path("/project"),
        )
        assert result == "/project/scripts/process.sh main.py a.py b.py"


class TestExecuteCommand:
    """Tests for command execution."""

    def test_successful_command(self) -> None:
        """CMD-5.3.1: Exit code 0 - success."""
        result = execute_command("echo hello")
        assert result.success is True
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_failed_command(self) -> None:
        """CMD-5.3.2: Exit code 1 - failure."""
        result = execute_command("exit 1")
        assert result.success is False
        assert result.exit_code == 1

    def test_command_timeout(self) -> None:
        """CMD-5.3.3: Command timeout."""
        result = execute_command("sleep 10", timeout=1)
        assert result.success is False
        assert "timed out" in result.stderr.lower()

    def test_command_not_found(self) -> None:
        """CMD-5.3.4: Command not found."""
        result = execute_command("nonexistent_command_12345")
        assert result.success is False
        # Different systems return different error messages
        assert result.exit_code != 0 or "not found" in result.stderr.lower()


class TestRunCommandActionEachMatch:
    """Tests for run_for: each_match mode (CMD-5.1.x)."""

    def test_single_file(self) -> None:
        """CMD-5.1.1: Single file triggers single command."""
        action = CommandAction(command="echo {file}", run_for="each_match")
        results = run_command_action(action, ["src/main.py"])

        assert len(results) == 1
        assert results[0].command == "echo src/main.py"
        assert results[0].success is True

    def test_multiple_files(self) -> None:
        """CMD-5.1.2: Multiple files trigger command for each."""
        action = CommandAction(command="echo {file}", run_for="each_match")
        results = run_command_action(action, ["src/a.py", "src/b.py"])

        assert len(results) == 2
        assert results[0].command == "echo src/a.py"
        assert results[1].command == "echo src/b.py"

    def test_no_files(self) -> None:
        """CMD-5.1.3: No files - no command run."""
        action = CommandAction(command="echo {file}", run_for="each_match")
        results = run_command_action(action, [])

        assert len(results) == 0


class TestRunCommandActionAllMatches:
    """Tests for run_for: all_matches mode (CMD-5.2.x)."""

    def test_multiple_files_single_command(self) -> None:
        """CMD-5.2.1: Multiple files in single command."""
        action = CommandAction(command="echo {files}", run_for="all_matches")
        results = run_command_action(action, ["a.js", "b.js", "c.js"])

        assert len(results) == 1
        assert results[0].command == "echo a.js b.js c.js"
        assert results[0].success is True

    def test_single_file_single_command(self) -> None:
        """CMD-5.2.2: Single file in single command."""
        action = CommandAction(command="echo {files}", run_for="all_matches")
        results = run_command_action(action, ["a.js"])

        assert len(results) == 1
        assert results[0].command == "echo a.js"


class TestAllCommandsSucceeded:
    """Tests for all_commands_succeeded helper."""

    def test_all_success(self) -> None:
        """All commands succeeded."""
        results = [
            CommandResult(success=True, exit_code=0, stdout="ok", stderr="", command="echo 1"),
            CommandResult(success=True, exit_code=0, stdout="ok", stderr="", command="echo 2"),
        ]
        assert all_commands_succeeded(results) is True

    def test_one_failure(self) -> None:
        """One command failed."""
        results = [
            CommandResult(success=True, exit_code=0, stdout="ok", stderr="", command="echo 1"),
            CommandResult(success=False, exit_code=1, stdout="", stderr="error", command="exit 1"),
        ]
        assert all_commands_succeeded(results) is False

    def test_empty_list(self) -> None:
        """Empty list is considered success."""
        assert all_commands_succeeded([]) is True


class TestFormatCommandErrors:
    """Tests for format_command_errors helper."""

    def test_single_error(self) -> None:
        """Format single error."""
        results = [
            CommandResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="Something went wrong",
                command="failing_cmd",
            ),
        ]
        output = format_command_errors(results)
        assert "Command: failing_cmd" in output
        assert "Something went wrong" in output
        assert "Exit code: 1" in output

    def test_multiple_errors(self) -> None:
        """Format multiple errors."""
        results = [
            CommandResult(success=False, exit_code=1, stdout="", stderr="Error 1", command="cmd1"),
            CommandResult(success=False, exit_code=2, stdout="", stderr="Error 2", command="cmd2"),
        ]
        output = format_command_errors(results)
        assert "cmd1" in output
        assert "Error 1" in output
        assert "cmd2" in output
        assert "Error 2" in output

    def test_ignores_success(self) -> None:
        """Ignore successful commands."""
        results = [
            CommandResult(success=True, exit_code=0, stdout="ok", stderr="", command="good_cmd"),
            CommandResult(success=False, exit_code=1, stdout="", stderr="bad", command="bad_cmd"),
        ]
        output = format_command_errors(results)
        assert "good_cmd" not in output
        assert "bad_cmd" in output

    def test_includes_rule_name(self) -> None:
        """Include rule name when provided."""
        results = [
            CommandResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="Error output",
                command="test_cmd",
            ),
        ]
        output = format_command_errors(results, rule_name="My Test Rule")
        assert "Rule: My Test Rule" in output
        assert "Command: test_cmd" in output
        assert "Exit code: 1" in output
        assert "Stderr:\nError output" in output

    def test_includes_stdout(self) -> None:
        """Include stdout when present."""
        results = [
            CommandResult(
                success=False,
                exit_code=1,
                stdout="Standard output here",
                stderr="Standard error here",
                command="test_cmd",
            ),
        ]
        output = format_command_errors(results)
        assert "Stdout:\nStandard output here" in output
        assert "Stderr:\nStandard error here" in output

    def test_shows_no_output_message(self) -> None:
        """Show '(no output)' when no stdout or stderr."""
        results = [
            CommandResult(
                success=False,
                exit_code=42,
                stdout="",
                stderr="",
                command="silent_cmd",
            ),
        ]
        output = format_command_errors(results)
        assert "Command: silent_cmd" in output
        assert "Exit code: 42" in output
        assert "(no output)" in output

    def test_full_error_format(self) -> None:
        """Test complete error format with all fields."""
        results = [
            CommandResult(
                success=False,
                exit_code=42,
                stdout="stdout output",
                stderr="stderr output",
                command="echo test && exit 42",
            ),
        ]
        output = format_command_errors(results, rule_name="Command Failure Rule")
        # Verify all parts are present in the correct format
        assert "Rule: Command Failure Rule" in output
        assert "Command: echo test && exit 42" in output
        assert "Exit code: 42" in output
        assert "Stdout:\nstdout output" in output
        assert "Stderr:\nstderr output" in output
