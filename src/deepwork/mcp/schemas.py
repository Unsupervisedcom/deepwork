"""Pydantic models for MCP tool inputs and outputs.

IMPORTANT: If you modify any models in this file that affect the MCP tool
interfaces (input models, output models, or their fields), you MUST also
update the documentation in doc/mcp_interface.md to keep it in sync with
the implementation.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class StepStatus(str, Enum):
    """Status returned from finished_step."""

    NEEDS_WORK = "needs_work"
    NEXT_STEP = "next_step"
    WORKFLOW_COMPLETE = "workflow_complete"


# =============================================================================
# Workflow Info Models
# NOTE: These models are returned by get_workflows tool.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class StepInfo(BaseModel):
    """Information about a single step."""

    id: str = Field(description="Step identifier")
    name: str = Field(description="Human-readable step name")
    description: str = Field(description="What the step does")
    dependencies: list[str] = Field(default_factory=list, description="Required prior steps")


class ConcurrentStepGroup(BaseModel):
    """A group of steps that can be executed concurrently."""

    step_ids: list[str] = Field(description="Steps that run in parallel")
    is_concurrent: bool = Field(default=True)


class WorkflowStepEntryInfo(BaseModel):
    """Information about a workflow step entry (sequential or concurrent)."""

    step_ids: list[str] = Field(description="Step ID(s) in this entry")
    is_concurrent: bool = Field(
        default=False, description="True if steps run in parallel"
    )


class WorkflowInfo(BaseModel):
    """Information about a workflow."""

    name: str = Field(description="Workflow identifier")
    summary: str = Field(description="Short description of workflow")


class JobInfo(BaseModel):
    """Information about a job and its workflows."""

    name: str = Field(description="Job identifier")
    summary: str = Field(description="Short summary of the job")
    description: str | None = Field(default=None, description="Full description")
    workflows: list[WorkflowInfo] = Field(default_factory=list)
    standalone_steps: list[StepInfo] = Field(
        default_factory=list, description="Steps not in any workflow"
    )


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
    instance_id: str | None = Field(
        default=None,
        description="Optional identifier (e.g., 'acme', 'q1-2026')",
    )


class FinishedStepInput(BaseModel):
    """Input for finished_step tool."""

    outputs: list[str] = Field(description="List of output file paths created")
    notes: str | None = Field(default=None, description="Optional notes about work done")
    quality_review_override_reason: str | None = Field(
        default=None,
        description="If provided, skips the quality gate review. Must explain why the review is being bypassed.",
    )


# =============================================================================
# Quality Gate Models
# =============================================================================


class QualityCriteriaResult(BaseModel):
    """Result for a single quality criterion."""

    criterion: str = Field(description="The quality criterion text")
    passed: bool = Field(description="Whether this criterion passed")
    feedback: str | None = Field(default=None, description="Feedback if failed")


class QualityGateResult(BaseModel):
    """Result from quality gate evaluation."""

    passed: bool = Field(description="Overall pass/fail")
    feedback: str = Field(description="Summary feedback")
    criteria_results: list[QualityCriteriaResult] = Field(
        default_factory=list, description="Per-criterion results"
    )


# =============================================================================
# Tool Output Models
# NOTE: Changes to these models affect MCP tool return types.
#       Update doc/mcp_interface.md when modifying.
# =============================================================================


class ActiveStepInfo(BaseModel):
    """Information about the step to begin working on."""

    session_id: str = Field(description="Unique session identifier")
    branch_name: str = Field(description="Git branch for this workflow instance")
    step_id: str = Field(description="ID of the current step")
    step_expected_outputs: list[str] = Field(description="Expected output files for this step")
    step_quality_criteria: list[str] = Field(
        default_factory=list, description="Criteria for step completion"
    )
    step_instructions: str = Field(description="Instructions for the step")


class GetWorkflowsResponse(BaseModel):
    """Response from get_workflows tool."""

    jobs: list[JobInfo] = Field(description="List of all jobs with their workflows")


class StartWorkflowResponse(BaseModel):
    """Response from start_workflow tool."""

    begin_step: ActiveStepInfo = Field(description="Information about the first step to begin")


class FinishedStepResponse(BaseModel):
    """Response from finished_step tool."""

    status: StepStatus = Field(description="Result status")

    # For needs_work status
    feedback: str | None = Field(default=None, description="Feedback from quality gate")
    failed_criteria: list[QualityCriteriaResult] | None = Field(
        default=None, description="Failed quality criteria"
    )

    # For next_step status
    begin_step: ActiveStepInfo | None = Field(
        default=None, description="Information about the next step to begin"
    )

    # For workflow_complete status
    summary: str | None = Field(
        default=None, description="Summary of completed workflow"
    )
    all_outputs: list[str] | None = Field(
        default=None, description="All outputs from all steps"
    )


# =============================================================================
# Session State Models
# =============================================================================


class StepProgress(BaseModel):
    """Progress for a single step in a workflow."""

    step_id: str = Field(description="Step identifier")
    started_at: str | None = Field(default=None, description="ISO timestamp when started")
    completed_at: str | None = Field(
        default=None, description="ISO timestamp when completed"
    )
    outputs: list[str] = Field(default_factory=list, description="Output files created")
    notes: str | None = Field(default=None, description="Notes from agent")
    quality_attempts: int = Field(default=0, description="Number of quality gate attempts")


class WorkflowSession(BaseModel):
    """State for an active workflow session."""

    session_id: str = Field(description="Unique session identifier")
    job_name: str = Field(description="Name of the job")
    workflow_name: str = Field(description="Name of the workflow")
    instance_id: str | None = Field(default=None, description="Instance identifier")
    goal: str = Field(description="User's goal for this workflow")
    branch_name: str = Field(description="Git branch name")
    current_step_id: str = Field(description="Current step in workflow")
    current_entry_index: int = Field(
        default=0, description="Index of current entry in step_entries"
    )
    step_progress: dict[str, StepProgress] = Field(
        default_factory=dict, description="Progress for each step"
    )
    started_at: str = Field(description="ISO timestamp when session started")
    completed_at: str | None = Field(
        default=None, description="ISO timestamp when completed"
    )
    status: str = Field(default="active", description="Session status")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowSession":
        """Create from dictionary."""
        return cls.model_validate(data)
