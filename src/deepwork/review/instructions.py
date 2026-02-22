"""Review instruction file generation.

Generates self-contained markdown instruction files for review agents.
Each file contains the review instructions, files to examine, and any
additional context. Written to .deepwork/tmp/review_instructions/.
"""

import random
import shutil
from pathlib import Path

from deepwork.review.config import ReviewTask
from deepwork.utils.fs import safe_write

INSTRUCTIONS_DIR = ".deepwork/tmp/review_instructions"


def write_instruction_files(
    tasks: list[ReviewTask],
    project_root: Path,
) -> list[tuple[ReviewTask, Path]]:
    """Write instruction files for all review tasks.

    Clears any existing instruction files, then generates a new .md file
    for each task in .deepwork/tmp/review_instructions/.

    Args:
        tasks: List of ReviewTask objects to generate files for.
        project_root: Absolute path to the project root.

    Returns:
        List of (ReviewTask, instruction_file_path) tuples.
    """
    instructions_dir = project_root / INSTRUCTIONS_DIR

    # Clear previous instruction files
    if instructions_dir.exists():
        shutil.rmtree(instructions_dir)
    instructions_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[ReviewTask, Path]] = []

    for task in tasks:
        content = build_instruction_file(task)
        file_id = random.randint(1000000, 9999999)
        file_path = instructions_dir / f"{file_id}.md"

        # Ensure unique filename
        while file_path.exists():
            file_id = random.randint(1000000, 9999999)
            file_path = instructions_dir / f"{file_id}.md"

        safe_write(file_path, content)
        results.append((task, file_path))

    return results


def build_instruction_file(task: ReviewTask) -> str:
    """Build the markdown content for a single review instruction file.

    Args:
        task: The ReviewTask to generate instructions for.

    Returns:
        Markdown string containing the complete review instructions.
    """
    parts: list[str] = []

    # Header
    scope = _describe_scope(task)
    parts.append(f"# Review: {task.rule_name} — {scope}\n")

    # Review instructions
    parts.append("## Review Instructions\n")
    parts.append(task.instructions.strip())
    parts.append("")

    # Files to review
    parts.append("## Files to Review\n")
    for filepath in task.files_to_review:
        parts.append(f"- @{filepath}")
    parts.append("")

    # Additional context: unchanged matching files
    if task.additional_files:
        parts.append("## Unchanged Matching Files\n")
        parts.append(
            "These files match the review patterns but were not changed. "
            "They are provided for context.\n"
        )
        for filepath in task.additional_files:
            parts.append(f"- @{filepath}")
        parts.append("")

    # Additional context: all changed filenames
    if task.all_changed_filenames:
        parts.append("## All Changed Files\n")
        parts.append(
            "The following files were changed in this changeset "
            "(listed for context, not all are subject to this review).\n"
        )
        for filepath in task.all_changed_filenames:
            parts.append(f"- {filepath}")
        parts.append("")

    # Traceability: link back to the source policy
    if task.source_location:
        parts.append("---\n")
        parts.append(
            f"This review was requested by the policy at `{task.source_location}`."
        )
        parts.append("")

    return "\n".join(parts)


def _describe_scope(task: ReviewTask) -> str:
    """Generate a human-readable scope description for the task.

    Args:
        task: The ReviewTask to describe.

    Returns:
        Scope description string.
    """
    if len(task.files_to_review) == 1:
        return task.files_to_review[0]
    return f"{len(task.files_to_review)} files"
