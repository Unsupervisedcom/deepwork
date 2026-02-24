"""MCP adapter for the DeepWork review pipeline.

Thin adapter that exposes the review pipeline as a single function
suitable for registration as an MCP tool.
"""

from pathlib import Path

from deepwork.review.discovery import DiscoveryError, load_all_rules
from deepwork.review.formatter import format_for_claude
from deepwork.review.instructions import INSTRUCTIONS_DIR, write_instruction_files
from deepwork.review.matcher import (
    GitDiffError,
    format_source_location,
    get_changed_files,
    match_files_to_rules,
    match_rule,
)

FORMATTERS = {
    "claude": format_for_claude,
}

SUPPORTED_PLATFORMS = set(FORMATTERS.keys())


class ReviewToolError(Exception):
    """Exception raised for review tool errors (git failures, write failures)."""

    pass


def _format_discovery_warnings(errors: list[DiscoveryError]) -> str:
    """Format discovery errors into a bullet-list warning string.

    Args:
        errors: List of DiscoveryError objects.

    Returns:
        Multi-line string with one ``  - path: error`` entry per error.
    """
    return "\n".join(f"  - {e.file_path}: {e.error}" for e in errors)


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
    rules, discovery_errors = load_all_rules(project_root)

    if not rules:
        if discovery_errors:
            warnings = _format_discovery_warnings(discovery_errors)
            return f"No valid .deepreview rules found. Parse errors:\n{warnings}"
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
    result = formatter(task_files, project_root)

    if discovery_errors:
        warnings = _format_discovery_warnings(discovery_errors)
        result = f"Warning: Some .deepreview files could not be parsed:\n{warnings}\n\n{result}"

    return result


def get_configured_reviews(
    project_root: Path,
    only_rules_matching_files: list[str] | None = None,
) -> list[dict[str, str]]:
    """Return metadata for configured review rules.

    Args:
        project_root: Absolute path to the project root.
        only_rules_matching_files: When provided, only return rules whose
            include/exclude patterns match at least one of these files.

    Returns:
        List of dicts with ``name``, ``description``, and ``defining_file``.
    """
    rules, errors = load_all_rules(project_root)

    if only_rules_matching_files is not None:
        rules = [
            rule for rule in rules if match_rule(only_rules_matching_files, rule, project_root)
        ]

    result = [
        {
            "name": rule.name,
            "description": rule.description,
            "defining_file": format_source_location(rule, project_root),
        }
        for rule in rules
    ]

    if errors:
        for err in errors:
            result.append(
                {
                    "name": f"PARSE_ERROR:{err.file_path}",
                    "description": err.error,
                    "defining_file": str(err.file_path),
                }
            )

    return result


def mark_passed(project_root: Path, review_id: str) -> str:
    """Create a ``.passed`` marker for a review so it is skipped on re-runs.

    Args:
        project_root: Absolute path to the project root.
        review_id: The deterministic review ID returned in the instruction file.

    Returns:
        Confirmation message.

    Raises:
        ValueError: If ``review_id`` is empty or contains path traversal.
    """
    if not review_id or not review_id.strip():
        raise ValueError("review_id must not be empty.")
    if ".." in review_id or review_id.startswith("/"):
        raise ValueError("review_id must not contain path traversal sequences.")

    instructions_dir = project_root / INSTRUCTIONS_DIR
    instructions_dir.mkdir(parents=True, exist_ok=True)

    passed_file = instructions_dir / f"{review_id}.passed"
    passed_file.write_bytes(b"")

    return f"Review '{review_id}' marked as passed."
