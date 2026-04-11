"""PostToolUse hook: nudge the agent to run the review skill after a
git commit -- but only when at least one applicable review has not
already been marked as passed for the committed files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    output_hook_error,
    run_hook,
)

REMINDER_CONTEXT = (
    "You **MUST** use AskUserQuestion tool to offer to the user to run "
    "the `review` skill to review the changes you just committed if you "
    "have not run a review recently."
)

ALL_PASSED_CONTEXT = "No re-review needed - all reviews passed for committed files"


def post_commit_reminder_hook(hook_input: HookInput) -> HookOutput:
    if hook_input.event != NormalizedEvent.AFTER_TOOL:
        return HookOutput()
    if hook_input.tool_name != "shell":
        return HookOutput()
    command = hook_input.tool_input.get("command", "") or ""
    if "git commit" not in command:
        return HookOutput()

    cwd = hook_input.cwd or os.getcwd()
    project_root = Path(cwd)

    committed = _committed_files(project_root)
    if committed is None:
        # Git call failed; fall back to the safe old behavior.
        return HookOutput(context=REMINDER_CONTEXT)

    try:
        from deepwork.review.mcp import all_reviews_passed_for_files

        passed = all_reviews_passed_for_files(project_root, committed)
    except Exception:
        return HookOutput(context=REMINDER_CONTEXT)

    return HookOutput(context=ALL_PASSED_CONTEXT if passed else REMINDER_CONTEXT)


def _committed_files(project_root: Path) -> list[str] | None:
    """Return files in HEAD's commit, or ``None`` if the git command fails."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
    return run_hook(post_commit_reminder_hook, platform)


if __name__ == "__main__":  # pragma: no cover
    try:
        sys.exit(main())
    except Exception as e:
        output_hook_error(e, context="post_commit_reminder hook")
        sys.exit(0)
