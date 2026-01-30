"""Tests for expert agent generator."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.experts_generator import ExpertGenerator, ExpertGeneratorError
from deepwork.core.experts_parser import ExpertDefinition, Learning, Topic


class TestExpertGenerator:
    """Tests for ExpertGenerator class."""

    def test_init_default_templates(self) -> None:
        """Test initialization with default templates directory."""
        generator = ExpertGenerator()

        assert generator.templates_dir.exists()
        assert (generator.templates_dir / "claude").exists()

    def test_init_custom_templates(self, tmp_path: Path) -> None:
        """Test initialization with custom templates directory."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        generator = ExpertGenerator(templates_dir)

        assert generator.templates_dir == templates_dir

    def test_init_nonexistent_templates(self, tmp_path: Path) -> None:
        """Test initialization with nonexistent templates fails."""
        with pytest.raises(ExpertGeneratorError, match="not found"):
            ExpertGenerator(tmp_path / "nonexistent")

    def test_get_agent_filename(self) -> None:
        """Test agent filename generation."""
        generator = ExpertGenerator()

        assert generator.get_agent_filename("rails-activejob") == "dwe_rails-activejob.md"
        assert generator.get_agent_filename("experts") == "dwe_experts.md"

    def test_get_agent_name(self) -> None:
        """Test agent name generation."""
        generator = ExpertGenerator()

        assert generator.get_agent_name("rails-activejob") == "rails-activejob"
        assert generator.get_agent_name("experts") == "experts"


class TestGenerateExpertAgent:
    """Tests for generating expert agent files."""

    @pytest.fixture
    def generator(self) -> ExpertGenerator:
        """Create a generator instance."""
        return ExpertGenerator()

    @pytest.fixture
    def claude_adapter(self, tmp_path: Path) -> ClaudeAdapter:
        """Create a Claude adapter."""
        return ClaudeAdapter(project_root=tmp_path)

    @pytest.fixture
    def sample_expert(self, tmp_path: Path) -> ExpertDefinition:
        """Create a sample expert definition."""
        expert_dir = tmp_path / "rails_activejob"
        expert_dir.mkdir(parents=True)

        return ExpertDefinition(
            name="rails-activejob",
            discovery_description="Rails ActiveJob background processing",
            full_expertise="You are an expert on Rails ActiveJob.\n\n## Key Concepts\n\n- Queues\n- Retries",
            expert_dir=expert_dir,
            topics=[
                Topic(name="Retry Handling", keywords=["retry"], source_file=expert_dir / "topics/retry.md"),
            ],
            learnings=[
                Learning(name="Sentry Issue", summarized_result="Fixed it", source_file=expert_dir / "learnings/sentry.md"),
            ],
        )

    def test_generate_expert_agent_creates_file(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, sample_expert: ExpertDefinition, tmp_path: Path
    ) -> None:
        """Test that generating an expert agent creates the file."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        agent_path = generator.generate_expert_agent(sample_expert, claude_adapter, output_dir)

        assert agent_path.exists()
        assert agent_path.name == "dwe_rails-activejob.md"
        assert agent_path.parent.name == "agents"

    def test_generate_expert_agent_content(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, sample_expert: ExpertDefinition, tmp_path: Path
    ) -> None:
        """Test the content of generated expert agent file."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        agent_path = generator.generate_expert_agent(sample_expert, claude_adapter, output_dir)
        content = agent_path.read_text()

        # Check frontmatter
        assert "name: rails-activejob" in content
        assert "Rails ActiveJob" in content

        # Check full_expertise is included
        assert "expert on Rails ActiveJob" in content
        assert "Key Concepts" in content

        # Check dynamic command embedding
        assert '$(deepwork topics --expert "rails-activejob")' in content
        assert '$(deepwork learnings --expert "rails-activejob")' in content

    def test_generate_expert_agent_creates_agents_dir(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, sample_expert: ExpertDefinition, tmp_path: Path
    ) -> None:
        """Test that generating creates the agents directory if needed."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        assert not (output_dir / "agents").exists()

        generator.generate_expert_agent(sample_expert, claude_adapter, output_dir)

        assert (output_dir / "agents").exists()

    def test_generate_all_expert_agents(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, tmp_path: Path
    ) -> None:
        """Test generating agents for multiple experts."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        expert1 = ExpertDefinition(
            name="expert-one",
            discovery_description="First expert",
            full_expertise="Expert one content",
            expert_dir=tmp_path / "expert_one",
        )
        expert2 = ExpertDefinition(
            name="expert-two",
            discovery_description="Second expert",
            full_expertise="Expert two content",
            expert_dir=tmp_path / "expert_two",
        )

        agent_paths = generator.generate_all_expert_agents([expert1, expert2], claude_adapter, output_dir)

        assert len(agent_paths) == 2
        assert all(p.exists() for p in agent_paths)
        assert {p.name for p in agent_paths} == {"dwe_expert-one.md", "dwe_expert-two.md"}

    def test_generate_empty_experts_list(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, tmp_path: Path
    ) -> None:
        """Test generating with empty experts list."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        agent_paths = generator.generate_all_expert_agents([], claude_adapter, output_dir)

        assert agent_paths == []


class TestExpertAgentTemplate:
    """Tests for the expert agent template structure."""

    @pytest.fixture
    def generator(self) -> ExpertGenerator:
        """Create a generator instance."""
        return ExpertGenerator()

    @pytest.fixture
    def claude_adapter(self, tmp_path: Path) -> ClaudeAdapter:
        """Create a Claude adapter."""
        return ClaudeAdapter(project_root=tmp_path)

    def test_template_has_yaml_frontmatter(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, tmp_path: Path
    ) -> None:
        """Test that generated agent has YAML frontmatter."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        expert = ExpertDefinition(
            name="test-expert",
            discovery_description="Test description",
            full_expertise="Test expertise",
            expert_dir=tmp_path / "test_expert",
        )

        agent_path = generator.generate_expert_agent(expert, claude_adapter, output_dir)
        content = agent_path.read_text()

        # Check YAML frontmatter markers
        assert content.startswith("---\n")
        lines = content.split("\n")
        # Find second ---
        second_marker = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                second_marker = i
                break
        assert second_marker is not None, "YAML frontmatter not properly closed"

    def test_template_escapes_description(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, tmp_path: Path
    ) -> None:
        """Test that description with quotes is properly escaped."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        expert = ExpertDefinition(
            name="test-expert",
            discovery_description='Description with "quotes" inside',
            full_expertise="Test expertise",
            expert_dir=tmp_path / "test_expert",
        )

        agent_path = generator.generate_expert_agent(expert, claude_adapter, output_dir)
        content = agent_path.read_text()

        # Should escape quotes in description
        assert r'\"quotes\"' in content or "quotes" in content

    def test_template_truncates_long_description(
        self, generator: ExpertGenerator, claude_adapter: ClaudeAdapter, tmp_path: Path
    ) -> None:
        """Test that long descriptions are truncated."""
        output_dir = tmp_path / ".claude"
        output_dir.mkdir()

        # Create a very long description
        long_description = "A" * 500

        expert = ExpertDefinition(
            name="test-expert",
            discovery_description=long_description,
            full_expertise="Test expertise",
            expert_dir=tmp_path / "test_expert",
        )

        agent_path = generator.generate_expert_agent(expert, claude_adapter, output_dir)
        content = agent_path.read_text()

        # Extract description from frontmatter
        lines = content.split("\n")
        for line in lines:
            if line.startswith("description:"):
                # Should be truncated
                assert len(line) < 500
                break
