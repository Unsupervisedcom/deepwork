"""Slash-command file generator using Jinja2 templates."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.detector import PlatformConfig
from deepwork.core.parser import JobDefinition, Step
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

    def _get_jinja_env(self, platform: PlatformConfig) -> Environment:
        """
        Get Jinja2 environment for a platform.

        Args:
            platform: Platform configuration

        Returns:
            Jinja2 Environment
        """
        platform_templates_dir = self.templates_dir / platform.name
        if not platform_templates_dir.exists():
            raise GeneratorError(
                f"Templates for platform '{platform.name}' not found at {platform_templates_dir}"
            )

        return Environment(
            loader=FileSystemLoader(platform_templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _build_step_context(
        self, job: JobDefinition, step: Step, step_index: int
    ) -> dict[str, Any]:
        """
        Build template context for a step.

        Args:
            job: Job definition
            step: Step to generate context for
            step_index: Index of step in job (0-based)

        Returns:
            Template context dictionary
        """
        # Read step instructions
        instructions_file = job.job_dir / step.instructions_file
        instructions_content = safe_read(instructions_file)
        if instructions_content is None:
            raise GeneratorError(
                f"Step instructions file not found: {instructions_file}"
            )

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

        # Determine next and previous steps
        next_step = None
        prev_step = None
        if step_index < len(job.steps) - 1:
            next_step = job.steps[step_index + 1].id
        if step_index > 0:
            prev_step = job.steps[step_index - 1].id

        return {
            "job_name": job.name,
            "job_version": job.version,
            "job_description": job.description,
            "step_id": step.id,
            "step_name": step.name,
            "step_description": step.description,
            "step_number": step_index + 1,  # 1-based for display
            "total_steps": len(job.steps),
            "instructions_file": step.instructions_file,
            "instructions_content": instructions_content,
            "user_inputs": user_inputs,
            "file_inputs": file_inputs,
            "outputs": step.outputs,
            "dependencies": step.dependencies,
            "next_step": next_step,
            "prev_step": prev_step,
        }

    def generate_step_command(
        self,
        job: JobDefinition,
        step: Step,
        platform: PlatformConfig,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate slash-command file for a single step.

        Args:
            job: Job definition
            step: Step to generate command for
            platform: Platform configuration
            output_dir: Directory to write command file to

        Returns:
            Path to generated command file

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create commands subdirectory if needed
        commands_dir = output_dir / platform.commands_dir
        commands_dir.mkdir(parents=True, exist_ok=True)

        # Find step index
        try:
            step_index = next(
                i for i, s in enumerate(job.steps) if s.id == step.id
            )
        except StopIteration as e:
            raise GeneratorError(f"Step '{step.id}' not found in job '{job.name}'") from e

        # Build context
        context = self._build_step_context(job, step, step_index)

        # Load and render template
        env = self._get_jinja_env(platform)
        try:
            template = env.get_template("command-job-step.md.jinja")
        except TemplateNotFound as e:
            raise GeneratorError(f"Template not found: {e}") from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise GeneratorError(f"Template rendering failed: {e}") from e

        # Write command file
        command_filename = f"{job.name}.{step.id}.md"
        command_path = commands_dir / command_filename

        try:
            safe_write(command_path, rendered)
        except Exception as e:
            raise GeneratorError(f"Failed to write command file: {e}") from e

        return command_path

    def generate_all_commands(
        self,
        job: JobDefinition,
        platform: PlatformConfig,
        output_dir: Path | str,
    ) -> list[Path]:
        """
        Generate slash-command files for all steps in a job.

        Args:
            job: Job definition
            platform: Platform configuration
            output_dir: Directory to write command files to

        Returns:
            List of paths to generated command files

        Raises:
            GeneratorError: If generation fails
        """
        command_paths = []

        for step in job.steps:
            command_path = self.generate_step_command(job, step, platform, output_dir)
            command_paths.append(command_path)

        return command_paths

    def generate_core_commands(
        self, platform: PlatformConfig, output_dir: Path | str
    ) -> list[Path]:
        """
        Generate core DeepWork commands (like define).

        Args:
            platform: Platform configuration
            output_dir: Base directory to write commands to (e.g., .claude/)

        Returns:
            List of paths to generated command files

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)
        commands_dir = output_dir / platform.commands_dir
        commands_dir.mkdir(parents=True, exist_ok=True)

        command_paths = []

        # Core templates to generate
        core_templates = [
            ("command-define.md.jinja", "deepwork.define_job.md"),
            ("command-refine.md.jinja", "deepwork.refine_job.md"),
        ]

        env = self._get_jinja_env(platform)

        for template_name, command_filename in core_templates:
            try:
                template = env.get_template(template_name)
            except TemplateNotFound:
                # Skip if template doesn't exist yet
                continue

            try:
                rendered = template.render()
            except Exception as e:
                raise GeneratorError(
                    f"Core template rendering failed for {template_name}: {e}"
                ) from e

            command_path = commands_dir / command_filename

            try:
                safe_write(command_path, rendered)
            except Exception as e:
                raise GeneratorError(f"Failed to write core command file: {e}") from e

            command_paths.append(command_path)

        return command_paths

