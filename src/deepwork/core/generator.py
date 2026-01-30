"""Skill file generator using Jinja2 templates."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.adapters import AgentAdapter, SkillLifecycleHook
from deepwork.core.doc_spec_parser import (
    DocSpec,
    DocSpecParseError,
    parse_doc_spec_file,
)
from deepwork.core.parser import JobDefinition, Step
from deepwork.schemas.job_schema import LIFECYCLE_HOOK_EVENTS
from deepwork.utils.fs import safe_read, safe_write


class GeneratorError(Exception):
    """Exception raised for skill generation errors."""

    pass


class SkillGenerator:
    """Generates skill files from job definitions."""

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

        # Cache for loaded doc specs (keyed by absolute file path)
        self._doc_spec_cache: dict[Path, DocSpec] = {}

    def _load_doc_spec(self, project_root: Path, doc_spec_path: str) -> DocSpec | None:
        """
        Load a doc spec by file path with caching.

        Args:
            project_root: Path to project root
            doc_spec_path: Relative path to doc spec file (e.g., ".deepwork/doc_specs/report.md")

        Returns:
            DocSpec if file exists and parses, None otherwise
        """
        full_path = project_root / doc_spec_path
        if full_path in self._doc_spec_cache:
            return self._doc_spec_cache[full_path]

        if not full_path.exists():
            return None

        try:
            doc_spec = parse_doc_spec_file(full_path)
        except DocSpecParseError:
            return None

        self._doc_spec_cache[full_path] = doc_spec
        return doc_spec

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
        Check if a step is standalone (not part of any workflow).

        A step is standalone if:
        - It's not listed in any workflow definition
        - OR (for backward compatibility) no workflows are defined and the step
          has no dependencies and no other steps depend on it

        Args:
            job: Job definition
            step: Step to check

        Returns:
            True if step is standalone
        """
        # If workflows are defined, use workflow membership
        if job.workflows:
            return job.get_workflow_for_step(step.id) is None
        else:
            # Backward compatibility: if no workflows defined, use dependency analysis
            # Step has dependencies - not standalone
            if step.dependencies:
                return False

            # Check if any other step depends on this step
            for other_step in job.steps:
                if step.id in other_step.dependencies:
                    return False

        return True

    def _get_workflow_context(self, job: JobDefinition, step: Step) -> dict[str, Any]:
        """
        Build workflow context for a step.

        Args:
            job: Job definition
            step: Step to build context for

        Returns:
            Workflow context dictionary with workflow info, or empty dict if standalone
        """
        workflow = job.get_workflow_for_step(step.id)
        if not workflow:
            return {}

        position = job.get_step_position_in_workflow(step.id)
        return {
            "workflow_name": workflow.name,
            "workflow_summary": workflow.summary,
            "workflow_step_number": position[0] if position else 1,
            "workflow_total_steps": position[1] if position else 1,
            "workflow_next_step": job.get_next_step_in_workflow(step.id),
            "workflow_prev_step": job.get_prev_step_in_workflow(step.id),
        }

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
        self,
        job: JobDefinition,
        step: Step,
        step_index: int,
        adapter: AgentAdapter,
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        """
        Build template context for a step.

        Args:
            job: Job definition
            step: Step to generate context for
            step_index: Index of step in job (0-based)
            adapter: Agent adapter for platform-specific hook name mapping
            project_root: Optional project root for loading doc specs

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

        # Get workflow context (empty dict if standalone)
        workflow_ctx = self._get_workflow_context(job, step)

        # Determine next and previous steps based on workflow (if defined) or order
        next_step = None
        prev_step = None
        if not is_standalone:
            if workflow_ctx:
                # Use workflow-defined order
                next_step = workflow_ctx.get("workflow_next_step")
                prev_step = workflow_ctx.get("workflow_prev_step")
            else:
                # Backward compatibility: use step array order
                if step_index < len(job.steps) - 1:
                    next_step = job.steps[step_index + 1].id
                if step_index > 0:
                    prev_step = job.steps[step_index - 1].id

        # Build hooks context for all lifecycle events
        # Structure: {platform_event_name: [hook_contexts]}
        hooks: dict[str, list[dict[str, Any]]] = {}
        for event in LIFECYCLE_HOOK_EVENTS:
            if event in step.hooks:
                # Get platform-specific event name from adapter
                hook_enum = SkillLifecycleHook(event)
                platform_event_name = adapter.get_platform_hook_name(hook_enum)
                if platform_event_name:
                    hook_contexts = [
                        self._build_hook_context(job, hook_action)
                        for hook_action in step.hooks[event]
                    ]
                    if hook_contexts:
                        hooks[platform_event_name] = hook_contexts

        # Claude Code has separate Stop and SubagentStop events. When a Stop hook
        # is defined, also register it for SubagentStop so it triggers for both
        # the main agent and subagents.
        if "Stop" in hooks:
            hooks["SubagentStop"] = hooks["Stop"]

        # Backward compatibility: stop_hooks is after_agent hooks
        stop_hooks = hooks.get(
            adapter.get_platform_hook_name(SkillLifecycleHook.AFTER_AGENT) or "Stop", []
        )

        # Build rich outputs context with doc spec information
        outputs_context = []
        for output in step.outputs:
            output_ctx: dict[str, Any] = {
                "file": output.file,
                "has_doc_spec": output.has_doc_spec(),
            }
            if output.has_doc_spec() and output.doc_spec and project_root:
                doc_spec = self._load_doc_spec(project_root, output.doc_spec)
                if doc_spec:
                    output_ctx["doc_spec"] = {
                        "path": output.doc_spec,
                        "name": doc_spec.name,
                        "description": doc_spec.description,
                        "target_audience": doc_spec.target_audience,
                        "quality_criteria": [
                            {"name": c.name, "description": c.description}
                            for c in doc_spec.quality_criteria
                        ],
                        "example_document": doc_spec.example_document,
                    }
            outputs_context.append(output_ctx)

        context = {
            "job_name": job.name,
            "job_version": job.version,
            "job_summary": job.summary,
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
            "outputs": outputs_context,
            "dependencies": step.dependencies,
            "next_step": next_step,
            "prev_step": prev_step,
            "is_standalone": is_standalone,
            "hooks": hooks,  # New: all hooks by platform event name
            "stop_hooks": stop_hooks,  # Backward compat: after_agent hooks only
            "quality_criteria": step.quality_criteria,  # Declarative criteria with framing
            "agent": step.agent,  # Agent type (e.g., "general-purpose") - triggers context: fork
        }

        # Add workflow context if step is part of a workflow
        context.update(workflow_ctx)

        return context

    def _build_meta_skill_context(
        self, job: JobDefinition, adapter: AgentAdapter
    ) -> dict[str, Any]:
        """
        Build template context for a job's meta-skill.

        Args:
            job: Job definition
            adapter: Agent adapter for platform-specific configuration

        Returns:
            Template context dictionary
        """
        # Build step info for the meta-skill
        steps_info = []
        for step in job.steps:
            skill_filename = adapter.get_step_skill_filename(job.name, step.id, step.exposed)
            # Extract just the skill name (without path and extension)
            # For Claude: job_name.step_id/SKILL.md -> job_name.step_id
            # For Gemini: job_name/step_id.toml -> job_name:step_id
            if adapter.name == "gemini":
                # Gemini uses colon for namespacing: job_name:step_id
                parts = skill_filename.replace(".toml", "").split("/")
                skill_name = ":".join(parts)
            else:
                # Claude uses directory/SKILL.md format, extract directory name
                # job_name.step_id/SKILL.md -> job_name.step_id
                skill_name = skill_filename.replace("/SKILL.md", "")

            # Get workflow info for step
            workflow = job.get_workflow_for_step(step.id)
            step_info = {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "command_name": skill_name,
                "dependencies": step.dependencies,
                "exposed": step.exposed,
                "is_standalone": self._is_standalone_step(job, step),
            }
            if workflow:
                step_info["workflow_name"] = workflow.name

            steps_info.append(step_info)

        # Build workflow info
        workflows_info = []
        for workflow in job.workflows:
            workflows_info.append(
                {
                    "name": workflow.name,
                    "summary": workflow.summary,
                    "steps": workflow.steps,
                    "first_step": workflow.steps[0] if workflow.steps else None,
                }
            )

        # Identify standalone steps (not in any workflow)
        standalone_steps = [s for s in steps_info if s["is_standalone"]]

        return {
            "job_name": job.name,
            "job_version": job.version,
            "job_summary": job.summary,
            "job_description": job.description,
            "total_steps": len(job.steps),
            "steps": steps_info,
            "workflows": workflows_info,
            "standalone_steps": standalone_steps,
            "has_workflows": bool(job.workflows),
        }

    def generate_meta_skill(
        self,
        job: JobDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate the meta-skill file for a job.

        The meta-skill is the primary user interface for a job, routing
        user intent to the appropriate step.

        Args:
            job: Job definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill file to

        Returns:
            Path to generated meta-skill file

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create skills subdirectory if needed
        skills_dir = output_dir / adapter.skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Build context
        context = self._build_meta_skill_context(job, adapter)

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(adapter.meta_skill_template)
        except TemplateNotFound as e:
            raise GeneratorError(f"Meta-skill template not found: {e}") from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise GeneratorError(f"Meta-skill template rendering failed: {e}") from e

        # Write meta-skill file
        skill_filename = adapter.get_meta_skill_filename(job.name)
        skill_path = skills_dir / skill_filename

        # Ensure parent directories exist (for Gemini's job_name/index.toml structure)
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            safe_write(skill_path, rendered)
        except Exception as e:
            raise GeneratorError(f"Failed to write meta-skill file: {e}") from e

        return skill_path

    def generate_step_skill(
        self,
        job: JobDefinition,
        step: Step,
        adapter: AgentAdapter,
        output_dir: Path | str,
        project_root: Path | str | None = None,
    ) -> Path:
        """
        Generate skill file for a single step.

        Args:
            job: Job definition
            step: Step to generate skill for
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill file to
            project_root: Optional project root for loading doc specs (defaults to output_dir)

        Returns:
            Path to generated skill file

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)
        project_root_path = Path(project_root) if project_root else output_dir

        # Create skills subdirectory if needed
        skills_dir = output_dir / adapter.skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Find step index
        try:
            step_index = next(i for i, s in enumerate(job.steps) if s.id == step.id)
        except StopIteration as e:
            raise GeneratorError(f"Step '{step.id}' not found in job '{job.name}'") from e

        # Build context (include exposed for template user-invocable setting)
        context = self._build_step_context(job, step, step_index, adapter, project_root_path)
        context["exposed"] = step.exposed

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(adapter.skill_template)
        except TemplateNotFound as e:
            raise GeneratorError(f"Template not found: {e}") from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise GeneratorError(f"Template rendering failed: {e}") from e

        # Write skill file
        skill_filename = adapter.get_step_skill_filename(job.name, step.id, step.exposed)
        skill_path = skills_dir / skill_filename

        # Ensure parent directories exist (for Gemini's job_name/step_id.toml structure)
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            safe_write(skill_path, rendered)
        except Exception as e:
            raise GeneratorError(f"Failed to write skill file: {e}") from e

        return skill_path

    def generate_all_skills(
        self,
        job: JobDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
        project_root: Path | str | None = None,
    ) -> list[Path]:
        """
        Generate all skill files for a job: meta-skill and step skills.

        Args:
            job: Job definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill files to
            project_root: Optional project root for loading doc specs (defaults to output_dir)

        Returns:
            List of paths to generated skill files (meta-skill first, then steps)

        Raises:
            GeneratorError: If generation fails
        """
        skill_paths = []
        project_root_path = Path(project_root) if project_root else Path(output_dir)

        # Generate meta-skill first (job-level entry point)
        meta_skill_path = self.generate_meta_skill(job, adapter, output_dir)
        skill_paths.append(meta_skill_path)

        # Generate step skills
        for step in job.steps:
            skill_path = self.generate_step_skill(job, step, adapter, output_dir, project_root_path)
            skill_paths.append(skill_path)

        return skill_paths
