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

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from deepwork.mcp.quality_gate import QualityGate
from deepwork.mcp.schemas import (
    FinishedStepInput,
    StartWorkflowInput,
)
from deepwork.mcp.state import StateManager
from deepwork.mcp.tools import WorkflowTools


def create_server(
    project_root: Path | str,
    quality_gate_command: str | None = None,
    quality_gate_timeout: int = 120,
    quality_gate_max_attempts: int = 3,
) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        project_root: Path to the project root
        quality_gate_command: Optional command for quality gate agent
        quality_gate_timeout: Timeout in seconds for quality gate (default: 120)
        quality_gate_max_attempts: Max attempts before failing quality gate (default: 3)

    Returns:
        Configured FastMCP server instance
    """
    project_path = Path(project_root).resolve()

    # Initialize components
    state_manager = StateManager(project_path)

    quality_gate: QualityGate | None = None
    if quality_gate_command:
        quality_gate = QualityGate(
            command=quality_gate_command,
            timeout=quality_gate_timeout,
        )

    tools = WorkflowTools(
        project_root=project_path,
        state_manager=state_manager,
        quality_gate=quality_gate,
        max_quality_attempts=quality_gate_max_attempts,
    )

    # Create MCP server
    mcp = FastMCP(
        name="deepwork",
        instructions=_get_server_instructions(),
    )

    # =========================================================================
    # MCP Tool Registrations
    # =========================================================================
    # IMPORTANT: When modifying these tool signatures (parameters, return types,
    # descriptions), update doc/mcp_interface.md to keep documentation in sync.
    # =========================================================================

    @mcp.tool(
        description=(
            "List all available DeepWork workflows. "
            "Returns job names, workflow definitions, and step information. "
            "Call this first to discover available workflows."
        )
    )
    def get_workflows() -> dict[str, Any]:
        """Get all available workflows."""
        response = tools.get_workflows()
        return response.model_dump()

    @mcp.tool(
        description=(
            "Start a new workflow session. "
            "Creates a git branch, initializes state tracking, and returns "
            "the first step's instructions. "
            "Required parameters: goal (what user wants), job_name, workflow_name. "
            "Optional: instance_id for naming (e.g., 'acme', 'q1-2026')."
        )
    )
    async def start_workflow(
        goal: str,
        job_name: str,
        workflow_name: str,
        instance_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a workflow and get first step instructions."""
        input_data = StartWorkflowInput(
            goal=goal,
            job_name=job_name,
            workflow_name=workflow_name,
            instance_id=instance_id,
        )
        response = await tools.start_workflow(input_data)
        return response.model_dump()

    @mcp.tool(
        description=(
            "Report that you've finished a workflow step. "
            "Validates outputs against quality criteria (if configured), "
            "then returns either: "
            "'needs_work' with feedback to fix issues, "
            "'next_step' with instructions for the next step, or "
            "'workflow_complete' when finished. "
            "Required: outputs (list of file paths created). "
            "Optional: notes about work done. "
            "Optional: quality_review_override_reason to skip quality review (must explain why)."
        )
    )
    async def finished_step(
        outputs: list[str],
        notes: str | None = None,
        quality_review_override_reason: str | None = None,
    ) -> dict[str, Any]:
        """Report step completion and get next instructions."""
        input_data = FinishedStepInput(
            outputs=outputs,
            notes=notes,
            quality_review_override_reason=quality_review_override_reason,
        )
        response = await tools.finished_step(input_data)
        return response.model_dump()

    return mcp


def _get_server_instructions() -> str:
    """Get the server instructions for agents.

    Returns:
        Instructions string describing how to use the DeepWork MCP server.
    """
    return """# DeepWork Workflow Server

This MCP server guides you through multi-step workflows with quality gates.

## Workflow

1. **Discover**: Call `get_workflows` to see available workflows
2. **Start**: Call `start_workflow` with your goal, job_name, and workflow_name
3. **Execute**: Follow the step instructions returned
4. **Checkpoint**: Call `finished_step` with your outputs when done with each step
5. **Iterate**: If `needs_work`, fix issues and call `finished_step` again
6. **Continue**: If `next_step`, execute new instructions and repeat
7. **Complete**: When `workflow_complete`, the workflow is done

## Quality Gates

Steps may have quality criteria. When you call `finished_step`:
- Your outputs are evaluated against the criteria
- If any fail, you'll get `needs_work` status with feedback
- Fix the issues and call `finished_step` again
- After passing, you'll get the next step or completion

## Best Practices

- Always call `get_workflows` first to understand available options
- Provide clear goals when starting - they're used for context
- Create all expected outputs before calling `finished_step`
- Use instance_id for meaningful names (e.g., client name, quarter)
- Read quality gate feedback carefully before retrying
"""
