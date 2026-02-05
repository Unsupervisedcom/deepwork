"""MCP tool implementations for DeepWork workflows.

This module provides the core tools for guiding agents through workflows:
- get_workflows: List all available workflows
- start_workflow: Initialize a workflow session
- finished_step: Report step completion and get next instructions
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from deepwork.core.parser import JobDefinition, ParseError, Workflow, parse_job_definition
from deepwork.mcp.schemas import (
    AbortWorkflowInput,
    AbortWorkflowResponse,
    ActiveStepInfo,
    FinishedStepInput,
    FinishedStepResponse,
    GetWorkflowsResponse,
    JobInfo,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepStatus,
    WorkflowInfo,
)
from deepwork.mcp.state import StateManager

if TYPE_CHECKING:
    from deepwork.mcp.quality_gate import QualityGate


class ToolError(Exception):
    """Exception raised for tool execution errors."""

    pass


class WorkflowTools:
    """Implements the MCP tools for workflow management."""

    def __init__(
        self,
        project_root: Path,
        state_manager: StateManager,
        quality_gate: QualityGate | None = None,
        max_quality_attempts: int = 3,
    ):
        """Initialize workflow tools.

        Args:
            project_root: Path to project root
            state_manager: State manager instance
            quality_gate: Optional quality gate for step validation
            max_quality_attempts: Maximum attempts before failing quality gate
        """
        self.project_root = project_root
        self.jobs_dir = project_root / ".deepwork" / "jobs"
        self.state_manager = state_manager
        self.quality_gate = quality_gate
        self.max_quality_attempts = max_quality_attempts

    def _load_all_jobs(self) -> list[JobDefinition]:
        """Load all job definitions from the jobs directory.

        Returns:
            List of parsed JobDefinition objects
        """
        jobs: list[JobDefinition] = []

        if not self.jobs_dir.exists():
            return jobs

        for job_dir in self.jobs_dir.iterdir():
            if job_dir.is_dir() and (job_dir / "job.yml").exists():
                try:
                    job = parse_job_definition(job_dir)
                    jobs.append(job)
                except ParseError:
                    # Skip invalid job definitions
                    continue

        return jobs

    def _job_to_info(self, job: JobDefinition) -> JobInfo:
        """Convert a JobDefinition to JobInfo for response.

        Args:
            job: Parsed job definition

        Returns:
            JobInfo with workflow details
        """
        # Convert workflows
        workflows = [
            WorkflowInfo(
                name=wf.name,
                summary=wf.summary,
            )
            for wf in job.workflows
        ]

        return JobInfo(
            name=job.name,
            summary=job.summary,
            description=job.description,
            workflows=workflows,
        )

    def _get_job(self, job_name: str) -> JobDefinition:
        """Get a specific job by name.

        Args:
            job_name: Job name to find

        Returns:
            JobDefinition

        Raises:
            ToolError: If job not found
        """
        job_dir = self.jobs_dir / job_name
        if not job_dir.exists():
            raise ToolError(f"Job not found: {job_name}")

        try:
            return parse_job_definition(job_dir)
        except ParseError as e:
            raise ToolError(f"Failed to parse job '{job_name}': {e}") from e

    def _get_workflow(self, job: JobDefinition, workflow_name: str) -> Workflow:
        """Get a specific workflow from a job.

        If the workflow name doesn't match any workflow but the job has exactly
        one workflow, that workflow is returned automatically.

        Args:
            job: Job definition
            workflow_name: Workflow name to find

        Returns:
            Workflow

        Raises:
            ToolError: If workflow not found and job has multiple workflows
        """
        for wf in job.workflows:
            if wf.name == workflow_name:
                return wf

        # Auto-select if there's only one workflow
        if len(job.workflows) == 1:
            return job.workflows[0]

        available = [wf.name for wf in job.workflows]
        raise ToolError(
            f"Workflow '{workflow_name}' not found in job '{job.name}'. "
            f"Available workflows: {', '.join(available)}"
        )

    def _get_step_instructions(self, job: JobDefinition, step_id: str) -> str:
        """Get the instruction content for a step.

        Args:
            job: Job definition
            step_id: Step ID

        Returns:
            Step instruction content

        Raises:
            ToolError: If step or instruction file not found
        """
        step = job.get_step(step_id)
        if step is None:
            raise ToolError(f"Step not found: {step_id}")

        instructions_path = job.job_dir / step.instructions_file
        if not instructions_path.exists():
            raise ToolError(f"Instructions file not found: {step.instructions_file}")

        return instructions_path.read_text(encoding="utf-8")

    # =========================================================================
    # Tool Implementations
    # =========================================================================

    def get_workflows(self) -> GetWorkflowsResponse:
        """List all available workflows.

        Returns:
            GetWorkflowsResponse with all jobs and their workflows
        """
        jobs = self._load_all_jobs()
        job_infos = [self._job_to_info(job) for job in jobs]

        return GetWorkflowsResponse(jobs=job_infos)

    async def start_workflow(self, input_data: StartWorkflowInput) -> StartWorkflowResponse:
        """Start a new workflow session.

        Args:
            input_data: StartWorkflowInput with goal, job_name, workflow_name

        Returns:
            StartWorkflowResponse with session ID, branch, and first step

        Raises:
            ToolError: If job or workflow not found
        """
        # Load job and workflow
        job = self._get_job(input_data.job_name)
        workflow = self._get_workflow(job, input_data.workflow_name)

        if not workflow.steps:
            raise ToolError(f"Workflow '{workflow.name}' has no steps")

        first_step_id = workflow.steps[0]
        first_step = job.get_step(first_step_id)
        if first_step is None:
            raise ToolError(f"First step not found: {first_step_id}")

        # Create session (use resolved workflow name in case it was auto-selected)
        session = await self.state_manager.create_session(
            job_name=input_data.job_name,
            workflow_name=workflow.name,
            goal=input_data.goal,
            first_step_id=first_step_id,
            instance_id=input_data.instance_id,
        )

        # Mark first step as started
        await self.state_manager.start_step(first_step_id)

        # Get step instructions
        instructions = self._get_step_instructions(job, first_step_id)

        # Get expected outputs
        step_outputs = [out.file for out in first_step.outputs]

        return StartWorkflowResponse(
            begin_step=ActiveStepInfo(
                session_id=session.session_id,
                branch_name=session.branch_name,
                step_id=first_step_id,
                step_expected_outputs=step_outputs,
                step_quality_criteria=first_step.quality_criteria,
                step_instructions=instructions,
            ),
            stack=self.state_manager.get_stack(),
        )

    async def finished_step(self, input_data: FinishedStepInput) -> FinishedStepResponse:
        """Report step completion and get next instructions.

        Args:
            input_data: FinishedStepInput with outputs and optional notes

        Returns:
            FinishedStepResponse with status and next step or completion

        Raises:
            StateError: If no active session
            ToolError: If quality gate fails after max attempts
        """
        session = self.state_manager.require_active_session()
        current_step_id = session.current_step_id

        # Load job and workflow
        job = self._get_job(session.job_name)
        workflow = self._get_workflow(job, session.workflow_name)
        current_step = job.get_step(current_step_id)

        if current_step is None:
            raise ToolError(f"Current step not found: {current_step_id}")

        # Run quality gate if available and step has criteria (unless overridden)
        if (
            self.quality_gate
            and current_step.quality_criteria
            and not input_data.quality_review_override_reason
        ):
            attempts = await self.state_manager.record_quality_attempt(current_step_id)

            result = await self.quality_gate.evaluate(
                quality_criteria=current_step.quality_criteria,
                outputs=input_data.outputs,
                project_root=self.project_root,
            )

            if not result.passed:
                # Check max attempts
                if attempts >= self.max_quality_attempts:
                    raise ToolError(
                        f"Quality gate failed after {self.max_quality_attempts} attempts. "
                        f"Feedback: {result.feedback}"
                    )

                # Return needs_work status
                failed_criteria = [cr for cr in result.criteria_results if not cr.passed]
                return FinishedStepResponse(
                    status=StepStatus.NEEDS_WORK,
                    feedback=result.feedback,
                    failed_criteria=failed_criteria,
                    stack=self.state_manager.get_stack(),
                )

        # Mark step as completed
        await self.state_manager.complete_step(
            step_id=current_step_id,
            outputs=input_data.outputs,
            notes=input_data.notes,
        )

        # Find next step
        current_entry_index = session.current_entry_index
        next_entry_index = current_entry_index + 1

        if next_entry_index >= len(workflow.step_entries):
            # Workflow complete - get outputs before completing (which pops from stack)
            all_outputs = self.state_manager.get_all_outputs()
            await self.state_manager.complete_workflow()

            return FinishedStepResponse(
                status=StepStatus.WORKFLOW_COMPLETE,
                summary=f"Workflow '{workflow.name}' completed successfully!",
                all_outputs=all_outputs,
                stack=self.state_manager.get_stack(),
            )

        # Get next step
        next_entry = workflow.step_entries[next_entry_index]

        # For concurrent entries, we use the first step as the "current"
        # The agent will handle running them in parallel via Task tool
        next_step_id = next_entry.step_ids[0]
        next_step = job.get_step(next_step_id)

        if next_step is None:
            raise ToolError(f"Next step not found: {next_step_id}")

        # Advance session
        await self.state_manager.advance_to_step(next_step_id, next_entry_index)
        await self.state_manager.start_step(next_step_id)

        # Get instructions
        instructions = self._get_step_instructions(job, next_step_id)
        step_outputs = [out.file for out in next_step.outputs]

        # Add info about concurrent steps if this is a concurrent entry
        if next_entry.is_concurrent and len(next_entry.step_ids) > 1:
            concurrent_info = (
                f"\n\n**CONCURRENT STEPS**: This entry has {len(next_entry.step_ids)} "
                f"steps that can run in parallel: {', '.join(next_entry.step_ids)}\n"
                f"Use the Task tool to execute them concurrently."
            )
            instructions = instructions + concurrent_info

        # Reload session to get current state after advance
        session = self.state_manager.require_active_session()

        return FinishedStepResponse(
            status=StepStatus.NEXT_STEP,
            begin_step=ActiveStepInfo(
                session_id=session.session_id,
                branch_name=session.branch_name,
                step_id=next_step_id,
                step_expected_outputs=step_outputs,
                step_quality_criteria=next_step.quality_criteria,
                step_instructions=instructions,
            ),
            stack=self.state_manager.get_stack(),
        )

    async def abort_workflow(self, input_data: AbortWorkflowInput) -> AbortWorkflowResponse:
        """Abort the current workflow and return to the previous one.

        Args:
            input_data: AbortWorkflowInput with explanation

        Returns:
            AbortWorkflowResponse with abort info and new stack state

        Raises:
            StateError: If no active session
        """
        aborted_session, new_active = await self.state_manager.abort_workflow(
            input_data.explanation
        )

        return AbortWorkflowResponse(
            aborted_workflow=f"{aborted_session.job_name}/{aborted_session.workflow_name}",
            aborted_step=aborted_session.current_step_id,
            explanation=input_data.explanation,
            stack=self.state_manager.get_stack(),
            resumed_workflow=(
                f"{new_active.job_name}/{new_active.workflow_name}" if new_active else None
            ),
            resumed_step=new_active.current_step_id if new_active else None,
        )
