"""Expert agent and workflow skill generator using Jinja2 templates."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.adapters import AgentAdapter, SkillLifecycleHook
from deepwork.core.doc_spec_parser import (
    DocSpec,
    DocSpecParseError,
    parse_doc_spec_file,
)
from deepwork.core.experts_parser import (
    ExpertDefinition,
    WorkflowDefinition,
    WorkflowStep,
)
from deepwork.schemas.workflow_schema import LIFECYCLE_HOOK_EVENTS
from deepwork.utils.fs import safe_read, safe_write


class ExpertGeneratorError(Exception):
    """Exception raised for expert agent generation errors."""


class WorkflowGeneratorError(Exception):
    """Exception raised for workflow skill generation errors."""


class ExpertGenerator:
    """Generates agent files and workflow skills from expert definitions."""

    # Template filenames
    EXPERT_AGENT_TEMPLATE = "agent-expert.md.jinja"

    def __init__(self, templates_dir: Path | str | None = None):
        """
        Initialize generator.

        Args:
            templates_dir: Path to templates directory
                          (defaults to package templates directory)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = Path(templates_dir)

        if not self.templates_dir.exists():
            raise ExpertGeneratorError(f"Templates directory not found: {self.templates_dir}")

        # Cache for loaded doc specs
        self._doc_spec_cache: dict[Path, DocSpec] = {}

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
            raise ExpertGeneratorError(
                f"Templates for platform '{adapter.name}' not found at {platform_templates_dir}"
            )

        return Environment(
            loader=FileSystemLoader(platform_templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _load_doc_spec(self, project_root: Path, doc_spec_path: str) -> DocSpec | None:
        """
        Load a doc spec by file path with caching.

        Args:
            project_root: Path to project root
            doc_spec_path: Relative path to doc spec file

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

    # =========================================================================
    # Expert agent generation
    # =========================================================================

    def _build_expert_context(self, expert: ExpertDefinition) -> dict[str, Any]:
        """
        Build template context for an expert.

        Args:
            expert: Expert definition

        Returns:
            Template context dictionary
        """
        # Build workflow info for the expert
        workflows_info = []
        for workflow in expert.workflows:
            workflow_info = {
                "name": workflow.name,
                "summary": workflow.summary,
                "step_count": len(workflow.steps),
                "first_step": workflow.steps[0].id if workflow.steps else None,
            }
            workflows_info.append(workflow_info)

        return {
            "expert_name": expert.name,
            "discovery_description": expert.discovery_description,
            "full_expertise": expert.full_expertise,
            "workflows": workflows_info,
            "has_workflows": bool(expert.workflows),
        }

    def get_agent_filename(self, expert_name: str) -> str:
        """
        Get the filename for an expert agent.

        Args:
            expert_name: Name of the expert (e.g., "rails-activejob")

        Returns:
            Agent filename (e.g., "dwe_rails-activejob.md")
        """
        return f"dwe_{expert_name}.md"

    def get_agent_name(self, expert_name: str) -> str:
        """
        Get the agent name field value for an expert.

        Args:
            expert_name: Name of the expert (e.g., "rails-activejob")

        Returns:
            Agent name (e.g., "rails-activejob")
        """
        return expert_name

    def generate_expert_agent(
        self,
        expert: ExpertDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate an agent file from an expert definition.

        Args:
            expert: Expert definition
            adapter: Agent adapter for the target platform
            output_dir: Platform config directory (e.g., .claude/)

        Returns:
            Path to generated agent file

        Raises:
            ExpertGeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create agents subdirectory
        agents_dir = output_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Build context
        context = self._build_expert_context(expert)

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(self.EXPERT_AGENT_TEMPLATE)
        except TemplateNotFound as e:
            raise ExpertGeneratorError(
                f"Expert agent template not found: {self.EXPERT_AGENT_TEMPLATE}"
            ) from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise ExpertGeneratorError(
                f"Expert agent template rendering failed for '{expert.name}': {e}"
            ) from e

        # Write agent file
        agent_filename = self.get_agent_filename(expert.name)
        agent_path = agents_dir / agent_filename

        try:
            safe_write(agent_path, rendered)
        except Exception as e:
            raise ExpertGeneratorError(f"Failed to write agent file: {e}") from e

        return agent_path

    def generate_all_expert_agents(
        self,
        experts: list[ExpertDefinition],
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> list[Path]:
        """
        Generate agent files for all experts.

        Args:
            experts: List of expert definitions
            adapter: Agent adapter for the target platform
            output_dir: Platform config directory (e.g., .claude/)

        Returns:
            List of paths to generated agent files

        Raises:
            ExpertGeneratorError: If generation fails for any expert
        """
        agent_paths: list[Path] = []

        for expert in experts:
            agent_path = self.generate_expert_agent(expert, adapter, output_dir)
            agent_paths.append(agent_path)

        return agent_paths

    # =========================================================================
    # Workflow skill generation
    # =========================================================================

    def _build_hook_context(self, workflow: WorkflowDefinition, hook_action: Any) -> dict[str, Any]:
        """
        Build context for a single hook action.

        Args:
            workflow: Workflow definition
            hook_action: WorkflowHookAction instance

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
            prompt_file_path = workflow.workflow_dir / hook_action.prompt_file
            prompt_content = safe_read(prompt_file_path)
            if prompt_content is None:
                raise WorkflowGeneratorError(f"Hook prompt file not found: {prompt_file_path}")
            hook_ctx["content"] = prompt_content
        elif hook_action.is_script():
            hook_ctx["type"] = "script"
            hook_ctx["path"] = hook_action.script
        return hook_ctx

    def _build_step_context(
        self,
        expert: ExpertDefinition,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        adapter: AgentAdapter,
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        """
        Build template context for a workflow step.

        Args:
            expert: Expert definition (parent)
            workflow: Workflow definition
            step: Step to generate context for
            adapter: Agent adapter for platform-specific hook name mapping
            project_root: Optional project root for loading doc specs

        Returns:
            Template context dictionary
        """
        # Read step instructions
        instructions_file = workflow.workflow_dir / step.instructions_file
        instructions_content = safe_read(instructions_file)
        if instructions_content is None:
            raise WorkflowGeneratorError(f"Step instructions file not found: {instructions_file}")

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

        # Get step position in workflow
        position = workflow.get_step_position(step.id)
        next_step = workflow.get_next_step(step.id)
        prev_step = workflow.get_prev_step(step.id)

        # Build hooks context for all lifecycle events
        hooks: dict[str, list[dict[str, Any]]] = {}
        for event in LIFECYCLE_HOOK_EVENTS:
            if event in step.hooks:
                hook_enum = SkillLifecycleHook(event)
                platform_event_name = adapter.get_platform_hook_name(hook_enum)
                if platform_event_name:
                    hook_contexts = [
                        self._build_hook_context(workflow, hook_action)
                        for hook_action in step.hooks[event]
                    ]
                    if hook_contexts:
                        hooks[platform_event_name] = hook_contexts

        # Claude Code: duplicate Stop hooks to SubagentStop
        if "Stop" in hooks:
            hooks["SubagentStop"] = hooks["Stop"]

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

        return {
            # Expert context
            "expert_name": expert.name,
            # Workflow context
            "workflow_name": workflow.name,
            "workflow_version": workflow.version,
            "workflow_summary": workflow.summary,
            "workflow_description": workflow.description,
            "workflow_step_number": position[0] if position else 1,
            "workflow_total_steps": position[1] if position else 1,
            # Step context
            "step_id": step.id,
            "step_name": step.name,
            "step_description": step.description,
            "instructions_file": step.instructions_file,
            "instructions_content": instructions_content,
            "user_inputs": user_inputs,
            "file_inputs": file_inputs,
            "outputs": outputs_context,
            "dependencies": step.dependencies,
            "next_step": next_step,
            "prev_step": prev_step,
            "exposed": step.exposed,
            "hooks": hooks,
            "quality_criteria": step.quality_criteria,
            # Use the expert's name as the agent - each expert becomes its own agent
            "agent": expert.name,
        }

    def _build_workflow_meta_context(
        self,
        expert: ExpertDefinition,
        workflow: WorkflowDefinition,
        adapter: AgentAdapter,
    ) -> dict[str, Any]:
        """
        Build template context for a workflow's meta-skill.

        Args:
            expert: Expert definition (parent)
            workflow: Workflow definition
            adapter: Agent adapter for platform-specific configuration

        Returns:
            Template context dictionary
        """
        # Build step info for the meta-skill
        steps_info = []
        for step in workflow.steps:
            # Skill command is expert-name.step-id
            skill_command = f"{expert.name}.{step.id}"

            step_info = {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "command_name": skill_command,
                "dependencies": step.dependencies,
                "exposed": step.exposed,
            }
            steps_info.append(step_info)

        # Build execution order info with concurrent step support
        execution_entries_info = []
        if workflow.execution_order:
            for entry in workflow.execution_order:
                entry_info: dict[str, Any] = {
                    "is_concurrent": entry.is_concurrent,
                    "step_ids": entry.step_ids,
                }
                if entry.is_concurrent:
                    concurrent_steps = []
                    for i, step_id in enumerate(entry.step_ids):
                        step = workflow.get_step(step_id)
                        concurrent_steps.append(
                            {
                                "id": step_id,
                                "name": step.name if step else step_id,
                                "description": step.description if step else "",
                                "task_number": i + 1,
                            }
                        )
                    entry_info["concurrent_steps"] = concurrent_steps
                execution_entries_info.append(entry_info)
        else:
            # Default: each step is sequential
            for step in workflow.steps:
                execution_entries_info.append(
                    {
                        "is_concurrent": False,
                        "step_ids": [step.id],
                    }
                )

        first_step = workflow.steps[0].id if workflow.steps else None

        return {
            "expert_name": expert.name,
            "workflow_name": workflow.name,
            "workflow_version": workflow.version,
            "workflow_summary": workflow.summary,
            "workflow_description": workflow.description,
            "total_steps": len(workflow.steps),
            "steps": steps_info,
            "execution_entries": execution_entries_info,
            "first_step": first_step,
        }

    def get_workflow_meta_skill_filename(self, expert_name: str, workflow_name: str) -> str:
        """
        Get filename for a workflow meta-skill.

        Args:
            expert_name: Expert name (e.g., "deepwork-jobs")
            workflow_name: Workflow name (e.g., "new_job")

        Returns:
            Skill filename (e.g., "deepwork-jobs.new_job/SKILL.md" for Claude)
        """
        # Use expert-name.workflow-name format
        return f"{expert_name}.{workflow_name}/SKILL.md"

    def get_step_skill_filename(self, expert_name: str, step_id: str, exposed: bool = False) -> str:
        """
        Get filename for a step skill.

        Args:
            expert_name: Expert name (e.g., "deepwork-jobs")
            step_id: Step ID (e.g., "define")
            exposed: Whether step is user-invocable

        Returns:
            Skill filename (e.g., "deepwork-jobs.define/SKILL.md" for Claude)
        """
        # 2-part naming: expert-name.step-id
        return f"{expert_name}.{step_id}/SKILL.md"

    def generate_workflow_meta_skill(
        self,
        expert: ExpertDefinition,
        workflow: WorkflowDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate the meta-skill file for a workflow.

        Args:
            expert: Expert definition (parent)
            workflow: Workflow definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill file to

        Returns:
            Path to generated meta-skill file

        Raises:
            WorkflowGeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create skills subdirectory
        skills_dir = output_dir / adapter.skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Build context
        context = self._build_workflow_meta_context(expert, workflow, adapter)

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(adapter.meta_skill_template)
        except TemplateNotFound as e:
            raise WorkflowGeneratorError(
                f"Workflow meta-skill template not found: {adapter.meta_skill_template}"
            ) from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise WorkflowGeneratorError(
                f"Workflow meta-skill template rendering failed: {e}"
            ) from e

        # Write meta-skill file
        skill_filename = self.get_workflow_meta_skill_filename(expert.name, workflow.name)
        skill_path = skills_dir / skill_filename

        # Ensure parent directories exist
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            safe_write(skill_path, rendered)
        except Exception as e:
            raise WorkflowGeneratorError(f"Failed to write meta-skill file: {e}") from e

        return skill_path

    def generate_workflow_step_skill(
        self,
        expert: ExpertDefinition,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        adapter: AgentAdapter,
        output_dir: Path | str,
        project_root: Path | str | None = None,
    ) -> Path:
        """
        Generate skill file for a single workflow step.

        Args:
            expert: Expert definition (parent)
            workflow: Workflow definition
            step: Step to generate skill for
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill file to
            project_root: Optional project root for loading doc specs

        Returns:
            Path to generated skill file

        Raises:
            WorkflowGeneratorError: If generation fails
        """
        output_dir = Path(output_dir)
        project_root_path = Path(project_root) if project_root else output_dir

        # Create skills subdirectory
        skills_dir = output_dir / adapter.skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Build context
        context = self._build_step_context(expert, workflow, step, adapter, project_root_path)

        # Load and render template
        env = self._get_jinja_env(adapter)
        try:
            template = env.get_template(adapter.skill_template)
        except TemplateNotFound as e:
            raise WorkflowGeneratorError(
                f"Workflow step template not found: {adapter.skill_template}"
            ) from e

        try:
            rendered = template.render(**context)
        except Exception as e:
            raise WorkflowGeneratorError(f"Workflow step template rendering failed: {e}") from e

        # Write skill file
        skill_filename = self.get_step_skill_filename(expert.name, step.id, step.exposed)
        skill_path = skills_dir / skill_filename

        # Ensure parent directories exist
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            safe_write(skill_path, rendered)
        except Exception as e:
            raise WorkflowGeneratorError(f"Failed to write skill file: {e}") from e

        return skill_path

    def generate_all_workflow_skills(
        self,
        expert: ExpertDefinition,
        workflow: WorkflowDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
        project_root: Path | str | None = None,
    ) -> list[Path]:
        """
        Generate all skill files for a workflow: meta-skill and step skills.

        Args:
            expert: Expert definition (parent)
            workflow: Workflow definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill files to
            project_root: Optional project root for loading doc specs

        Returns:
            List of paths to generated skill files (meta-skill first, then steps)

        Raises:
            WorkflowGeneratorError: If generation fails
        """
        skill_paths: list[Path] = []
        project_root_path = Path(project_root) if project_root else Path(output_dir)

        # Generate meta-skill first
        meta_skill_path = self.generate_workflow_meta_skill(expert, workflow, adapter, output_dir)
        skill_paths.append(meta_skill_path)

        # Generate step skills
        for step in workflow.steps:
            skill_path = self.generate_workflow_step_skill(
                expert, workflow, step, adapter, output_dir, project_root_path
            )
            skill_paths.append(skill_path)

        return skill_paths

    def generate_all_expert_skills(
        self,
        expert: ExpertDefinition,
        adapter: AgentAdapter,
        output_dir: Path | str,
        project_root: Path | str | None = None,
    ) -> list[Path]:
        """
        Generate all skill files for all workflows in an expert.

        Args:
            expert: Expert definition
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill files to
            project_root: Optional project root for loading doc specs

        Returns:
            List of paths to all generated skill files

        Raises:
            WorkflowGeneratorError: If generation fails
        """
        all_skill_paths: list[Path] = []

        for workflow in expert.workflows:
            workflow_paths = self.generate_all_workflow_skills(
                expert, workflow, adapter, output_dir, project_root
            )
            all_skill_paths.extend(workflow_paths)

        return all_skill_paths
