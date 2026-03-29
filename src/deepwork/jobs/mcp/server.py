"""FastMCP server for DeepWork workflows.

This module creates and configures the MCP server that exposes workflow
management tools to AI agents.

Usage:
    deepwork serve --path /path/to/project

IMPORTANT: If you modify any tool signatures, parameters, or return types in this
file, you MUST also update the documentation in doc/mcp_interface.md to keep it
in sync with the implementation.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from deepwork.jobs.mcp.schemas import (
    AbortWorkflowInput,
    ArgumentValue,
    FinishedStepInput,
    GoToStepInput,
    StartWorkflowInput,
)
from deepwork.jobs.mcp.state import StateManager
from deepwork.jobs.mcp.status import StatusWriter
from deepwork.jobs.mcp.tools import WorkflowTools

# Configure logging
logger = logging.getLogger("deepwork.jobs.mcp")


def _ensure_schema_available(project_root: Path) -> None:
    """Copy job.schema.json to .deepwork/ so agents have a stable reference path."""
    from deepwork.jobs.schema import get_schema_path

    schema_source = get_schema_path()
    target_dir = project_root / ".deepwork"
    target = target_dir / "job.schema.json"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema_source, target)
    except OSError:
        logger.warning("Could not copy schema to %s", target)


def create_server(
    project_root: Path | str,
    platform: str | None = None,
    **_kwargs: Any,
) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        project_root: Path to the project root
        platform: Platform identifier for the review tool (e.g., "claude").
            Defaults to "claude" if not set. (default: None)
        **_kwargs: Accepted for backwards compatibility (enable_quality_gate,
            quality_gate_timeout, quality_gate_max_attempts, external_runner).
            These are no longer used — quality reviews now go through the
            DeepWork Reviews infrastructure.

    Returns:
        Configured FastMCP server instance
    """
    project_path = Path(project_root).resolve()

    # Copy the job schema to a stable location so agents can always reference it
    _ensure_schema_available(project_path)

    # Initialize components
    state_manager = StateManager(project_root=project_path, platform=platform or "claude")
    status_writer = StatusWriter(project_path)

    tools = WorkflowTools(
        project_root=project_path,
        state_manager=state_manager,
        status_writer=status_writer,
    )

    # Write initial manifest at startup
    try:
        tools._write_manifest()
    except Exception:
        logger.warning("Failed to write initial job manifest", exc_info=True)

    # Create MCP server
    mcp = FastMCP(
        name="deepwork",
        instructions=_get_server_instructions(),
    )

    # =========================================================================
    # MCP Tool Registrations
    # =========================================================================

    def _log_tool_call(
        tool_name: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Log a tool call with stack information."""
        log_data: dict[str, Any] = {"tool": tool_name}
        if session_id:
            stack = [entry.model_dump() for entry in state_manager.get_stack(session_id, agent_id)]
            log_data["stack"] = stack
            log_data["stack_depth"] = len(stack)
        if params:
            log_data["params"] = params
        logger.info("MCP tool call: %s", log_data)

    @mcp.tool(
        description=(
            "List all available DeepWork workflows. "
            "Returns job names, workflow definitions, and step information. "
            "Call this first to discover available workflows."
        )
    )
    def get_workflows() -> dict[str, Any]:
        """Get all available workflows."""
        _log_tool_call("get_workflows")
        response = tools.get_workflows()
        return response.model_dump()

    @mcp.tool(
        description=(
            "Start a new workflow session. "
            "Initializes state tracking and returns the first step's instructions. "
            "Required parameters: goal (what user wants), job_name, workflow_name, "
            "session_id (CLAUDE_CODE_SESSION_ID from startup context). "
            "Optional: inputs (map of step_argument names to values for the first step), "
            "agent_id (CLAUDE_CODE_AGENT_ID from startup context, for sub-agents). "
            "Supports nested workflows - starting a workflow while one is active "
            "pushes onto the stack. Use abort_workflow to cancel and return to parent."
        )
    )
    async def start_workflow(
        goal: str,
        job_name: str,
        workflow_name: str,
        session_id: str,
        inputs: dict[str, ArgumentValue] | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a workflow and get first step instructions."""
        _log_tool_call(
            "start_workflow",
            {
                "goal": goal,
                "job_name": job_name,
                "workflow_name": workflow_name,
                "inputs": inputs,
                "agent_id": agent_id,
            },
            session_id=session_id,
            agent_id=agent_id,
        )
        input_data = StartWorkflowInput(
            goal=goal,
            job_name=job_name,
            workflow_name=workflow_name,
            inputs=inputs,
            session_id=session_id,
            agent_id=agent_id,
        )
        response = await tools.start_workflow(input_data)
        return response.model_dump()

    @mcp.tool(
        description=(
            "Report that you've finished a workflow step. "
            "Validates outputs and runs quality reviews (from step definitions and .deepreview rules), "
            "then returns either: "
            "'needs_work' with review instructions to follow, "
            "'next_step' with instructions for the next step, or "
            "'workflow_complete' when finished (pops from stack if nested). "
            "Required: outputs (map of step_argument names to values), "
            "session_id (CLAUDE_CODE_SESSION_ID from startup context). "
            "For outputs with type 'file_path': pass a single string path or list of paths. "
            "For outputs with type 'string': pass a string value. "
            "Outputs marked required: true must be provided; required: false outputs can be omitted. "
            "Check step_expected_outputs in the response to see each output's type and required status. "
            "Optional: work_summary describing the work done (used by process_requirements reviews). "
            "Optional: quality_review_override_reason to skip quality review (must explain why). "
            "Optional: agent_id (CLAUDE_CODE_AGENT_ID from startup context, for sub-agents)."
        )
    )
    async def finished_step(
        outputs: dict[str, ArgumentValue],
        session_id: str,
        work_summary: str | None = None,
        quality_review_override_reason: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Report step completion and get next instructions."""
        _log_tool_call(
            "finished_step",
            {
                "outputs": outputs,
                "work_summary": work_summary,
                "quality_review_override_reason": quality_review_override_reason,
                "agent_id": agent_id,
            },
            session_id=session_id,
            agent_id=agent_id,
        )
        input_data = FinishedStepInput(
            outputs=outputs,
            work_summary=work_summary,
            quality_review_override_reason=quality_review_override_reason,
            session_id=session_id,
            agent_id=agent_id,
        )
        response = await tools.finished_step(input_data)
        return response.model_dump()

    @mcp.tool(
        description=(
            "Abort the current workflow and return to the parent workflow (if nested). "
            "Use this when a workflow cannot be completed and needs to be abandoned. "
            "Required: explanation (why the workflow is being aborted), "
            "session_id (CLAUDE_CODE_SESSION_ID from startup context). "
            "Optional: agent_id (CLAUDE_CODE_AGENT_ID from startup context, for sub-agents). "
            "Returns the aborted workflow info and the resumed parent workflow (if any)."
        )
    )
    async def abort_workflow(
        explanation: str,
        session_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Abort the current workflow and return to parent."""
        _log_tool_call(
            "abort_workflow",
            {"explanation": explanation, "agent_id": agent_id},
            session_id=session_id,
            agent_id=agent_id,
        )
        input_data = AbortWorkflowInput(
            explanation=explanation, session_id=session_id, agent_id=agent_id
        )
        response = await tools.abort_workflow(input_data)
        return response.model_dump()

    @mcp.tool(
        description=(
            "Navigate back to a prior step in the current workflow. "
            "Clears all progress from the target step onward, forcing re-execution "
            "of subsequent steps to ensure consistency. "
            "Use this when earlier outputs need revision or quality issues are discovered. "
            "Files on disk are NOT deleted — only session tracking state is cleared. "
            "Required: step_id (the step name to go back to), "
            "session_id (CLAUDE_CODE_SESSION_ID from startup context). "
            "Optional: agent_id (CLAUDE_CODE_AGENT_ID from startup context, for sub-agents)."
        )
    )
    async def go_to_step(
        step_id: str,
        session_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Navigate back to a prior step, clearing subsequent progress."""
        _log_tool_call(
            "go_to_step",
            {"step_id": step_id, "agent_id": agent_id},
            session_id=session_id,
            agent_id=agent_id,
        )
        input_data = GoToStepInput(step_id=step_id, session_id=session_id, agent_id=agent_id)
        response = await tools.go_to_step(input_data)
        return response.model_dump()

    # ---- Review tool (outside the workflow lifecycle) ----

    from deepwork.review.mcp import ReviewToolError, run_review
    from deepwork.review.mcp import get_configured_reviews as get_configured_reviews_fn
    from deepwork.review.mcp import mark_passed as mark_passed_fn

    review_platform = platform or "claude"

    @mcp.tool(
        description=(
            "Run a review of changed files based on .deepreview configuration files. "
            "Returns a list of review tasks to invoke in parallel. Each task has "
            "name, description, subagent_type, and prompt fields for the Task tool. "
            "Optional: files (list of file paths to review). When omitted, detects "
            "changes via git diff against the main branch."
        )
    )
    def get_review_instructions(files: list[str] | None = None) -> str:
        """Run review pipeline on changed files."""
        _log_tool_call("get_review_instructions", {"files": files})
        try:
            return run_review(project_path, review_platform, files)
        except ReviewToolError as e:
            return f"Review error: {e}"

    @mcp.tool(
        description=(
            "List all configured review rules from .deepreview files. "
            "Returns each rule's name, description, and defining file. "
            "Optional: only_rules_matching_files (list of file paths) to filter "
            "to rules that would apply to those specific files."
        )
    )
    def get_configured_reviews(
        only_rules_matching_files: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """List configured review rules, optionally filtered by file paths."""
        _log_tool_call(
            "get_configured_reviews",
            {"only_rules_matching_files": only_rules_matching_files},
        )
        return get_configured_reviews_fn(project_path, only_rules_matching_files)

    @mcp.tool(
        description=(
            "Mark a review as passed so it won't be re-run while reviewed files "
            "remain unchanged. The review_id is provided in the instruction file's "
            '"After Review" section.'
        )
    )
    def mark_review_as_passed(review_id: str) -> str:
        """Mark a review as passed by creating a .passed marker file."""
        _log_tool_call("mark_review_as_passed", {"review_id": review_id})
        try:
            return mark_passed_fn(project_path, review_id)
        except ValueError as e:
            return f"Validation error: {e}"

    return mcp


def _get_server_instructions() -> str:
    """Get the server instructions for agents."""
    return """# DeepWork Workflow Server

This MCP server guides you through multi-step workflows with quality gates.

## Session Identity

All workflow tools require `session_id` (your CLAUDE_CODE_SESSION_ID from startup context).
If you are a sub-agent, also pass `agent_id` (your CLAUDE_CODE_AGENT_ID from startup context).

## Workflow

1. **Discover**: Call `get_workflows` to see available workflows
2. **Start**: Call `start_workflow` with your goal, job_name, workflow_name, and session_id
3. **Execute**: Follow the step instructions returned
4. **Checkpoint**: Call `finished_step` with your outputs and session_id when done with each step
5. **Iterate**: If `needs_work`, fix issues and call `finished_step` again
6. **Continue**: If `next_step`, execute new instructions and repeat
7. **Complete**: When `workflow_complete`, the workflow is done

## Quality Gates

Steps may have quality criteria. When you call `finished_step`:
- Your outputs are evaluated against the criteria
- If any fail, you'll get `needs_work` status with feedback
- Fix the issues and call `finished_step` again
- After passing, you'll get the next step or completion

## Nested Workflows

Workflows can be nested - starting a new workflow while one is active pushes
onto a stack. This is useful when a step requires running another workflow.

- All tool responses include a `stack` field showing the current workflow stack
- Each stack entry shows `{workflow: "job/workflow", step: "current_step"}`
- When a workflow completes, it pops from the stack and resumes the parent
- Use `abort_workflow` to cancel the current workflow and return to parent

## Aborting Workflows

If a workflow cannot be completed, use `abort_workflow` with an explanation:
- The current workflow is marked as aborted and popped from the stack
- If there was a parent workflow, it becomes active again
- The explanation is saved for debugging and audit purposes

## Going Back

Use `go_to_step` to navigate back to a prior step when earlier outputs need revision:
- All progress from the target step onward is cleared (outputs, timestamps, quality attempts)
- The agent must re-execute all steps from the target onward
- Files on disk are NOT deleted — only session tracking state is cleared
- Cannot go forward — use `finished_step` to advance

## Best Practices

- Always call `get_workflows` first to understand available options
- Provide clear goals when starting - they're used for context
- Create all expected outputs before calling `finished_step`
- Use instance_id for meaningful names (e.g., client name, quarter)
- Read quality gate feedback carefully before retrying
- Check the `stack` field in responses to understand nesting depth
- Use `abort_workflow` rather than leaving workflows in a broken state
"""
