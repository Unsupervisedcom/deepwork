"""MCP adapter for the DeepWork review pipeline.

Thin adapter that exposes the review pipeline as a single function
suitable for registration as an MCP tool.
"""

from pathlib import Path

from deepwork.review.discovery import load_all_rules
from deepwork.review.formatter import format_for_claude
from deepwork.review.instructions import write_instruction_files
from deepwork.review.matcher import GitDiffError, get_changed_files, match_files_to_rules

FORMATTERS = {
    "claude": format_for_claude,
}

SUPPORTED_PLATFORMS = set(FORMATTERS.keys())


class ReviewToolError(Exception):
    """Exception raised for review tool errors (git failures, write failures)."""

    pass


def run_review(
    project_root: Path,
    platform: str,
    files: list[str] | None = None,
) -> str:
    """Run the review pipeline and return formatted output.

    Args:
        project_root: Absolute path to the project root.
        platform: Target platform for formatting (e.g., "claude").
        files: Explicit file list. If None, detects changes via git diff.

    Returns:
        Formatted review output string.

    Raises:
        ReviewToolError: On git failures, write failures, or unsupported platform.
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise ReviewToolError(
            f"Unsupported platform: '{platform}'. "
            f"Supported platforms: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )

    # Step 1: Discover .deepreview files and parse rules
    rules, _discovery_errors = load_all_rules(project_root)

    if not rules:
        return "No .deepreview configuration files found."

    # Step 2: Determine changed files
    if files is not None:
        changed_files = sorted(set(files))
    else:
        try:
            changed_files = get_changed_files(project_root)
        except GitDiffError as e:
            raise ReviewToolError(f"Git error: {e}") from e

    if not changed_files:
        return "No changed files detected."

    # Step 3: Match changed files against rules
    tasks = match_files_to_rules(changed_files, rules, project_root, platform)

    if not tasks:
        return "No review rules matched the changed files."

    # Step 4: Generate instruction files
    try:
        task_files = write_instruction_files(tasks, project_root)
    except OSError as e:
        raise ReviewToolError(f"Error writing instruction files: {e}") from e

    # Step 5: Format output
    formatter = FORMATTERS[platform]
    return formatter(task_files, project_root)
