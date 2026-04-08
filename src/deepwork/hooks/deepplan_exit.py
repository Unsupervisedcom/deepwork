"""PreToolUse hook for ExitPlanMode — enforces DeepPlan workflow.

Fires before ExitPlanMode. Checks if a deepplan workflow is active and
at the present_plan step. Blocks otherwise with instructions to start
or continue the workflow.
"""

from __future__ import annotations

import json
import os
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


def deepplan_exit_hook(hook_input: HookInput) -> HookOutput:
    """Pre-tool hook: enforce deepplan workflow before ExitPlanMode."""
    if hook_input.event != NormalizedEvent.BEFORE_TOOL:
        return HookOutput()

    if hook_input.tool_name != "exit_plan_mode":
        return HookOutput()

    session_id = hook_input.session_id
    if not session_id:
        return HookOutput()

    cwd = hook_input.cwd or os.getcwd()
    project_root = Path(cwd)

    state = _read_deepplan_state(project_root, session_id)

    if state == "at_present_plan":
        return HookOutput()
    elif state == "completed":
        return HookOutput()
    elif state == "active_not_at_present_plan":
        return HookOutput(
            decision="block",
            reason=(
                "The DeepPlan workflow is still in progress. "
                "Continue working through the workflow steps — "
                "ExitPlanMode should only be called during the `present_plan` step. "
                "Call `finished_step` to advance to the next step."
            ),
        )
    else:
        # No deepplan workflow found
        return HookOutput(
            decision="block",
            reason=(
                "Before exiting plan mode, start the DeepPlan workflow by calling "
                "`start_workflow` with job_name='deepplan' and "
                "workflow_name='create_deep_plan'. The workflow will guide you "
                "through structured planning and tell you when to call ExitPlanMode."
            ),
        )


def _read_deepplan_state(project_root: Path, session_id: str) -> str:
    """Check deepplan workflow state from session state files.

    Returns one of:
        "at_present_plan" — active deepplan workflow at present_plan step
        "active_not_at_present_plan" — active deepplan but not at present_plan
        "completed" — deepplan workflow was completed
        "none" — no deepplan workflow found
    """
    session_dir = (
        project_root / ".deepwork" / "tmp" / "sessions" / "claude" / f"session-{session_id}"
    )

    if not session_dir.exists():
        return "none"

    for state_file in session_dir.iterdir():
        if state_file.suffix != ".json":
            continue
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        # Check active workflow stack
        for entry in data.get("workflow_stack", []):
            if entry.get("job_name") == "deepplan":
                if entry.get("current_step_id") == "present_plan":
                    return "at_present_plan"
                return "active_not_at_present_plan"

        # Check completed workflows
        for entry in data.get("completed_workflows", []):
            if entry.get("job_name") == "deepplan" and entry.get("status") == "completed":
                return "completed"

    return "none"


def main() -> int:
    """Entry point for the hook CLI."""
    platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
    return run_hook(deepplan_exit_hook, platform)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        output_hook_error(e, context="deepplan_exit hook")
        sys.exit(0)
