"""CLI command for running DeepWork Reviews."""

import sys
from pathlib import Path

import click

from deepwork.review.discovery import load_all_rules
from deepwork.review.formatter import format_for_claude
from deepwork.review.instructions import write_instruction_files
from deepwork.review.matcher import GitDiffError, get_changed_files, match_files_to_rules


@click.command()
@click.option(
    "--instructions-for",
    "instructions_for",
    type=click.Choice(["claude"]),
    required=True,
    help="Target platform for review instructions.",
)
@click.option(
    "--base-ref",
    "base_ref",
    default=None,
    help="Git ref to diff against. Auto-detects merge-base with main/master if not specified.",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project root directory.",
)
@click.option(
    "--files",
    "file_args",
    multiple=True,
    help="Explicit file paths to review (skips git diff). Can be repeated.",
)
def review(
    instructions_for: str,
    base_ref: str | None,
    path: str,
    file_args: tuple[str, ...],
) -> None:
    """Generate review instructions for changed files based on .deepreview configs.

    By default, detects changed files via git diff. You can override this by
    passing explicit file paths with --files or by piping a file list on stdin:

    \b
      # Explicit files
      deepwork review --instructions-for claude --files src/app.py --files src/lib.py

    \b
      # Pipe from git
      git diff --name-only HEAD~3 | deepwork review --instructions-for claude

    \b
      # Glob (shell expands the pattern)
      printf '%s\n' src/**/*.py | deepwork review --instructions-for claude

    \b
      # find
      find src -name '*.py' | deepwork review --instructions-for claude
    """
    project_root = Path(path).resolve()

    # Step 1: Discover .deepreview files and parse rules
    rules, discovery_errors = load_all_rules(project_root)

    for err in discovery_errors:
        click.echo(f"Warning: {err.file_path}: {err.error}", err=True)

    if not rules:
        click.echo("No .deepreview configuration files found.")
        return

    # Step 2: Determine changed files
    changed_files = _resolve_changed_files(file_args, project_root, base_ref)
    if changed_files is None:
        # Error already printed
        sys.exit(1)

    if not changed_files:
        click.echo("No changed files detected.")
        return

    # Step 3: Match changed files against rules
    tasks = match_files_to_rules(changed_files, rules, project_root, instructions_for)

    if not tasks:
        click.echo("No review rules matched the changed files.")
        return

    # Step 4: Generate instruction files
    try:
        task_files = write_instruction_files(tasks, project_root)
    except OSError as e:
        click.echo(f"Error writing instruction files: {e}", err=True)
        sys.exit(1)

    # Step 5: Format and output
    if instructions_for == "claude":
        output = format_for_claude(task_files, project_root)
        click.echo(output)


def _resolve_changed_files(
    file_args: tuple[str, ...],
    project_root: Path,
    base_ref: str | None,
) -> list[str] | None:
    """Determine the list of changed files from args, stdin, or git diff.

    Priority:
      1. --files arguments (if any provided)
      2. stdin (if piped, not a TTY)
      3. git diff (default)

    Returns:
        Sorted deduplicated list of file paths, or None on error.
    """
    if file_args:
        return _normalize_file_list(list(file_args))

    if not sys.stdin.isatty():
        lines = sys.stdin.read().strip().splitlines()
        files = [line.strip() for line in lines if line.strip()]
        if files:
            return _normalize_file_list(files)

    try:
        return get_changed_files(project_root, base_ref)
    except GitDiffError as e:
        click.echo(f"Error: {e}", err=True)
        return None


def _normalize_file_list(files: list[str]) -> list[str]:
    """Deduplicate and sort a list of file paths."""
    return sorted(set(files))
