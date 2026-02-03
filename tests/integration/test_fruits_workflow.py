"""Integration tests for the fruits CI test workflow.

This module tests the fruits job - a simple, deterministic workflow
designed for automated CI testing of the DeepWork framework.
"""

from pathlib import Path

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.parser import parse_job_definition


class TestFruitsWorkflow:
    """Integration tests for the fruits CI test workflow."""

    def test_fruits_job_parses_correctly(self, fixtures_dir: Path) -> None:
        """Test that the fruits job definition parses correctly."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        assert job.name == "fruits"
        assert job.version == "1.0.0"
        assert len(job.steps) == 2

        # Verify step IDs
        step_ids = [step.id for step in job.steps]
        assert step_ids == ["identify", "classify"]

    def test_fruits_identify_step_structure(self, fixtures_dir: Path) -> None:
        """Test the identify step has correct structure."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        identify_step = job.steps[0]
        assert identify_step.id == "identify"
        assert identify_step.name == "Identify Fruits"

        # Has user input
        assert len(identify_step.inputs) == 1
        assert identify_step.inputs[0].is_user_input()
        assert identify_step.inputs[0].name == "raw_items"

        # Has output
        assert len(identify_step.outputs) == 1
        assert identify_step.outputs[0].file == "identified_fruits.md"

        # No dependencies (first step)
        assert identify_step.dependencies == []

    def test_fruits_classify_step_structure(self, fixtures_dir: Path) -> None:
        """Test the classify step has correct structure."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        classify_step = job.steps[1]
        assert classify_step.id == "classify"
        assert classify_step.name == "Classify Fruits"

        # Has file input from previous step
        assert len(classify_step.inputs) == 1
        assert classify_step.inputs[0].is_file_input()
        assert classify_step.inputs[0].file == "identified_fruits.md"
        assert classify_step.inputs[0].from_step == "identify"

        # Has output
        assert len(classify_step.outputs) == 1
        assert classify_step.outputs[0].file == "classified_fruits.md"

        # Depends on identify step
        assert classify_step.dependencies == ["identify"]

    def test_fruits_skill_generation(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test that fruits job generates valid Claude skills."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # Now includes meta-skill + step skills
        assert len(skill_paths) == 3  # 1 meta + 2 steps

        # Verify skill directories with SKILL.md files exist
        meta_skill = skills_dir / "skills" / "fruits" / "SKILL.md"
        identify_skill = skills_dir / "skills" / "fruits.identify" / "SKILL.md"
        classify_skill = skills_dir / "skills" / "fruits.classify" / "SKILL.md"
        assert meta_skill.exists()
        assert identify_skill.exists()
        assert classify_skill.exists()

    def test_fruits_identify_skill_content(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test the identify skill has correct content."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        generator.generate_all_skills(job, adapter, skills_dir)

        # Step skills use directory/SKILL.md format
        identify_skill = skills_dir / "skills" / "fruits.identify" / "SKILL.md"
        content = identify_skill.read_text()

        # Check header
        assert "# fruits.identify" in content

        # Check step info
        assert "Step 1/2" in content

        # Check user input is mentioned
        assert "raw_items" in content

        # Check output is mentioned
        assert "identified_fruits.md" in content

        # Check next step is suggested
        assert "/fruits.classify" in content

    def test_fruits_classify_skill_content(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test the classify skill has correct content."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        generator.generate_all_skills(job, adapter, skills_dir)

        # Step skills use directory/SKILL.md format
        classify_skill = skills_dir / "skills" / "fruits.classify" / "SKILL.md"
        content = classify_skill.read_text()

        # Check header
        assert "# fruits.classify" in content

        # Check step info
        assert "Step 2/2" in content

        # Check file input is mentioned
        assert "identified_fruits.md" in content
        assert "from `identify`" in content

        # Check output is mentioned
        assert "classified_fruits.md" in content

        # Check workflow complete (last step)
        assert "workflow complete" in content.lower()

    def test_fruits_dependency_validation(self, fixtures_dir: Path) -> None:
        """Test that dependency validation passes for fruits job."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        # This should not raise - dependencies are valid
        job.validate_dependencies()

    def test_fruits_job_is_deterministic_design(self, fixtures_dir: Path) -> None:
        """Verify the fruits job is designed for deterministic testing.

        This test documents the design properties that make this job
        suitable for CI testing.
        """
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        # Job has clear, simple structure
        assert len(job.steps) == 2

        # Steps form a linear dependency chain
        assert job.steps[0].dependencies == []
        assert job.steps[1].dependencies == ["identify"]

        # First step takes user input
        identify_step = job.steps[0]
        assert len(identify_step.inputs) == 1
        assert identify_step.inputs[0].is_user_input()

        # Second step uses output from first step
        classify_step = job.steps[1]
        assert len(classify_step.inputs) == 1
        assert classify_step.inputs[0].is_file_input()
        assert classify_step.inputs[0].from_step == "identify"

        # Outputs are well-defined markdown files
        assert len(identify_step.outputs) == 1
        assert identify_step.outputs[0].file == "identified_fruits.md"
        assert len(classify_step.outputs) == 1
        assert classify_step.outputs[0].file == "classified_fruits.md"
