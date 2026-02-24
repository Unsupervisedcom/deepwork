"""Review instruction file generation.

Generates self-contained markdown instruction files for review agents.
Each file contains the review instructions, files to examine, and any
additional context. Written to .deepwork/tmp/review_instructions/.
"""

import hashlib
import re
from pathlib import Path

from deepwork.review.config import ReviewTask
from deepwork.utils.fs import safe_write

INSTRUCTIONS_DIR = ".deepwork/tmp/review_instructions"

_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9\-_.]")


def compute_review_id(task: ReviewTask, project_root: Path) -> str:
    """Build a deterministic review ID encoding rule, paths, and content hash.

    Format: ``{sanitized_rule}--{sanitized_paths}--{content_hash_12}``.

    Args:
        task: The ReviewTask to compute an ID for.
        project_root: Absolute path to the project root.

    Returns:
        A deterministic, human-readable review ID string.
    """
    rule_part = _sanitize_for_id(task.rule_name)
    paths_part = _paths_component(task.files_to_review)
    hash_part = _content_hash(task.files_to_review, project_root)
    return f"{rule_part}--{paths_part}--{hash_part}"


def _sanitize_for_id(name: str) -> str:
    """Replace non-alphanumeric chars (except ``-``, ``_``, ``.``) with ``-``."""
    return _SANITIZE_RE.sub("-", name)


def _paths_component(files: list[str]) -> str:
    """Build the file-paths segment of a review ID.

    Each path has ``/`` replaced with ``-``.  Multiple paths are sorted
    alphabetically, then joined with ``_AND_``.  If the result exceeds
    100 characters, falls back to ``{N}_files``.
    """
    sanitized = sorted(f.replace("/", "-") for f in files)
    joined = "_AND_".join(sanitized)
    if len(joined) > 100:
        return f"{len(files)}_files"
    return joined


def _content_hash(files: list[str], project_root: Path) -> str:
    """SHA-256 content hash (first 12 hex chars) of the given files.

    Files are sorted alphabetically before concatenation.  Files that
    cannot be read contribute the placeholder ``MISSING``.
    """
    h = hashlib.sha256()
    for filepath in sorted(files):
        try:
            content = (project_root / filepath).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = "MISSING"
        h.update(content.encode("utf-8"))
    return h.hexdigest()[:12]


def write_instruction_files(
    tasks: list[ReviewTask],
    project_root: Path,
) -> list[tuple[ReviewTask, Path]]:
    """Write instruction files for all review tasks.

    Clears any existing ``.md`` instruction files (preserving ``.passed``
    marker files), then generates a new file for each task that does not
    already have a ``.passed`` marker.

    Args:
        tasks: List of ReviewTask objects to generate files for.
        project_root: Absolute path to the project root.

    Returns:
        List of (ReviewTask, instruction_file_path) tuples for tasks that
        were *not* skipped.
    """
    instructions_dir = project_root / INSTRUCTIONS_DIR

    # Clear previous .md instruction files (preserve .passed markers)
    if instructions_dir.exists():
        for child in instructions_dir.iterdir():
            if child.suffix == ".md":
                child.unlink()
    instructions_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[ReviewTask, Path]] = []

    for task in tasks:
        review_id = compute_review_id(task, project_root)

        # Skip if a .passed marker exists for this exact review_id
        passed_marker = instructions_dir / f"{review_id}.passed"
        if passed_marker.exists():
            continue

        content = build_instruction_file(task, review_id)
        file_path = instructions_dir / f"{review_id}.md"

        safe_write(file_path, content)
        results.append((task, file_path))

    return results


def build_instruction_file(task: ReviewTask, review_id: str = "") -> str:
    """Build the markdown content for a single review instruction file.

    Args:
        task: The ReviewTask to generate instructions for.
        review_id: The deterministic review ID for this task (used in the
            "After Review" section).

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

    # After Review: instruct agent to mark review as passed
    if review_id:
        parts.append("## After Review\n")
        parts.append(
            "If this review passes with no findings, call the "
            "`mark_review_as_passed` tool with:\n"
        )
        parts.append(f'- `review_id`: `"{review_id}"`')
        parts.append("")

    # Traceability: link back to the source policy
    if task.source_location:
        parts.append("---\n")
        parts.append(f"This review was requested by the policy at `{task.source_location}`.")
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
