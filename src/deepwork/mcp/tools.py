"""MCP tool implementations for DeepWork workflows.

This module provides the core tools for guiding agents through workflows:
- get_workflows: List all available workflows
- start_workflow: Initialize a workflow session
- finished_step: Report step completion and get next instructions
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from deepwork.core.jobs import find_job_dir, load_all_jobs
from deepwork.core.parser import (
    JobDefinition,
    OutputSpec,
    ParseError,
    Workflow,
    parse_job_definition,
)
from deepwork.mcp.schemas import (
    AbortWorkflowInput,
    AbortWorkflowResponse,
    ActiveStepInfo,
    ExpectedOutput,
    FinishedStepInput,
    FinishedStepResponse,
    GetWorkflowsResponse,
    JobInfo,
    ReviewInfo,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepStatus,
    WorkflowInfo,
)
from deepwork.mcp.state import StateManager

logger = logging.getLogger("deepwork.mcp")

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
        external_runner: str | None = None,
    ):
        """Initialize workflow tools.

        Args:
            project_root: Path to project root
            state_manager: State manager instance
            quality_gate: Optional quality gate for step validation
            max_quality_attempts: Maximum attempts before failing quality gate
            external_runner: External runner for quality gate reviews.
                "claude" uses Claude CLI subprocess. None means agent self-review.
        """
        self.project_root = project_root
        self.state_manager = state_manager
        self.quality_gate = quality_gate
        self.max_quality_attempts = max_quality_attempts
        self.external_runner = external_runner

    def _load_all_jobs(self) -> list[JobDefinition]:
        """Load all job definitions from all configured job folders.

        Returns:
            List of parsed JobDefinition objects
        """
        return load_all_jobs(self.project_root)

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

        Searches all configured job folders for the named job.

        Args:
            job_name: Job name to find

        Returns:
            JobDefinition

        Raises:
            ToolError: If job not found
        """
        job_dir = find_job_dir(self.project_root, job_name)
        if job_dir is None:
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

    def _validate_outputs(
        self,
        submitted: dict[str, str | list[str]],
        declared: list[OutputSpec],
    ) -> None:
        """Validate submitted outputs against declared output specs.

        Checks:
        1. Every submitted key matches a declared output name
        2. Every declared output has a corresponding submitted key
        3. type: file -> value is a single string path, file must exist
        4. type: files -> value is a list of strings, each file must exist

        Args:
            submitted: The outputs dict from the agent
            declared: The OutputSpec list from the step definition

        Raises:
            ToolError: If validation fails
        """
        declared_map = {spec.name: spec for spec in declared}
        declared_names = set(declared_map.keys())
        submitted_names = set(submitted.keys())

        # Check for unknown output keys
        extra = submitted_names - declared_names
        if extra:
            raise ToolError(
                f"Unknown output names: {', '.join(sorted(extra))}. "
                f"Declared outputs: {', '.join(sorted(declared_names))}"
            )

        # Check for missing required output keys
        required_names = {spec.name for spec in declared if spec.required}
        missing = required_names - submitted_names
        if missing:
            raise ToolError(
                f"Missing required outputs: {', '.join(sorted(missing))}. "
                f"All required outputs must be provided."
            )

        # Validate types and file existence
        for name, value in submitted.items():
            spec = declared_map[name]

            if spec.type == "file":
                if not isinstance(value, str):
                    raise ToolError(
                        f"Output '{name}' is declared as type 'file' and must be a "
                        f"single string path, got {type(value).__name__}"
                    )
                full_path = self.project_root / value
                if not full_path.exists():
                    raise ToolError(f"Output '{name}': file not found at '{value}'")

            elif spec.type == "files":
                if not isinstance(value, list):
                    raise ToolError(
                        f"Output '{name}' is declared as type 'files' and must be a "
                        f"list of paths, got {type(value).__name__}"
                    )
                for path in value:
                    if not isinstance(path, str):
                        raise ToolError(
                            f"Output '{name}': all paths must be strings, got {type(path).__name__}"
                        )
                    full_path = self.project_root / path
                    if not full_path.exists():
                        raise ToolError(f"Output '{name}': file not found at '{path}'")

    @staticmethod
    def _build_expected_outputs(outputs: list[OutputSpec]) -> list[ExpectedOutput]:
        """Build ExpectedOutput list from OutputSpec list."""
        syntax_map = {
            "file": "filepath",
            "files": "array of filepaths for all individual files",
        }
        return [
            ExpectedOutput(
                name=out.name,
                type=out.type,
                description=out.description,
                required=out.required,
                syntax_for_finished_step_tool=syntax_map.get(out.type, out.type),
            )
            for out in outputs
        ]

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
        step_outputs = self._build_expected_outputs(first_step.outputs)

        return StartWorkflowResponse(
            begin_step=ActiveStepInfo(
                session_id=session.session_id,
                branch_name=session.branch_name,
                step_id=first_step_id,
                step_expected_outputs=step_outputs,
                step_reviews=[
                    ReviewInfo(
                        run_each=r.run_each,
                        quality_criteria=r.quality_criteria,
                        additional_review_guidance=r.additional_review_guidance,
                    )
                    for r in first_step.reviews
                ],
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
        session = self.state_manager._resolve_session(input_data.session_id)
        sid = session.session_id
        current_step_id = session.current_step_id

        # Load job and workflow
        job = self._get_job(session.job_name)
        workflow = self._get_workflow(job, session.workflow_name)
        current_step = job.get_step(current_step_id)

        if current_step is None:
            raise ToolError(f"Current step not found: {current_step_id}")

        # Validate outputs against step's declared output specs
        self._validate_outputs(input_data.outputs, current_step.outputs)

        # Run quality gate if available and step has reviews (unless overridden)
        if (
            self.quality_gate
            and current_step.reviews
            and not input_data.quality_review_override_reason
        ):
            # Build review dicts and output specs used by both paths
            review_dicts = [
                {
                    "run_each": r.run_each,
                    "quality_criteria": r.quality_criteria,
                    "additional_review_guidance": r.additional_review_guidance,
                }
                for r in current_step.reviews
            ]
            output_specs = {out.name: out.type for out in current_step.outputs}

            if self.external_runner is None:
                # Self-review mode: build instructions file and return guidance
                # to the agent to verify its own work via a subagent.
                review_content = await self.quality_gate.build_review_instructions_file(
                    reviews=review_dicts,
                    outputs=input_data.outputs,
                    output_specs=output_specs,
                    project_root=self.project_root,
                    notes=input_data.notes,
                )

                # Write instructions to .deepwork/tmp/
                tmp_dir = self.project_root / ".deepwork" / "tmp"
                tmp_dir.mkdir(parents=True, exist_ok=True)
                review_filename = f"quality_review_{sid}_{current_step_id}.md"
                review_file_path = tmp_dir / review_filename
                async with aiofiles.open(review_file_path, "w", encoding="utf-8") as f:
                    await f.write(review_content)

                relative_path = f".deepwork/tmp/{review_filename}"
                feedback = (
                    f"Quality review required. Review instructions have been written to: "
                    f"{relative_path}\n\n"
                    f"Verify the quality of your work:\n"
                    f'1. Spawn a subagent with the prompt: "Read the file at '
                    f"{relative_path} and follow the instructions in it. "
                    f"Review the referenced output files and evaluate them against "
                    f'the criteria specified. Report your detailed findings."\n'
                    f"2. Review the subagent's findings\n"
                    f"3. Fix any issues identified by the subagent\n"
                    f"4. Repeat steps 1-3 until all criteria pass\n"
                    f"5. Once all criteria pass, call finished_step again with "
                    f"quality_review_override_reason set to describe the "
                    f"review outcome (e.g. 'Self-review passed: all criteria met')"
                )

                return FinishedStepResponse(
                    status=StepStatus.NEEDS_WORK,
                    feedback=feedback,
                    stack=self.state_manager.get_stack(),
                )
            else:
                # External runner mode: use quality gate subprocess evaluation
                attempts = await self.state_manager.record_quality_attempt(
                    current_step_id, session_id=sid
                )

                failed_reviews = await self.quality_gate.evaluate_reviews(
                    reviews=review_dicts,
                    outputs=input_data.outputs,
                    output_specs=output_specs,
                    project_root=self.project_root,
                    notes=input_data.notes,
                )

                if failed_reviews:
                    # Check max attempts
                    if attempts >= self.max_quality_attempts:
                        feedback_parts = [r.feedback for r in failed_reviews]
                        raise ToolError(
                            f"Quality gate failed after {self.max_quality_attempts} attempts. "
                            f"Feedback: {'; '.join(feedback_parts)}"
                        )

                    # Return needs_work status
                    combined_feedback = "; ".join(r.feedback for r in failed_reviews)
                    return FinishedStepResponse(
                        status=StepStatus.NEEDS_WORK,
                        feedback=combined_feedback,
                        failed_reviews=failed_reviews,
                        stack=self.state_manager.get_stack(),
                    )

        # Mark step as completed
        await self.state_manager.complete_step(
            step_id=current_step_id,
            outputs=input_data.outputs,
            notes=input_data.notes,
            session_id=sid,
        )

        # Find next step
        current_entry_index = session.current_entry_index
        next_entry_index = current_entry_index + 1

        if next_entry_index >= len(workflow.step_entries):
            # Workflow complete - get outputs before completing (which removes from stack)
            all_outputs = self.state_manager.get_all_outputs(session_id=sid)
            await self.state_manager.complete_workflow(session_id=sid)

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
        await self.state_manager.advance_to_step(next_step_id, next_entry_index, session_id=sid)
        await self.state_manager.start_step(next_step_id, session_id=sid)

        # Get instructions
        instructions = self._get_step_instructions(job, next_step_id)
        step_outputs = self._build_expected_outputs(next_step.outputs)

        # Add info about concurrent steps if this is a concurrent entry
        if next_entry.is_concurrent and len(next_entry.step_ids) > 1:
            concurrent_info = (
                f"\n\n**CONCURRENT STEPS**: This entry has {len(next_entry.step_ids)} "
                f"steps that can run in parallel: {', '.join(next_entry.step_ids)}\n"
                f"Use the Task tool to execute them concurrently."
            )
            instructions = instructions + concurrent_info

        # Reload session to get current state after advance
        session = self.state_manager._resolve_session(sid)

        return FinishedStepResponse(
            status=StepStatus.NEXT_STEP,
            begin_step=ActiveStepInfo(
                session_id=session.session_id,
                branch_name=session.branch_name,
                step_id=next_step_id,
                step_expected_outputs=step_outputs,
                step_reviews=[
                    ReviewInfo(
                        run_each=r.run_each,
                        quality_criteria=r.quality_criteria,
                        additional_review_guidance=r.additional_review_guidance,
                    )
                    for r in next_step.reviews
                ],
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
            input_data.explanation, session_id=input_data.session_id
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
