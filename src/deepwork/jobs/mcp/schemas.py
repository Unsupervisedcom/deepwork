"""Pydantic models for MCP tool inputs and outputs.

IMPORTANT: If you modify any models in this file that affect the MCP tool
interfaces (input models, output models, or their fields), you MUST also
update the documentation in doc/mcp_interface.md to keep it in sync with
the implementation.
"""

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class StepStatus(StrEnum):
    """Status returned from finished_step."""

    NEEDS_WORK = "needs_work"
    NEXT_STEP = "next_step"
    WORKFLOW_COMPLETE = "workflow_complete"


# =============================================================================
# Shared Argument Value Type
# =============================================================================


ArgumentValue = str | list[str]
"""Value for a step argument.

For file_path type arguments: a single string path or list of string paths.
For string type arguments: a single string value.
"""


# =============================================================================
# Workflow Info Models
# NOTE: These models are returned by get_workflows tool.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class WorkflowInfo(BaseModel):
    """Information about a workflow."""

    name: str = Field(description="Workflow identifier")
    summary: str = Field(description="Short description of workflow")
    how_to_invoke: str = Field(
        description="Instructions for how to invoke this workflow (e.g., directly via MCP tools, or delegated to a sub-agent)",
    )


class JobInfo(BaseModel):
    """Information about a job and its workflows."""

    name: str = Field(description="Job identifier")
    summary: str = Field(description="Short summary of the job")
    workflows: list[WorkflowInfo] = Field(default_factory=list)


# =============================================================================
# Tool Input Models
# NOTE: Changes to these models affect MCP tool parameters.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class StartWorkflowInput(BaseModel):
    """Input for start_workflow tool."""

    goal: str = Field(description="What the user wants to accomplish")
    job_name: str = Field(description="Name of the job")
    workflow_name: str = Field(description="Name of the workflow within the job")
    inputs: dict[str, ArgumentValue] | None = Field(
        default=None,
        description=(
            "Optional input values for the first step. Map of step_argument names to values. "
            "For file_path type arguments: pass a file path string or list of file path strings. "
            "For string type arguments: pass a string value. "
            "These values are made available to the first step and flow through the workflow."
        ),
    )
    session_id: str | None = Field(
        default=None,
        description=(
            "Session identifier for persistent state storage. "
            "For Claude Code: use CLAUDE_CODE_SESSION_ID from startup context. "
            "For other platforms: omit to have the server auto-generate a stable session ID, "
            "then use the session_id returned in begin_step for all subsequent calls."
        ),
    )
    agent_id: str | None = Field(
        default=None,
        description=(
            "Agent identifier for sub-agent scoping (CLAUDE_CODE_AGENT_ID from startup context "
            "on Claude Code). When set, this workflow is scoped to this agent — "
            "other agents in the same session won't see it in their stack."
        ),
    )


class FinishedStepInput(BaseModel):
    """Input for finished_step tool."""

    outputs: dict[str, ArgumentValue] = Field(
        description=(
            "Map of step_argument names to values. "
            "For outputs declared with type 'file_path': pass a single string path or list of paths. "
            "For outputs declared with type 'string': pass a string value. "
            "Outputs with required: false can be omitted from this map. "
            "Check step_expected_outputs from start_workflow/finished_step response "
            "to see each output's type and required status."
        )
    )
    work_summary: str | None = Field(
        default=None,
        description=(
            "Summary of the work done in this step. Used by process_requirements "
            "reviews to evaluate whether the work process met quality criteria. "
            "Include key decisions, approaches taken, and any deviations from the instructions."
        ),
    )
    quality_review_override_reason: str | None = Field(
        default=None,
        description="If provided, skips the quality gate review. Must explain why the review is being bypassed.",
    )
    session_id: str = Field(
        description=(
            "Session identifier from the start_workflow response (begin_step.session_id). "
            "Identifies the workflow session to report completion for."
        ),
    )
    agent_id: str | None = Field(
        default=None,
        description=(
            "Agent identifier for sub-agent scoping (CLAUDE_CODE_AGENT_ID from startup context "
            "on Claude Code). When set, operates on this agent's scoped workflow stack."
        ),
    )


class AbortWorkflowInput(BaseModel):
    """Input for abort_workflow tool."""

    explanation: str = Field(description="Explanation of why the workflow is being aborted")
    session_id: str = Field(
        description=(
            "Session identifier from the start_workflow response (begin_step.session_id). "
            "Identifies the workflow session to abort."
        ),
    )
    agent_id: str | None = Field(
        default=None,
        description=(
            "Agent identifier for sub-agent scoping (CLAUDE_CODE_AGENT_ID from startup context "
            "on Claude Code). When set, operates on this agent's scoped workflow stack."
        ),
    )


