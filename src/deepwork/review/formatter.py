"""Output formatting for review task instructions.

Formats ReviewTask results into structured text that AI agent platforms
(e.g., Claude Code) can use to dispatch parallel review agents.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from deepwork.review.config import ReviewTask
from deepwork.review.instructions import short_instruction_filename


def _relative_instruction_path(file_path: Path, project_root: Path) -> Path:
    """Resolve instruction file path relative to the project when possible."""
    try:
        return file_path.relative_to(project_root)
    except ValueError:
        return file_path


def _git_common_dir(project_root: Path) -> Path | None:
    """Return the absolute path to the git common directory.

    In a normal repo this is ``<repo>/.git``.  In a linked worktree it
    still points to the *main* repo's ``.git`` directory, which lets
    callers discover the main working-tree root.

    Returns ``None`` when *project_root* is not inside a git repository
    or the ``git`` command is unavailable.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        raw = result.stdout.strip()
        if not raw:
            return None
        return Path(raw)
    except Exception:
        return None


def _resolve_file_ref_root(project_root: Path) -> Path:
    """Resolve the root directory for ``@file`` references.

    In a git worktree, Claude Code expands ``@file`` paths relative to
    the *main* working tree — not the worktree.  This function detects
    worktrees and returns the main repo root so that formatted paths
    resolve correctly.

    Falls back to *project_root* when not in a worktree or when git is
    unavailable.
    """
    git_common = _git_common_dir(project_root)
    if git_common is None:
        return project_root

    main_root = git_common.parent
    if main_root != project_root and project_root.is_relative_to(main_root):
        return main_root

    return project_root


def format_for_claude(
    task_files: list[tuple[ReviewTask, Path]],
    project_root: Path,
) -> str:
    """Format review tasks as Claude Code parallel task invocations.

    Produces structured text that Claude Code can parse to dispatch
    multiple review agents in parallel.

    Args:
        task_files: List of (ReviewTask, instruction_file_path) tuples.
        project_root: Absolute path to the project root.

    Returns:
        Formatted instruction text for Claude Code.
    """
    if not task_files:
        return "No review tasks to execute."

    file_ref_root = _resolve_file_ref_root(project_root)

    lines: list[str] = []
    lines.append("Invoke the following list of Tasks in parallel.")
    lines.append(
        "IMPORTANT: Do NOT read the prompt files yourself. Pass the prompt field "
        "directly to each agent — the @file references are expanded automatically.\n"
    )

    for task, file_path in task_files:
        # Make the instruction file path relative to the file-ref root
        # (main repo root in a worktree, project_root otherwise)
        try:
            rel_path = file_path.relative_to(file_ref_root)
        except ValueError:
            rel_path = file_path

        name = _task_name(task)
        description = _task_description(task)
        subagent_type = task.agent_name or "general-purpose"

        lines.append(f'name: "{name}"')
        lines.append(f"\tdescription: {description}")
        lines.append(f"\tsubagent_type: {subagent_type}")
        lines.append(f'\tprompt: "@{rel_path}"')
        lines.append("")

    return "\n".join(lines)


def format_for_openclaw(
    task_files: list[tuple[ReviewTask, Path]],
    project_root: Path,
) -> str:
    """Format review tasks as OpenClaw `sessions_spawn` work items."""
    if not task_files:
        return "No review tasks to execute."

    lines: list[str] = []
    lines.append("Spawn the following review sub-agents in parallel with `sessions_spawn`.")
    lines.append(
        "IMPORTANT: Do not complete these reviews in the main session unless you cannot "
        "spawn sub-agents. Spawn all of them before you wait for completions. Use each "
        "instruction path exactly as written, relative to the workspace, and do not "
        "rewrite it as an absolute host path. Omit `timeoutSeconds` on review spawns so "
        "the runtime default applies; if a timeout value is required, use `0`.\n"
    )

    for idx, (task, file_path) in enumerate(task_files, start=1):
        alias_path = file_path.with_name(short_instruction_filename(file_path.stem))
        rel_path = _relative_instruction_path(alias_path, project_root)
        name = _task_name(task)
        description = _task_description(task)

        lines.append(f"{idx}. label: {name}")
        lines.append(f"   description: {description}")
        lines.append(
            "   task: Read the review instructions at "
            f"`{rel_path}` and execute that review. Return only findings and concrete fixes."
        )
        if task.agent_name:
            lines.append(f"   agent_type: {task.agent_name}")
        lines.append("")

    return "\n".join(lines)


FORMATTERS = {
    "claude": format_for_claude,
    "openclaw": format_for_openclaw,
}


def _task_description(task: ReviewTask) -> str:
    """Generate a short description for a review task.

    Args:
        task: The ReviewTask to describe.

    Returns:
        Short description string.
    """
    prefix = _scope_prefix(task)
    return f"Review {prefix}{task.rule_name}"


def _task_name(task: ReviewTask) -> str:
    """Generate a descriptive name for a review task.

    Includes a scope prefix derived from the source directory when the
    rule comes from a subdirectory .deepreview file.  This disambiguates
    same-named rules from different directories (REVIEW-REQ-004.10).

    For inline-content tasks (type: string step outputs per JOBS-REQ-004.8)
    the scope reads ``inline content`` instead of a file count.

    Args:
        task: The ReviewTask to name.

    Returns:
        Task name string.
    """
    prefix = _scope_prefix(task)
    if not task.files_to_review and task.inline_content is not None:
        return f"{prefix}{task.rule_name} review of inline content"
    if len(task.files_to_review) == 1:
        return f"{prefix}{task.rule_name} review of {task.files_to_review[0]}"
    return f"{prefix}{task.rule_name} review of {len(task.files_to_review)} files"


def _scope_prefix(task: ReviewTask) -> str:
    """Derive a short scope prefix from the task's source_location.

    Returns ``"dirname/"`` when the .deepreview file lives in a
    subdirectory, or ``""`` for root-level rules or when no source
    location is available.

    Args:
        task: The ReviewTask with source_location set by the matcher.

    Returns:
        Scope prefix string (e.g., ``"my_job/"`` or ``""``).
    """
    if not task.source_location:
        return ""
    # source_location is formatted as "relative/path/.deepreview:line"
    path_part = task.source_location.rsplit(":", 1)[0]
    parent = Path(path_part).parent
    if parent == Path("."):
        return ""
    return f"{parent.name}/"
