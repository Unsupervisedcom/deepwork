"""Output formatting for review task instructions.

Formats ReviewTask results into structured text that AI agent platforms
(e.g., Claude Code) can use to dispatch parallel review agents.
"""

from pathlib import Path

from deepwork.review.config import ReviewTask


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

    lines: list[str] = []
    lines.append("Invoke the following list of Tasks in parallel:\n")

    for task, file_path in task_files:
        # Make the instruction file path relative to project root
        try:
            rel_path = file_path.relative_to(project_root)
        except ValueError:
            rel_path = file_path

        name = _task_name(task)
        agent = task.agent_name or "Default"

        lines.append(f'Name: "{name}"')
        lines.append(f"\tAgent: {agent}")
        lines.append(f'\tprompt: "@{rel_path}"')
        lines.append("")

    return "\n".join(lines)


def _task_name(task: ReviewTask) -> str:
    """Generate a descriptive name for a review task.

    Args:
        task: The ReviewTask to name.

    Returns:
        Task name string.
    """
    if len(task.files_to_review) == 1:
        return f"{task.rule_name} review of {task.files_to_review[0]}"
    return f"{task.rule_name} review of {len(task.files_to_review)} files"