class GoToStepInput(BaseModel):
    """Input for go_to_step tool."""

    step_id: str = Field(description="Name of the step to navigate back to")
    session_id: str = Field(
        description=(
            "Session identifier from the start_workflow response (begin_step.session_id). "
            "Identifies the workflow session for navigation."
        ),
    )
    agent_id: str | None = Field(
        default=None,
        description=(
            "Agent identifier for sub-agent scoping (CLAUDE_CODE_AGENT_ID from startup context "
            "on Claude Code). When set, operates on this agent's scoped workflow stack."
        ),
    )


# =============================================================================
# Tool Output Models
# NOTE: Changes to these models affect MCP tool return types.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class ExpectedOutput(BaseModel):
    """Describes an expected output for a step."""

    name: str = Field(
        description="Output name (step_argument name, use as key in finished_step outputs)"
    )
    type: str = Field(description="Argument type: 'file_path' or 'string'")
    description: str = Field(description="What this output should contain")
    required: bool = Field(
        description="Whether this output must be provided. If false, it can be omitted from finished_step outputs."
    )
    syntax_for_finished_step_tool: str = Field(
        description="The value format to use for this output when calling finished_step"
    )


class StepInputInfo(BaseModel):
    """Information about an input provided to a step."""

    name: str = Field(description="Step argument name")
    type: str = Field(description="Argument type: 'file_path' or 'string'")
    description: str = Field(description="What this input represents")
    value: ArgumentValue | None = Field(
        default=None, description="The input value (file path or string content), if available"
    )
    required: bool = Field(default=True, description="Whether this input is required")


class ActiveStepInfo(BaseModel):
    """Information about the step to begin working on."""

    session_id: str = Field(
        description=(
            "The session ID for this workflow. "
            "Use this value as session_id in all subsequent calls to finished_step, "
            "abort_workflow, and go_to_step."
        )
    )
    step_id: str = Field(description="Name of the current step")
    project_root: str = Field(
        description="Absolute path to the MCP server's project root. "
        "Use this as the base directory for .deepwork/ operations "
        "(e.g. creating jobs at [project_root]/.deepwork/jobs/)."
    )
    job_dir: str = Field(
        description="Absolute path to the job directory. Templates, scripts, "
        "and other files referenced in step instructions live here."
    )
    step_expected_outputs: list[ExpectedOutput] = Field(
        description="Expected outputs for this step, including type and format hints"
    )
    step_inputs: list[StepInputInfo] = Field(
        default_factory=list, description="Inputs provided to this step with their values"
    )
    step_instructions: str = Field(description="Instructions for the step")
    common_job_info: str = Field(
        default="",
        description="Common context and information shared across all steps in this workflow",
    )


class JobLoadErrorInfo(BaseModel):
    """A job that failed to load due to a parse or validation error."""

    job_name: str = Field(description="Directory name of the job that failed")
    job_dir: str = Field(description="Absolute path to the job directory")
    error: str = Field(description="Detailed error message explaining why the job failed to load")


class GetWorkflowsResponse(BaseModel):
    """Response from get_workflows tool."""

    jobs: list[JobInfo] = Field(description="List of all jobs with their workflows")
    errors: list[JobLoadErrorInfo] = Field(
        default_factory=list,
        description="Jobs that failed to load, with detailed error messages",
    )


class StackEntry(BaseModel):
    """An entry in the workflow stack."""

    workflow: str = Field(description="Workflow identifier (job_name/workflow_name)")
    step: str = Field(description="Current step name in this workflow")


class StartWorkflowResponse(BaseModel):
    """Response from start_workflow tool."""

    important_note: str = Field(
        default=(
            "IMPORTANT: If, given the info on the workflow you now have, the user's request "
            "seems ambiguous and can be interpreted several ways, you MUST use AskUserQuestion "
            "to clarify their intent if that tool is available."
        ),
        description="Important instruction for the agent",
    )
    begin_step: ActiveStepInfo = Field(description="Information about the first step to begin")
    stack: list[StackEntry] = Field(
        default_factory=list, description="Current workflow stack after starting"
    )


class FinishedStepResponse(BaseModel):
    """Response from finished_step tool."""

    status: StepStatus = Field(description="Result status")

    # For needs_work status
    feedback: str | None = Field(default=None, description="Feedback from quality reviews")

    # For next_step status
    begin_step: ActiveStepInfo | None = Field(
        default=None, description="Information about the next step to begin"
    )

    # For workflow_complete status
    summary: str | None = Field(default=None, description="Summary of completed workflow")
    all_outputs: dict[str, ArgumentValue] | None = Field(
        default=None, description="All outputs from all steps"
    )
    post_workflow_instructions: str | None = Field(
        default=None, description="Instructions for after workflow completion"
    )

    # Stack info (included in all responses)
    stack: list[StackEntry] = Field(
        default_factory=list, description="Current workflow stack after this operation"
    )


