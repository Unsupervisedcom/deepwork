"""Skill file generator using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from deepwork.core.adapters import AgentAdapter
from deepwork.utils.fs import safe_write


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

    def generate_deepwork_skill(
        self,
        adapter: AgentAdapter,
        output_dir: Path | str,
    ) -> Path:
        """
        Generate the global /deepwork skill that instructs agents to use MCP tools.

        This is a single skill that provides the main entry point for DeepWork,
        directing agents to use the MCP server's tools for workflow management.

        Args:
            adapter: Agent adapter for the target platform
            output_dir: Directory to write skill file to

        Returns:
            Path to generated skill file

        Raises:
            GeneratorError: If generation fails
        """
        output_dir = Path(output_dir)

        # Create skills subdirectory if needed
        skills_dir = output_dir / adapter.skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Load and render template
        env = self._get_jinja_env(adapter)
        template_name = "skill-deepwork.md.jinja"

        try:
            template = env.get_template(template_name)
        except TemplateNotFound as e:
            raise GeneratorError(f"DeepWork skill template not found: {e}") from e

        try:
            rendered = template.render()
        except Exception as e:
            raise GeneratorError(f"DeepWork skill template rendering failed: {e}") from e

        # Write skill file
        # Use the adapter's convention for naming
        if adapter.name == "gemini":
            skill_filename = "deepwork/index.toml"
        else:
            skill_filename = "deepwork/SKILL.md"

        skill_path = skills_dir / skill_filename
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            safe_write(skill_path, rendered)
        except Exception as e:
            raise GeneratorError(f"Failed to write DeepWork skill file: {e}") from e

        return skill_path
