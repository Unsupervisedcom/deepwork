"""Tests for expert CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.experts import learnings, topics


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def project_with_expert(tmp_path: Path) -> Path:
    """Create a project with an expert."""
    # Create .deepwork/experts directory
    experts_dir = tmp_path / ".deepwork" / "experts"
    experts_dir.mkdir(parents=True)

    # Create an expert
    expert_dir = experts_dir / "test_expert"
    expert_dir.mkdir()

    # Create expert.yml
    (expert_dir / "expert.yml").write_text(
        """discovery_description: |
  Test expert for CLI testing

full_expertise: |
  You are an expert on testing CLI commands.
"""
    )

    # Create topics directory with topics
    topics_dir = expert_dir / "topics"
    topics_dir.mkdir()

    (topics_dir / "basics.md").write_text(
        """---
name: Testing Basics
keywords:
  - testing
  - basics
last_updated: 2025-01-30
---

Content about testing basics.
"""
    )

    (topics_dir / "advanced.md").write_text(
        """---
name: Advanced Testing
keywords:
  - advanced
  - mocking
last_updated: 2025-01-15
---

Content about advanced testing.
"""
    )

    # Create learnings directory with learnings
    learnings_dir = expert_dir / "learnings"
    learnings_dir.mkdir()

    (learnings_dir / "discovery.md").write_text(
        """---
name: Important Discovery
last_updated: 2025-01-20
summarized_result: |
  Found that X causes Y under Z conditions.
---

Full details of the discovery.
"""
    )

    return tmp_path


class TestTopicsCommand:
    """Tests for the topics command."""

    def test_topics_command_help(self, runner: CliRunner) -> None:
        """Test topics command shows help."""
        result = runner.invoke(topics, ["--help"])

        assert result.exit_code == 0
        assert "List topics for an expert" in result.output
        assert "--expert" in result.output

    def test_topics_command_requires_expert(self, runner: CliRunner) -> None:
        """Test topics command requires --expert option."""
        result = runner.invoke(topics, [])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_topics_command_lists_topics(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test topics command lists topics for an expert."""
        result = runner.invoke(
            topics, ["--expert", "test-expert", "--path", str(project_with_expert)]
        )

        assert result.exit_code == 0
        assert "Testing Basics" in result.output
        assert "Advanced Testing" in result.output
        assert "testing" in result.output  # keyword
        assert "advanced" in result.output  # keyword

    def test_topics_command_markdown_format(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test topics command outputs markdown format."""
        result = runner.invoke(
            topics, ["--expert", "test-expert", "--path", str(project_with_expert)]
        )

        assert result.exit_code == 0
        # Should contain markdown links
        assert "[Testing Basics]" in result.output
        assert "(topics/" in result.output

    def test_topics_command_sorted_by_date(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test topics are sorted by most recently updated."""
        result = runner.invoke(
            topics, ["--expert", "test-expert", "--path", str(project_with_expert)]
        )

        assert result.exit_code == 0
        # Testing Basics (2025-01-30) should come before Advanced Testing (2025-01-15)
        basics_pos = result.output.find("Testing Basics")
        advanced_pos = result.output.find("Advanced Testing")
        assert basics_pos < advanced_pos

    def test_topics_command_expert_not_found(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test topics command with nonexistent expert."""
        result = runner.invoke(
            topics, ["--expert", "nonexistent", "--path", str(project_with_expert)]
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_topics_command_no_experts_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test topics command when no experts directory exists."""
        result = runner.invoke(topics, ["--expert", "test", "--path", str(tmp_path)])

        assert result.exit_code != 0
        assert "No experts directory" in result.output or "not found" in result.output.lower()

    def test_topics_command_no_topics(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test topics command when expert has no topics."""
        # Create expert without topics
        experts_dir = tmp_path / ".deepwork" / "experts" / "empty_expert"
        experts_dir.mkdir(parents=True)
        (experts_dir / "expert.yml").write_text(
            "discovery_description: Empty expert\nfull_expertise: Nothing here."
        )

        result = runner.invoke(
            topics, ["--expert", "empty-expert", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "No topics yet" in result.output


class TestLearningsCommand:
    """Tests for the learnings command."""

    def test_learnings_command_help(self, runner: CliRunner) -> None:
        """Test learnings command shows help."""
        result = runner.invoke(learnings, ["--help"])

        assert result.exit_code == 0
        assert "List learnings for an expert" in result.output
        assert "--expert" in result.output

    def test_learnings_command_requires_expert(self, runner: CliRunner) -> None:
        """Test learnings command requires --expert option."""
        result = runner.invoke(learnings, [])

        assert result.exit_code != 0

    def test_learnings_command_lists_learnings(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test learnings command lists learnings for an expert."""
        result = runner.invoke(
            learnings, ["--expert", "test-expert", "--path", str(project_with_expert)]
        )

        assert result.exit_code == 0
        assert "Important Discovery" in result.output
        assert "X causes Y" in result.output

    def test_learnings_command_markdown_format(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test learnings command outputs markdown format."""
        result = runner.invoke(
            learnings, ["--expert", "test-expert", "--path", str(project_with_expert)]
        )

        assert result.exit_code == 0
        # Should contain markdown links
        assert "[Important Discovery]" in result.output
        assert "(learnings/" in result.output

    def test_learnings_command_expert_not_found(
        self, runner: CliRunner, project_with_expert: Path
    ) -> None:
        """Test learnings command with nonexistent expert."""
        result = runner.invoke(
            learnings, ["--expert", "nonexistent", "--path", str(project_with_expert)]
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_learnings_command_no_learnings(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test learnings command when expert has no learnings."""
        # Create expert without learnings
        experts_dir = tmp_path / ".deepwork" / "experts" / "empty_expert"
        experts_dir.mkdir(parents=True)
        (experts_dir / "expert.yml").write_text(
            "discovery_description: Empty expert\nfull_expertise: Nothing here."
        )

        result = runner.invoke(
            learnings, ["--expert", "empty-expert", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "No learnings yet" in result.output


class TestExpertNameResolution:
    """Tests for expert name resolution (dashes vs underscores)."""

    def test_expert_with_underscores_resolved(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that expert-name resolves to expert_name folder."""
        # Create expert with underscore folder name
        experts_dir = tmp_path / ".deepwork" / "experts" / "rails_activejob"
        experts_dir.mkdir(parents=True)
        (experts_dir / "expert.yml").write_text(
            "discovery_description: Rails ActiveJob\nfull_expertise: Content."
        )

        # Topics directory
        topics_dir = experts_dir / "topics"
        topics_dir.mkdir()
        (topics_dir / "test.md").write_text("---\nname: Test\n---\nContent")

        # Query with dashes
        result = runner.invoke(
            topics, ["--expert", "rails-activejob", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Test" in result.output

    def test_available_experts_shown_on_error(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that available experts are listed when expert not found."""
        # Create some experts
        experts_dir = tmp_path / ".deepwork" / "experts"
        experts_dir.mkdir(parents=True)

        for name in ["expert_a", "expert_b"]:
            ed = experts_dir / name
            ed.mkdir()
            (ed / "expert.yml").write_text(
                f"discovery_description: {name}\nfull_expertise: Content."
            )

        # Query nonexistent expert
        result = runner.invoke(
            topics, ["--expert", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code != 0
        assert "expert-a" in result.output.lower() or "expert_a" in result.output.lower()
        assert "expert-b" in result.output.lower() or "expert_b" in result.output.lower()
