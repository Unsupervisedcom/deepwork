"""Slash-command file generator using Jinja2 templates."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.adapters import AgentAdapter, CommandLifecycleHook
from deepwork.core.parser import JobDefinition, Step, Workflow
from deepwork.schemas.job_schema import LIFECYCLE_HOOK_EVENTS
from deepwork.utils.fs import safe_read, safe_write


class GeneratorError(Exception):
    """Exception raised for command generation errors."""

    pass


class CommandGenerator:
    """Generates slash-command files from job definitions."""

    def __init__(self, templates_dir: Path | str | None = None):
        """
        Initialize generator.

        Args:
            templates_dir: Path to templates directory
                          (defaults to package templates directory)
        """
        if templates_dir is None:
            # Use package templates directory
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = Path(templates_dir)

        if not self.templates_dir.exists():
            raise GeneratorError(f"Templates directory not found: {self.templates_dir}")

    def _get_jinja_env(self, adapter: AgentAdapter) -> Environment:
        """
        Get Jinja2 environment for an adapter.

        Args:
            adapter: Agent adapter

        Returns:
            Jinja2 Environment
        """
        platform_templates_dir = adapter.get_template_dir(self.templates_dir)
        if not platform_templates_dir.exists():
            raise GeneratorError(
                f"Templates for platform '{adapter.name}' not found at {platform_templates_dir}"
            )

        return Environment(
            loader=FileSystemLoader(platform_templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _is_standalone_step(self, job: JobDefinition, step: Step) -> bool:
        """
        Check if a step is standalone (not part of a named workflow).

        A step is standalone if it's in an anonymous workflow (a workflow with no name).
        Anonymous workflows are meant for single, independent steps.

        Args:
            job: Job definition
            step: Step to check

        Returns:
            True if step is standalone (in an anonymous workflow)
        """
        workflow = job.get_workflow_for_step(step.id)
        if workflow is None:
            return True
        return workflow.is_anonymous()

    def _build_hook_context(self, job: JobDefinition, hook_action: Any) -> dict[str, Any]:
        """
        Build context for a single hook action.

        Args:
            job: Job definition
            hook_action: HookAction instance

        Returns:
            Hook context dictionary
        """
        hook_ctx: dict[str, Any] = {}
        if hook_action.is_prompt():
            hook_ctx["type"] = "prompt"
            hook_ctx["content"] = hook_action.prompt
        elif hook_action.is_prompt_file():
            hook_ctx["type"] = "prompt_file"
            hook_ctx["path"] = hook_action.prompt_file
            # Read the prompt file content
            prompt_file_path = job.job_dir / hook_action.prompt_file
            prompt_content = safe_read(prompt_file_path)
            if prompt_content is None:
                raise GeneratorError(f"Hook prompt file not found: {prompt_file_path}")
            hook_ctx["content"] = prompt_content
        elif hook_action.is_script():
            hook_ctx["type"] = "script"
            hook_ctx["path"] = hook_action.script
        return hook_ctx

    def _build_step_context(
        self, job: JobDefinition, step: Step, step_index: int, adapter: AgentAdapter
    ) -> dict[str, Any]:
        """
        Build template context for a step.

        Args:
            job: Job definition
            step: Step to generate context for
            step_index: Index of step in job (0-based, across all workflows)
            adapter: Agent adapter for platform-specific hook name mapping

        Returns:
            Template context dictionary
        """
        # Read step instructions
        instructions_file = job.job_dir / step.instructions_file
        instructions_content = safe_read(instructions_file)
        if instructions_content is None:
            raise GeneratorError(f"Step instructions file not found: {instructions_file}")

        # Separate user inputs and file inputs
        user_inputs = [
            {"name": inp.name, "description": inp.description}
            for inp in step.inputs
            if inp.is_user_input()
        ]
        file_inputs = [
            {"file": inp.file, "from_step": inp.from_step}
            for inp in step.inputs
            if inp.is_file_input()
        ]

        # Check if this is a standalone step
        is_standalone = self._is_standalone_step(job, step)

        # Get the workflow containing this step
        workflow = job.get_workflow_for_step(step.id)

        # Determine next and previous steps within the workflow (only for non-standalone steps)
        next_step = None
        prev_step = None
        workflow_step_number = 1
        workflow_total_steps = 1
        if not is_standalone and workflow is not None:
            workflow_steps = workflow.steps
            workflow_total_steps = len(workflow_steps)
            try:
                workflow_step_index = next(
                    i for i, s in enumerate(workflow_steps) if s.id == step.id
                )
                workflow_step_number = workflow_step_index + 1
                if workflow_step_index < len(workflow_steps) - 1:
                    next_step = workflow_steps[workflow_step_index + 1].id
                if workflow_step_index > 0:
                    prev_step = workflow_steps[workflow_step_index - 1].id
            except StopIteration:
                pass

        # Build hooks context for all lifecycle events
        # Structure: {platform_event_name: [hook_contexts]}
        hooks: dict[str, list[dict[str, Any]]] = {}
        for event in LIFECYCLE_HOOK_EVENTS:
            if event in step.hooks:
                # Get platform-specific event name from adapter
                hook_enum = CommandLifecycleHook(event)
                platform_event_name = adapter.get_platform_hook_name(hook_enum)
                if platform_event_name:
                    hook_contexts = [
                        self._build_hook_context(job, hook_action)
                        for hook_action in step.hooks[event]
                    ]
                    if hook_contexts:
                        hooks[platform_event_name] = hook_contexts

        # Backward compatibility: stop_hooks is after_agent hooks
        stop_hooks = hooks.get(
            adapter.get_platform_hook_name(CommandLifecycleHook.AFTER_AGENT) or "Stop", []
        )

        return {
            "job_name": job.name,
            "job_version": job.version,
            "job_summary": job.summary,
            "job_description": job.description,
            "step_id": step.id,
            "step_name": step.name,
            "step_description": step.description,
            "step_number": workflow_step_number,  # 1-based position within workflow
            "total_steps": workflow_total_steps,  # Total steps in this workflow
            "workflow_name": workflow.name if workflow else None,
            "workflow_description": workflow.description if workflow else None,
            "instructions_file": step.instructions_file,
            "instructions_content": instructions_content,
            "user_inputs": user_inputs,
            "file_inputs": file_inputs,
            "outputs": step.outputs,
            "dependencies": step.dependencies,
            "next_step": next_step,
            "prev_step": prev_step,
            "is_standalone": is_standalone,
            "hooks": hooks,  # New: all hooks by platform event name
            "stop_hooks": stop_hooks,  # Backward compat: after_agent hooks only
        }

    def generate_step_command(
        self,
        job: JobDefinition,
        step: Step,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate slash-command file for a single step.

        Args:
            job: Job definition
            step: Step to generate command for
            adapter: Agent adapter for the target platform
            output_dir: Directory to write command file to

        Returns:
            Path to generated command file

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create commands subdirectory if needed
        commands_dir = output_dir / adapter.commands_dir
        commands_dir.mkdir(parents=True, exist_ok=True)

        # Find step index
        try:
            step_index = next(i for i, s in enumerate(job.steps) if s.id == step.id)
        except StopIteration as e:
            raise GeneratorError(f"Step '{step.id}' not found in job '{job.name}'") from e

        # Build context
        context = self._build_step_context(job, step, step_index, adapter)

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(adapter.command_template)
        except TemplateNotFound as e:
            raise GeneratorError(f"Template not found: {e}") from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise GeneratorError(f"Template rendering failed: {e}") from e

        # Write command file
        command_filename = adapter.get_command_filename(job.name, step.id)
        command_path = commands_dir / command_filename

        try:
            safe_write(command_path, rendered)
        except Exception as e:
            raise GeneratorError(f"Failed to write command file: {e}") from e

        return command_path

    def generate_all_commands(
        self,
        job: JobDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> list[Path]:
        """
        Generate slash-command files for all steps in a job.

        Args:
            job: Job definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write command files to

        Returns:
            List of paths to generated command files

        Raises:
            GeneratorError: If generation fails
        """
        command_paths = []

        for step in job.steps:
            command_path = self.generate_step_command(job, step, adapter, output_dir)
            command_paths.append(command_path)

        return command_paths
