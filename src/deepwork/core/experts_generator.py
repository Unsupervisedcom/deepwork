"""Expert agent generator using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.adapters import AgentAdapter
from deepwork.core.experts_parser import ExpertDefinition
from deepwork.utils.fs import safe_write


class ExpertGeneratorError(Exception):
    """Exception raised for expert agent generation errors."""


class ExpertGenerator:
    """Generates agent files from expert definitions."""

    # Template filename for expert agents
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

    def _build_expert_context(self, expert: ExpertDefinition) -> dict:
        """
        Build template context for an expert.

        Args:
            expert: Expert definition

        Returns:
            Template context dictionary
        """
        return {
            "expert_name": expert.name,
            "discovery_description": expert.discovery_description,
            "full_expertise": expert.full_expertise,
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