class AbortWorkflowResponse(BaseModel):
    """Response from abort_workflow tool."""

    aborted_workflow: str = Field(
        description="The workflow that was aborted (job_name/workflow_name)"
    )
    aborted_step: str = Field(description="The step that was active when aborted")
    explanation: str = Field(description="The explanation provided for aborting")
    stack: list[StackEntry] = Field(
        default_factory=list, description="Current workflow stack after abort"
    )
    resumed_workflow: str | None = Field(
        default=None, description="The workflow now active (if any)"
    )
    resumed_step: str | None = Field(default=None, description="The step now active (if any)")


class GoToStepResponse(BaseModel):
    """Response from go_to_step tool."""

    begin_step: ActiveStepInfo = Field(description="Information about the step to begin working on")
    invalidated_steps: list[str] = Field(
        description="Step names whose progress was cleared (from target step onward)"
    )
    stack: list[StackEntry] = Field(
        default_factory=list, description="Current workflow stack after navigation"
    )


# =============================================================================
# Session Job Models
# NOTE: These models support register_session_job / get_session_job tools.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class RegisterSessionJobInput(BaseModel):
    """Input for register_session_job tool."""

    job_name: str = Field(description="Name for the session job (must match ^[a-z][a-z0-9_]*$)")
    job_definition_yaml: str = Field(
        description="The full content of a job.yml definition as a YAML string"
    )
    session_id: str = Field(
        description=(
            "Session identifier. On Claude Code: pass CLAUDE_CODE_SESSION_ID. "
            "The job is stored under this session and discoverable by start_workflow."
        ),
    )


class GetSessionJobInput(BaseModel):
    """Input for get_session_job tool."""

    job_name: str = Field(description="Name of the session job to retrieve")
    session_id: str = Field(
        description="Session identifier used when the job was registered.",
    )


# =============================================================================
# Session State Models
# =============================================================================


class StepProgress(BaseModel):
    """Progress for a single step in a workflow."""

    step_id: str = Field(description="Step name")
    started_at: str | None = Field(default=None, description="ISO timestamp when started")
    completed_at: str | None = Field(default=None, description="ISO timestamp when completed")
    outputs: dict[str, ArgumentValue] = Field(
        default_factory=dict, description="Output values produced"
    )
    work_summary: str | None = Field(default=None, description="Summary of work done")
    input_values: dict[str, ArgumentValue] = Field(
        default_factory=dict, description="Input values provided to this step"
    )
    quality_attempts: int = Field(default=0, description="Number of quality gate attempts")
    sub_workflow_instance_ids: list[str] = Field(
        default_factory=list,
        description="Instance IDs of sub-workflows started from this step",
    )


class StepHistoryEntry(BaseModel):
    """An entry in the step execution history."""

    step_id: str = Field(description="Step identifier")
    started_at: str | None = Field(default=None, description="ISO timestamp when started")
    finished_at: str | None = Field(default=None, description="ISO timestamp when finished")
    sub_workflow_instance_ids: list[str] = Field(
        default_factory=list,
        description="Instance IDs of sub-workflows started during this step execution",
    )


class WorkflowSession(BaseModel):
    """State for an active workflow session."""

    session_id: str = Field(
        description="Session identifier used as the storage key for this workflow's state."
    )
    workflow_instance_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique identifier for this workflow instance",
    )
    job_name: str = Field(description="Name of the job")
    workflow_name: str = Field(description="Name of the workflow")
    goal: str = Field(description="User's goal for this workflow")
    current_step_id: str = Field(description="Current step name in workflow")
    current_step_index: int = Field(
        default=0, description="Index of current step in workflow steps list"
    )
    step_progress: dict[str, StepProgress] = Field(
        default_factory=dict, description="Progress for each step"
    )
    step_history: list[StepHistoryEntry] = Field(
        default_factory=list, description="Ordered history of step executions"
    )
    started_at: str = Field(description="ISO timestamp when session started")
    completed_at: str | None = Field(default=None, description="ISO timestamp when completed")
    status: str = Field(default="active", description="Session status: active, completed, aborted")
    abort_reason: str | None = Field(
        default=None, description="Explanation if workflow was aborted"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowSession":
        """Create from dictionary."""
        return cls.model_validate(data)
