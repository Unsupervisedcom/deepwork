"""Agent file generator for subagent definitions."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from deepwork.core.adapters import AgentAdapter
from deepwork.utils.fs import safe_write


class AgentGeneratorError(Exception):
    """Exception raised for agent generation errors."""

    pass


class AgentGenerator:
    """Generates agent definition files for platforms that support them."""

    def __init__(self, templates_dir: Path | str | None = None):
        """
        Initialize agent generator.

        Args:
            templates_dir: Path to templates directory
                          (defaults to package templates directory)
        """
        if templates_dir is None:
            # Use package templates directory
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = Path(templates_dir)

        if not self.templates_dir.exists():
            raise AgentGeneratorError(f"Templates directory not found: {self.templates_dir}")

    def _get_agent_templates(self, adapter: AgentAdapter) -> list[Path]:
        """
        Get list of agent template files for an adapter.

        Args:
            adapter: Agent adapter

        Returns:
            List of agent template file paths (empty if none exist)
        """
        platform_templates_dir = adapter.get_template_dir(self.templates_dir)
        agents_dir = platform_templates_dir / "agents"

        if not agents_dir.exists():
            return []

        # Find all .j2 template files in the agents directory
        agent_templates = list(agents_dir.glob("*.j2"))
        return agent_templates

    def generate_agents(
        self,
        adapter: AgentAdapter,
        project_path: Path | str,
    ) -> list[Path]:
        """
        Generate agent definition files for a platform.

        This creates agent files (e.g., .claude/agents/*.md) from templates
        in the templates directory. Only platforms that support agents will
        have agent templates.

        Args:
            adapter: Agent adapter for the target platform
            project_path: Path to project root

        Returns:
            List of paths to generated agent files

        Raises:
            AgentGeneratorError: If generation fails
        """
        project_path = Path(project_path)

        # Get agent templates for this platform
        agent_templates = self._get_agent_templates(adapter)

        if not agent_templates:
            # No agent templates for this platform - that's okay
            return []

        # Create agents directory in platform config
        platform_dir = project_path / adapter.config_dir
        agents_dir = platform_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Setup Jinja environment
        platform_templates_dir = adapter.get_template_dir(self.templates_dir)
        agents_templates_dir = platform_templates_dir / "agents"

        env = Environment(
            loader=FileSystemLoader(agents_templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        generated_paths: list[Path] = []

        # Process each agent template
        for template_path in agent_templates:
            template_name = template_path.name

            # Remove .j2 extension for output file
            output_filename = template_name[:-3] if template_name.endswith(".j2") else template_name

            try:
                # Load and render template
                template = env.get_template(template_name)
                rendered = template.render()

                # Write agent file
                agent_path = agents_dir / output_filename

                safe_write(agent_path, rendered)
                generated_paths.append(agent_path)

            except Exception as e:
                raise AgentGeneratorError(
                    f"Failed to generate agent {template_name}: {e}"
                ) from e

        return generated_paths
