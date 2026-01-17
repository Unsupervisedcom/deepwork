"""Execute command actions for rules."""

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from deepwork.core.rules_parser import CommandAction


@dataclass
class CommandResult:
    """Result of executing a command."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: str  # The actual command that was run


def substitute_command_variables(
    command_template: str,
    file: str | None = None,
    files: list[str] | None = None,
    repo_root: Path | None = None,
) -> str:
    """
    Substitute template variables in a command string.

    Variables:
    - {file} - Single file path
    - {files} - Space-separated file paths
    - {repo_root} - Repository root directory

    Args:
        command_template: Command string with {var} placeholders
        file: Single file path (for run_for: each_match)
        files: List of file paths (for run_for: all_matches)
        repo_root: Repository root path

    Returns:
        Command string with variables substituted
    """
    result = command_template

    if file is not None:
        # Quote file path to prevent command injection
        result = result.replace("{file}", shlex.quote(file))

    if files is not None:
        # Quote each file path individually
        quoted_files = " ".join(shlex.quote(f) for f in files)
        result = result.replace("{files}", quoted_files)

    if repo_root is not None:
        result = result.replace("{repo_root}", shlex.quote(str(repo_root)))

    return result


def execute_command(
    command: str,
    cwd: Path | None = None,
    timeout: int = 60,
) -> CommandResult:
    """
    Execute a command and capture output.

    Args:
        command: Command string to execute
        cwd: Working directory (defaults to current directory)
        timeout: Timeout in seconds

    Returns:
        CommandResult with execution details
    """
    try:
        # Run command as shell to support pipes, etc.
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return CommandResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            command=command,
        )

    except subprocess.TimeoutExpired:
        return CommandResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            command=command,
        )
    except Exception as e:
        return CommandResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=str(e),
            command=command,
        )


def run_command_action(
    action: CommandAction,
    trigger_files: list[str],
    repo_root: Path | None = None,
) -> list[CommandResult]:
    """
    Run a command action for the given trigger files.

    Args:
        action: CommandAction configuration
        trigger_files: Files that triggered the rule
        repo_root: Repository root path

    Returns:
        List of CommandResult (one per command execution)
    """
    results: list[CommandResult] = []

    if action.run_for == "each_match":
        # Run command for each file individually
        for file_path in trigger_files:
            command = substitute_command_variables(
                action.command,
                file=file_path,
                repo_root=repo_root,
            )
            result = execute_command(command, cwd=repo_root)
            results.append(result)

    elif action.run_for == "all_matches":
        # Run command once with all files
        command = substitute_command_variables(
            action.command,
            files=trigger_files,
            repo_root=repo_root,
        )
        result = execute_command(command, cwd=repo_root)
        results.append(result)

    return results


def all_commands_succeeded(results: list[CommandResult]) -> bool:
    """Check if all command executions succeeded."""
    return all(r.success for r in results)


def format_command_errors(results: list[CommandResult]) -> str:
    """Format error messages from failed commands."""
    errors: list[str] = []
    for result in results:
        if not result.success:
            msg = f"Command failed: {result.command}\n"
            if result.stderr:
                msg += f"Error: {result.stderr}\n"
            if result.exit_code != 0:
                msg += f"Exit code: {result.exit_code}\n"
            errors.append(msg)
    return "\n".join(errors)
