"""MCP tool implementations for DeepWork workflows.

This module provides the core tools for guiding agents through workflows:
- get_workflows: List all available workflows
- start_workflow: Initialize a workflow session
- finished_step: Report step completion and get next instructions
- abort_workflow: Abort the current workflow
- go_to_step: Navigate back to a prior step
- register_session_job: Register a transient job definition for the session
- get_session_job: Retrieve a session-scoped job definition
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import aiofiles

from deepwork.jobs.discovery import JobLoadError, find_job_dir, load_all_jobs
from deepwork.jobs.mcp.quality_gate import run_quality_gate
from deepwork.jobs.mcp.schemas import (
    AbortWorkflowInput,
    AbortWorkflowResponse,
    ActiveStepInfo,
    ArgumentValue,
    ExpectedOutput,
    FinishedStepInput,
    FinishedStepResponse,
    GetSessionJobInput,
    GetWorkflowsResponse,
    GoToStepInput,
    GoToStepResponse,
    JobInfo,
    JobLoadErrorInfo,
    RegisterSessionJobInput,
    StartWorkflowInput,
    StartWorkflowResponse,
    StepInputInfo,
    StepStatus,
    WorkflowInfo,
)
from deepwork.jobs.mcp.state import StateError, StateManager
from deepwork.jobs.parser import (
    JobDefinition,
    ParseError,
    Workflow,
    WorkflowStep,
    parse_job_definition,
)

logger = logging.getLogger("deepwork.jobs.mcp")

if TYPE_CHECKING:
    from deepwork.jobs.mcp.status import StatusWriter


class ToolError(Exception):
    """Exception raised for tool execution errors."""

    pass


class WorkflowTools:
    """Implements the MCP tools for workflow management."""

    def __init__(
        self,
        project_root: Path,
        state_manager: StateManager,
        status_writer: StatusWriter | None = None,
    ):
        """Initialize workflow tools.

        Args:
            project_root: Path to project root
            state_manager: State manager instance
            status_writer: Optional status writer for external status files.
        """
        self.project_root = project_root
        self.state_manager = state_manager
        self.status_writer = status_writer

    @property
    def platform(self) -> str:
        """Return the platform from the state manager."""
        return self.state_manager.platform

    def _resolve_session_id(self, session_id: str | None) -> str:
        """Resolve session_id: require it on Claude Code, auto-generate otherwise."""
        if session_id:
            return session_id
        if self.platform == "claude":
            raise ToolError(
                "session_id is required on Claude Code. "
                "Pass CLAUDE_CODE_SESSION_ID from startup context."
            )
        return uuid4().hex

    def _write_session_status(self, session_id: str) -> None:
        """Write session status file if status_writer is configured.

        Fire-and-forget: exceptions are logged as warnings and never propagated.
        """
        if self.status_writer:
            try:
                self.status_writer.write_session_status(
                    session_id, self.state_manager, self._load_all_jobs
                )
            except Exception:
                logger.warning("Failed to write session status", exc_info=True)

    def _write_manifest(self) -> None:
        """Write job manifest file if status_writer is configured.

        Fire-and-forget: exceptions are logged as warnings and never propagated.
        """
        if self.status_writer:
            try:
                jobs, _ = self._load_all_jobs()
                self.status_writer.write_manifest(jobs)
            except Exception:
                logger.warning("Failed to write job manifest", exc_info=True)

    def _load_all_jobs(self) -> tuple[list[JobDefinition], list[JobLoadError]]:
        """Load all job definitions from all configured job folders."""
        return load_all_jobs(self.project_root)

    def _job_to_info(self, job: JobDefinition) -> JobInfo:
        """Convert a JobDefinition to JobInfo for response."""
        workflows = []
        for wf_name, wf in job.workflows.items():
            if wf.agent:
                how_to_invoke = (
                    f'Invoke as an Agent using subagent_type="{wf.agent}" with a prompt '
                    f"giving full context needed and instructions to call "
                    f"`mcp__plugin_deepwork_deepwork__start_workflow` "
                    f'(job_name="{job.name}", workflow_name="{wf_name}"). '
                    f"If you do not have Agent as an available tool, invoke the workflow directly."
                )
            else:
                how_to_invoke = (
                    f"Call `mcp__plugin_deepwork_deepwork__start_workflow` with "
                    f'job_name="{job.name}" and workflow_name="{wf_name}", '
                    f"then follow the step instructions it returns."
                )
            workflows.append(
                WorkflowInfo(
                    name=wf_name,
                    summary=wf.summary,
                    how_to_invoke=how_to_invoke,
                )
            )

        return JobInfo(
            name=job.name,
            summary=job.summary,
            workflows=workflows,
        )

    def _get_job(self, job_name: str, session_id: str | None = None) -> JobDefinition:
        """Get a specific job by name.

        Checks session-scoped jobs first (if session_id provided),
        then falls back to standard discovery.
        """
        # Check session jobs first
        if session_id:
            session_job_dir = self._session_jobs_dir(session_id) / job_name
            if session_job_dir.is_dir() and (session_job_dir / "job.yml").exists():
                try:
                    return parse_job_definition(session_job_dir)
                except ParseError as e:
                    raise ToolError(f"Failed to parse session job '{job_name}': {e}") from e

        job_dir = find_job_dir(self.project_root, job_name)
        if job_dir is None:
            raise ToolError(f"Job not found: {job_name}")

        try:
            return parse_job_definition(job_dir)
        except ParseError as e:
            raise ToolError(f"Failed to parse job '{job_name}': {e}") from e

    def _get_workflow(self, job: JobDefinition, workflow_name: str) -> Workflow:
        """Get a specific workflow from a job.

        Auto-selects if there's only one workflow.
        """
        wf = job.get_workflow(workflow_name)
        if wf:
            return wf

        # Auto-select if there's only one workflow
        if len(job.workflows) == 1:
            return next(iter(job.workflows.values()))

        available = list(job.workflows.keys())
        raise ToolError(
            f"Workflow '{workflow_name}' not found in job '{job.name}'. "
            f"Available workflows: {', '.join(available)}"
        )

    def _resolve_input_values(
        self,
        step: WorkflowStep,
        job: JobDefinition,
        workflow: Workflow,
        session_id: str,
        agent_id: str | None,
        provided_inputs: dict[str, ArgumentValue] | None = None,
    ) -> dict[str, ArgumentValue]:
        """Resolve input values for a step from previous outputs or provided inputs."""
        values: dict[str, ArgumentValue] = {}

        # Collect all previous step outputs from the session
        try:
            all_outputs = self.state_manager.get_all_outputs(session_id, agent_id)
        except StateError:
            all_outputs = {}

        for input_name, _input_ref in step.inputs.items():
            # Check provided inputs first (from start_workflow)
            if provided_inputs and input_name in provided_inputs:
                values[input_name] = provided_inputs[input_name]
            # Then check previous step outputs
            elif input_name in all_outputs:
                values[input_name] = all_outputs[input_name]

        return values

    def _validate_outputs(
        self,
        submitted: dict[str, ArgumentValue],
        step: WorkflowStep,
        job: JobDefinition,
    ) -> None:
        """Validate submitted outputs against step's declared output refs."""
        declared_names = set(step.outputs.keys())
        submitted_names = set(submitted.keys())

        # Check for unknown output keys
        extra = submitted_names - declared_names
        if extra:
            raise ToolError(
                f"Unknown output names: {', '.join(sorted(extra))}. "
                f"Declared outputs: {', '.join(sorted(declared_names))}"
            )

        # Check for missing required output keys
        required_names = {name for name, ref in step.outputs.items() if ref.required}
        missing = required_names - submitted_names
        if missing:
            raise ToolError(
                f"Missing required outputs: {', '.join(sorted(missing))}. "
                f"All required outputs must be provided."
            )

        # Validate types and file existence
        for name, value in submitted.items():
            arg = job.get_argument(name)
            if not arg:
                continue

            if arg.type == "file_path":
                if isinstance(value, str):
                    full_path = self.project_root / value
                    if not full_path.exists():
                        raise ToolError(f"Output '{name}': file not found at '{value}'")
                elif isinstance(value, list):
                    for path in value:
                        if not isinstance(path, str):
                            raise ToolError(
                                f"Output '{name}': all paths must be strings, "
                                f"got {type(path).__name__}"
                            )
                        full_path = self.project_root / path
                        if not full_path.exists():
                            raise ToolError(f"Output '{name}': file not found at '{path}'")
                else:
                    raise ToolError(
                        f"Output '{name}' is type 'file_path' and must be a "
                        f"string path or list of paths, got {type(value).__name__}"
                    )
            elif arg.type == "string":
                if not isinstance(value, str):
                    raise ToolError(
                        f"Output '{name}' is type 'string' and must be a string, "
                        f"got {type(value).__name__}"
                    )

    def _build_expected_outputs(
        self, step: WorkflowStep, job: JobDefinition
    ) -> list[ExpectedOutput]:
        """Build ExpectedOutput list from step's output refs."""
        results = []
        for output_name, output_ref in step.outputs.items():
            arg = job.get_argument(output_name)
            if not arg:
                continue

            if arg.type == "file_path":
                syntax = "filepath or list of filepaths"
            else:
                syntax = "string value"

            results.append(
                ExpectedOutput(
                    name=output_name,
                    type=arg.type,
                    description=arg.description,
                    required=output_ref.required,
                    syntax_for_finished_step_tool=syntax,
                )
            )
        return results

    def _build_step_inputs_info(
        self,
        step: WorkflowStep,
        job: JobDefinition,
        input_values: dict[str, ArgumentValue],
    ) -> list[StepInputInfo]:
        """Build StepInputInfo list with resolved values."""
        results = []
        for input_name, input_ref in step.inputs.items():
            arg = job.get_argument(input_name)
            if not arg:
                continue

            value = input_values.get(input_name)
            results.append(
                StepInputInfo(
                    name=input_name,
                    type=arg.type,
                    description=arg.description,
                    value=value,
                    required=input_ref.required,
                )
            )
        return results

    def _build_step_instructions(
        self,
        step: WorkflowStep,
        job: JobDefinition,
        workflow: Workflow,
        input_values: dict[str, ArgumentValue],
    ) -> str:
        """Build complete step instructions with inputs prepended."""
        parts: list[str] = []

        # Prepend input descriptions and values
        if step.inputs:
            parts.append("## Inputs\n")
            for input_name, input_ref in step.inputs.items():
                arg = job.get_argument(input_name)
                if not arg:
                    continue

                value = input_values.get(input_name)
                required_str = " (required)" if input_ref.required else " (optional)"

                if value is None:
                    parts.append(
                        f"- **{input_name}**{required_str}: {arg.description} — *not yet available*"
                    )
                elif arg.type == "file_path":
                    if isinstance(value, list):
                        paths_str = ", ".join(f"`{p}`" for p in value)
                        parts.append(f"- **{input_name}**{required_str}: {paths_str}")
                    else:
                        parts.append(f"- **{input_name}**{required_str}: `{value}`")
                else:
                    parts.append(f"- **{input_name}**{required_str}: {value}")
            parts.append("")

        # For sub_workflow steps, generate delegation instructions
        if step.sub_workflow:
            sw = step.sub_workflow
            job_ref = sw.workflow_job or job.name
            parts.append(
                f"This step delegates to a sub-workflow. Call `start_workflow` with "
                f'job_name="{job_ref}" and workflow_name="{sw.workflow_name}", '
                f"then follow the instructions it returns until the sub-workflow completes."
            )
        elif step.instructions:
            parts.append(step.instructions)

        return "\n".join(parts)

    def _build_active_step_info(
        self,
        session_id: str,
        step: WorkflowStep,
        job: JobDefinition,
        workflow: Workflow,
        input_values: dict[str, ArgumentValue],
    ) -> ActiveStepInfo:
        """Build an ActiveStepInfo from a step definition and its context."""
        instructions = self._build_step_instructions(step, job, workflow, input_values)
        step_outputs = self._build_expected_outputs(step, job)
        step_inputs = self._build_step_inputs_info(step, job, input_values)

        return ActiveStepInfo(
            session_id=session_id,
            step_id=step.name,
            project_root=str(self.project_root),
            job_dir=str(job.job_dir),
            step_expected_outputs=step_outputs,
            step_inputs=step_inputs,
            step_instructions=instructions,
            common_job_info=workflow.common_job_info or "",
        )

    # =========================================================================
    # Tool Implementations
    # =========================================================================

    def get_workflows(self) -> GetWorkflowsResponse:
        """List all available workflows."""
        from deepwork.jobs.issues import detect_issues

        jobs, _ = self._load_all_jobs()
        job_infos = [self._job_to_info(job) for job in jobs]

        issues = detect_issues(self.project_root)
        error_infos = [
            JobLoadErrorInfo(
                job_name=issue.job_name,
                job_dir=issue.job_dir,
                error=f"{issue.message}\n{issue.suggestion}",
            )
            for issue in issues
        ]

        # Write manifest for external consumers
        if self.status_writer:
            try:
                self.status_writer.write_manifest(jobs)
            except Exception:
                logger.warning("Failed to write job manifest", exc_info=True)

        return GetWorkflowsResponse(jobs=job_infos, errors=error_infos)

    async def start_workflow(self, input_data: StartWorkflowInput) -> StartWorkflowResponse:
        """Start a new workflow session."""
        # Load job and workflow (check session jobs first)
        job = self._get_job(input_data.job_name, session_id=input_data.session_id)
        workflow = self._get_workflow(job, input_data.workflow_name)

        if not workflow.steps:
            raise ToolError(f"Workflow '{workflow.name}' has no steps")

        first_step = workflow.steps[0]

        sid = self._resolve_session_id(input_data.session_id)
        aid = input_data.agent_id

        # Create session (use resolved workflow name in case it was auto-selected)
        session = await self.state_manager.create_session(
            session_id=sid,
            job_name=input_data.job_name,
            workflow_name=workflow.name,
            goal=input_data.goal,
            first_step_id=first_step.name,
            agent_id=aid,
        )

        # Resolve input values for first step
        input_values = self._resolve_input_values(
            first_step,
            job,
            workflow,
            sid,
            aid,
            provided_inputs=input_data.inputs,
        )

        # Mark first step as started with input values
        await self.state_manager.start_step(
            sid, first_step.name, input_values=input_values, agent_id=aid
        )

        response = StartWorkflowResponse(
            begin_step=self._build_active_step_info(
                session.session_id, first_step, job, workflow, input_values
            ),
            stack=self.state_manager.get_stack(sid, aid),
        )
        self._write_session_status(sid)
        return response

    async def finished_step(self, input_data: FinishedStepInput) -> FinishedStepResponse:
        """Report step completion and get next instructions."""
        sid = input_data.session_id
        aid = input_data.agent_id
        try:
            session = self.state_manager.resolve_session(sid, aid)
        except StateError as err:
            raise ToolError(
                "No active workflow session. "
                "Provide the session_id from the start_workflow response (begin_step.session_id). "
                "If you want to resume a workflow, just start it again and call finished_step "
                "with quality_review_override_reason until you get back to your prior step."
            ) from err
        current_step_name = session.current_step_id

        # Load job and workflow (check session jobs first)
        job = self._get_job(session.job_name, session_id=sid)
        workflow = self._get_workflow(job, session.workflow_name)
        current_step = workflow.get_step(current_step_name)

        if current_step is None:
            raise ToolError(f"Current step not found: {current_step_name}")

        # Validate outputs against step's declared output refs
        self._validate_outputs(input_data.outputs, current_step, job)

        # Get input values from state
        input_values = self.state_manager.get_step_input_values(sid, current_step_name, aid)

        # Run quality gate if not overridden
        if not input_data.quality_review_override_reason:
            review_feedback = run_quality_gate(
                step=current_step,
                job=job,
                workflow=workflow,
                outputs=input_data.outputs,
                input_values=input_values,
                work_summary=input_data.work_summary,
                project_root=self.project_root,
            )

            if review_feedback:
                # Record quality attempt
                await self.state_manager.record_quality_attempt(
                    sid, current_step_name, agent_id=aid
                )

                return FinishedStepResponse(
                    status=StepStatus.NEEDS_WORK,
                    feedback=review_feedback,
                    stack=self.state_manager.get_stack(sid, aid),
                )

        # Mark step as completed
        await self.state_manager.complete_step(
            session_id=sid,
            step_id=current_step_name,
            outputs=input_data.outputs,
            work_summary=input_data.work_summary,
            agent_id=aid,
        )

        # Find next step
        current_step_index = session.current_step_index
        next_step_index = current_step_index + 1

        if next_step_index >= len(workflow.steps):
            # Workflow complete - get outputs before completing (which removes from stack)
            all_outputs = self.state_manager.get_all_outputs(sid, aid)
            await self.state_manager.complete_workflow(sid, aid)

            response = FinishedStepResponse(
                status=StepStatus.WORKFLOW_COMPLETE,
                summary=f"Workflow '{workflow.name}' completed successfully!",
                all_outputs=all_outputs,
                post_workflow_instructions=workflow.post_workflow_instructions,
                stack=self.state_manager.get_stack(sid, aid),
            )
            self._write_session_status(sid)
            return response

        # Get next step
        next_step = workflow.steps[next_step_index]

        # Advance session
        await self.state_manager.advance_to_step(sid, next_step.name, next_step_index, agent_id=aid)

        # Resolve input values for next step
        next_input_values = self._resolve_input_values(next_step, job, workflow, sid, aid)

        # Mark next step as started with input values
        await self.state_manager.start_step(
            sid, next_step.name, input_values=next_input_values, agent_id=aid
        )

        response = FinishedStepResponse(
            status=StepStatus.NEXT_STEP,
            begin_step=self._build_active_step_info(
                sid, next_step, job, workflow, next_input_values
            ),
            stack=self.state_manager.get_stack(sid, aid),
        )
        self._write_session_status(sid)
        return response

    async def abort_workflow(self, input_data: AbortWorkflowInput) -> AbortWorkflowResponse:
        """Abort the current workflow and return to the previous one."""
        sid = input_data.session_id
        aid = input_data.agent_id
        aborted_session, new_active = await self.state_manager.abort_workflow(
            sid, input_data.explanation, agent_id=aid
        )

        response = AbortWorkflowResponse(
            aborted_workflow=f"{aborted_session.job_name}/{aborted_session.workflow_name}",
            aborted_step=aborted_session.current_step_id,
            explanation=input_data.explanation,
            stack=self.state_manager.get_stack(sid, aid),
            resumed_workflow=(
                f"{new_active.job_name}/{new_active.workflow_name}" if new_active else None
            ),
            resumed_step=new_active.current_step_id if new_active else None,
        )
        self._write_session_status(sid)
        return response

    async def go_to_step(self, input_data: GoToStepInput) -> GoToStepResponse:
        """Navigate back to a prior step, clearing progress from that step onward."""
        sid = input_data.session_id
        aid = input_data.agent_id
        session = self.state_manager.resolve_session(sid, aid)

        # Load job and workflow (check session jobs first)
        job = self._get_job(session.job_name, session_id=sid)
        workflow = self._get_workflow(job, session.workflow_name)

        # Validate target step exists in workflow
        target_index = workflow.get_step_index(input_data.step_id)
        if target_index is None:
            raise ToolError(
                f"Step '{input_data.step_id}' not found in workflow '{workflow.name}'. "
                f"Available steps: {', '.join(workflow.step_names)}"
            )

        # Validate not going forward (use finished_step for that)
        current_step_index = session.current_step_index
        if target_index > current_step_index:
            raise ToolError(
                f"Cannot go forward to step '{input_data.step_id}' "
                f"(index {target_index} > current {current_step_index}). "
                f"Use finished_step to advance forward."
            )

        # Validate step definition exists
        target_step = workflow.steps[target_index]

        # Collect all step names from target index through end of workflow
        invalidate_step_names: list[str] = [s.name for s in workflow.steps[target_index:]]

        # Clear progress and update position
        await self.state_manager.go_to_step(
            session_id=sid,
            step_id=target_step.name,
            step_index=target_index,
            invalidate_step_ids=invalidate_step_names,
            agent_id=aid,
        )

        # Resolve input values for target step
        input_values = self._resolve_input_values(target_step, job, workflow, sid, aid)

        # Mark target step as started
        await self.state_manager.start_step(
            sid, target_step.name, input_values=input_values, agent_id=aid
        )

        response = GoToStepResponse(
            begin_step=self._build_active_step_info(sid, target_step, job, workflow, input_values),
            invalidated_steps=invalidate_step_names,
            stack=self.state_manager.get_stack(sid, aid),
        )
        self._write_session_status(sid)
        return response

    # =========================================================================
    # Session Job Tools
    # =========================================================================

    def _session_jobs_dir(self, session_id: str) -> Path:
        """Get the directory for session-scoped jobs."""
        return self.state_manager.sessions_dir / f"session-{session_id}" / "jobs"

    async def register_session_job(self, input_data: RegisterSessionJobInput) -> dict[str, str]:
        """Register a transient job definition scoped to the current session.

        Writes the job YAML to a session-scoped directory and validates it
        against the job schema. Can be called multiple times to overwrite.
        """
        import re

        import yaml

        sid = input_data.session_id
        job_name = input_data.job_name

        # Validate job name format
        if not re.match(r"^[a-z][a-z0-9_]*$", job_name):
            raise ToolError(f"Invalid job name '{job_name}': must match ^[a-z][a-z0-9_]*$")

        # Write YAML to session jobs directory
        job_dir = self._session_jobs_dir(sid) / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        job_file = job_dir / "job.yml"

        # Validate YAML syntax first
        try:
            yaml.safe_load(input_data.job_definition_yaml)
        except yaml.YAMLError as e:
            raise ToolError(f"Invalid YAML syntax: {e}") from e

        # Write the file
        async with aiofiles.open(job_file, "w") as f:
            await f.write(input_data.job_definition_yaml)

        # Validate against job schema by parsing
        try:
            parse_job_definition(job_dir)
        except ParseError as e:
            # Keep the file so the agent can see what went wrong, but report errors
            raise ToolError(
                f"Job definition validation failed: {e}\n"
                f"The file was written to {job_file} for inspection. "
                f"Fix the issues and call register_session_job again."
            ) from e

        return {
            "status": "registered",
            "job_name": job_name,
            "job_dir": str(job_dir),
            "message": (
                f"Session job '{job_name}' registered successfully. "
                f"It can be started with start_workflow(job_name='{job_name}', ...)."
            ),
        }

    async def get_session_job(self, input_data: GetSessionJobInput) -> dict[str, str]:
        """Retrieve the YAML content of a session-scoped job definition."""
        sid = input_data.session_id
        job_file = self._session_jobs_dir(sid) / input_data.job_name / "job.yml"

        if not job_file.exists():
            raise ToolError(f"Session job '{input_data.job_name}' not found for session '{sid}'.")

        async with aiofiles.open(job_file) as f:
            content = await f.read()

        return {
            "job_name": input_data.job_name,
            "job_definition_yaml": content,
        }
