"""Integration tests for expert sync functionality."""

from pathlib import Path

import pytest

from deepwork.cli.sync import sync_skills
from deepwork.utils.yaml_utils import save_yaml


@pytest.fixture
def project_with_experts(tmp_path: Path) -> Path:
    """Create a minimal project with experts for sync testing."""
    # Create .deepwork directory structure
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()

    # Create config.yml
    config = {"version": "0.1.0", "platforms": ["claude"]}
    save_yaml(deepwork_dir / "config.yml", config)

    # Create jobs directory (empty - no jobs to sync)
    jobs_dir = deepwork_dir / "jobs"
    jobs_dir.mkdir()

    # Create experts directory with an expert
    experts_dir = deepwork_dir / "experts"
    experts_dir.mkdir()

    expert_dir = experts_dir / "test_expert"
    expert_dir.mkdir()

    # Create expert.yml
    (expert_dir / "expert.yml").write_text(
        """discovery_description: |
  Test expert for integration testing

full_expertise: |
  # Test Expert

  You are an expert on testing integrations.

  ## Key Concepts

  - Integration testing
  - End-to-end testing
"""
    )

    # Create topics
    topics_dir = expert_dir / "topics"
    topics_dir.mkdir()
    (topics_dir / "basics.md").write_text(
        """---
name: Testing Basics
keywords:
  - basics
  - fundamentals
last_updated: 2025-01-30
---

Content about testing basics.
"""
    )

    # Create learnings
    learnings_dir = expert_dir / "learnings"
    learnings_dir.mkdir()
    (learnings_dir / "discovery.md").write_text(
        """---
name: Important Discovery
last_updated: 2025-01-20
summarized_result: |
  Found that integration tests should be isolated.
---

Details of the discovery.
"""
    )

    # Create .claude directory
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    return tmp_path


class TestExpertSync:
    """Tests for expert sync functionality."""

    def test_sync_creates_expert_agent(self, project_with_experts: Path) -> None:
        """Test that sync creates expert agent files."""
        # Run sync
        sync_skills(project_with_experts)

        # Check that agent was created
        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        assert agent_file.exists(), f"Expected agent file at {agent_file}"

    def test_sync_agent_has_correct_name(self, project_with_experts: Path) -> None:
        """Test that generated agent has correct name field."""
        sync_skills(project_with_experts)

        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        content = agent_file.read_text()

        assert "name: test-expert" in content

    def test_sync_agent_has_description(self, project_with_experts: Path) -> None:
        """Test that generated agent has description from discovery_description."""
        sync_skills(project_with_experts)

        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        content = agent_file.read_text()

        assert "integration testing" in content.lower()

    def test_sync_agent_has_full_expertise(self, project_with_experts: Path) -> None:
        """Test that generated agent includes full_expertise content."""
        sync_skills(project_with_experts)

        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        content = agent_file.read_text()

        assert "expert on testing integrations" in content
        assert "Key Concepts" in content

    def test_sync_agent_has_dynamic_topics_command(self, project_with_experts: Path) -> None:
        """Test that generated agent includes dynamic topics command embedding."""
        sync_skills(project_with_experts)

        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        content = agent_file.read_text()

        assert '$(deepwork topics --expert "test-expert")' in content

    def test_sync_agent_has_dynamic_learnings_command(self, project_with_experts: Path) -> None:
        """Test that generated agent includes dynamic learnings command embedding."""
        sync_skills(project_with_experts)

        agent_file = project_with_experts / ".claude" / "agents" / "dwe_test-expert.md"
        content = agent_file.read_text()

        assert '$(deepwork learnings --expert "test-expert")' in content


class TestExpertSyncMultiple:
    """Tests for syncing multiple experts."""

    def test_sync_multiple_experts(self, tmp_path: Path) -> None:
        """Test syncing multiple experts creates multiple agent files."""
        # Create project structure
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        save_yaml(deepwork_dir / "config.yml", {"version": "0.1.0", "platforms": ["claude"]})
        (deepwork_dir / "jobs").mkdir()

        experts_dir = deepwork_dir / "experts"
        experts_dir.mkdir()

        # Create multiple experts
        for name in ["expert_a", "expert_b", "expert_c"]:
            expert_dir = experts_dir / name
            expert_dir.mkdir()
            (expert_dir / "expert.yml").write_text(
                f"discovery_description: Expert {name}\nfull_expertise: Content for {name}."
            )

        (tmp_path / ".claude").mkdir()

        # Run sync
        sync_skills(tmp_path)

        # Check all agents were created
        agents_dir = tmp_path / ".claude" / "agents"
        assert (agents_dir / "dwe_expert-a.md").exists()
        assert (agents_dir / "dwe_expert-b.md").exists()
        assert (agents_dir / "dwe_expert-c.md").exists()


class TestExpertSyncNoExperts:
    """Tests for syncing when no experts exist."""

    def test_sync_no_experts_directory(self, tmp_path: Path) -> None:
        """Test sync works when no experts directory exists."""
        # Create minimal project without experts
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        save_yaml(deepwork_dir / "config.yml", {"version": "0.1.0", "platforms": ["claude"]})
        (deepwork_dir / "jobs").mkdir()
        (tmp_path / ".claude").mkdir()

        # Should not raise
        sync_skills(tmp_path)

        # Agents directory may or may not exist, but should have no agent files
        agents_dir = tmp_path / ".claude" / "agents"
        if agents_dir.exists():
            agent_files = list(agents_dir.glob("dwe_*.md"))
            assert len(agent_files) == 0

    def test_sync_empty_experts_directory(self, tmp_path: Path) -> None:
        """Test sync works when experts directory is empty."""
        # Create project with empty experts directory
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        save_yaml(deepwork_dir / "config.yml", {"version": "0.1.0", "platforms": ["claude"]})
        (deepwork_dir / "jobs").mkdir()
        (deepwork_dir / "experts").mkdir()  # Empty experts dir
        (tmp_path / ".claude").mkdir()

        # Should not raise
        sync_skills(tmp_path)


class TestExpertSyncWithJobs:
    """Tests for syncing experts alongside jobs."""

    def test_sync_experts_and_jobs_together(self, tmp_path: Path) -> None:
        """Test that sync handles both experts and jobs."""
        # Create project structure
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        save_yaml(deepwork_dir / "config.yml", {"version": "0.1.0", "platforms": ["claude"]})

        # Create a job
        job_dir = deepwork_dir / "jobs" / "test_job"
        job_dir.mkdir(parents=True)
        (job_dir / "job.yml").write_text(
            """name: test_job
version: 1.0.0
summary: A test job
steps:
  - id: step_one
    name: Step One
    description: First step
    instructions_file: steps/step_one.md
    outputs:
      - output.md
"""
        )
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_one.md").write_text("Do the first step.")

        # Create an expert
        expert_dir = deepwork_dir / "experts" / "test_expert"
        expert_dir.mkdir(parents=True)
        (expert_dir / "expert.yml").write_text(
            "discovery_description: Test expert\nfull_expertise: Expert content."
        )

        (tmp_path / ".claude").mkdir()

        # Run sync
        sync_skills(tmp_path)

        # Check both job skills and expert agents were created
        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists()
        # Job should have created skills
        assert any(skills_dir.iterdir())

        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.exists()
        assert (agents_dir / "dwe_test-expert.md").exists()
