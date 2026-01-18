"""Tests for skill generator."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import SkillGenerator, GeneratorError
from deepwork.core.parser import parse_job_definition


class TestSkillGenerator:
    """Tests for SkillGenerator class."""

    def test_init_default_templates_dir(self) -> None:
        """Test initialization with default templates directory."""
        generator = SkillGenerator()

        assert generator.templates_dir.exists()
        assert (generator.templates_dir / "claude").exists()

    def test_init_custom_templates_dir(self, temp_dir: Path) -> None:
        """Test initialization with custom templates directory."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        generator = SkillGenerator(templates_dir)

        assert generator.templates_dir == templates_dir

    def test_init_raises_for_missing_templates_dir(self, temp_dir: Path) -> None:
        """Test initialization raises error for missing templates directory."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(GeneratorError, match="Templates directory not found"):
            SkillGenerator(nonexistent)

    def test_generate_step_skill_simple_job(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skill for simple job step."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skill_path = generator.generate_step_skill(job, job.steps[0], adapter, temp_dir)

        assert skill_path.exists()
        # Step skills have clean names (no prefix)
        assert skill_path.name == "simple_job.single_step.md"

        content = skill_path.read_text()
        assert "# simple_job.single_step" in content
        # Single step with no dependencies is treated as standalone
        assert "Standalone skill" in content
        assert "input_param" in content
        assert "output.md" in content

    def test_generate_step_skill_complex_job_first_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for first step of complex job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skill_path = generator.generate_step_skill(job, job.steps[0], adapter, temp_dir)

        content = skill_path.read_text()
        assert "# competitive_research.identify_competitors" in content
        assert "Step 1 of 4" in content
        assert "market_segment" in content
        assert "product_category" in content
        # First step has no prerequisites
        assert "## Prerequisites" not in content
        # Has next step
        assert "/competitive_research.primary_research" in content

    def test_generate_step_skill_complex_job_middle_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for middle step with dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Generate primary_research (step 2)
        skill_path = generator.generate_step_skill(job, job.steps[1], adapter, temp_dir)

        content = skill_path.read_text()
        assert "# competitive_research.primary_research" in content
        assert "Step 2 of 4" in content
        # Has prerequisites
        assert "## Prerequisites" in content
        assert "/competitive_research.identify_competitors" in content
        # Has file input
        assert "competitors.md" in content
        assert "from step `identify_competitors`" in content
        # Has next step
        assert "/competitive_research.secondary_research" in content

    def test_generate_step_skill_complex_job_final_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for final step."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Generate comparative_report (step 4)
        skill_path = generator.generate_step_skill(job, job.steps[3], adapter, temp_dir)

        content = skill_path.read_text()
        assert "# competitive_research.comparative_report" in content
        assert "Step 4 of 4" in content
        # Has prerequisites
        assert "## Prerequisites" in content
        # Has multiple file inputs
        assert "primary_research.md" in content
        assert "secondary_research.md" in content
        # Final step - no next step
        assert "## Workflow Complete" in content
        assert "## Next Step" not in content

    def test_generate_step_skill_raises_for_missing_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that generating skill for non-existent step raises error."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Create a fake step not in the job
        from deepwork.core.parser import Step

        fake_step = Step(
            id="fake",
            name="Fake",
            description="Fake",
            instructions_file="steps/fake.md",
            outputs=["fake.md"],
        )

        with pytest.raises(GeneratorError, match="Step 'fake' not found"):
            generator.generate_step_skill(job, fake_step, adapter, temp_dir)

    def test_generate_step_skill_raises_for_missing_instructions(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that missing instructions file raises error."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        # Save original instructions file content
        instructions_file = job_dir / "steps" / "single_step.md"
        original_content = instructions_file.read_text()

        try:
            # Delete the instructions file
            instructions_file.unlink()

            generator = SkillGenerator()
            adapter = ClaudeAdapter()

            with pytest.raises(GeneratorError, match="instructions file not found"):
                generator.generate_step_skill(job, job.steps[0], adapter, temp_dir)
        finally:
            # Restore the file
            instructions_file.write_text(original_content)

    def test_generate_all_skills(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skills for all steps in a job (meta + step skills)."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skill_paths = generator.generate_all_skills(job, adapter, temp_dir)

        # Now includes meta-skill plus step skills
        assert len(skill_paths) == 5  # 1 meta + 4 steps
        assert all(p.exists() for p in skill_paths)

        # Check filenames - meta-skill first, then step skills (no prefix)
        expected_names = [
            "competitive_research.md",  # Meta-skill
            "competitive_research.identify_competitors.md",  # Step skills
            "competitive_research.primary_research.md",
            "competitive_research.secondary_research.md",
            "competitive_research.comparative_report.md",
        ]
        actual_names = [p.name for p in skill_paths]
        assert actual_names == expected_names

    def test_generate_meta_skill(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating meta-skill for a job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        meta_skill_path = generator.generate_meta_skill(job, adapter, temp_dir)

        assert meta_skill_path.exists()
        assert meta_skill_path.name == "competitive_research.md"

        content = meta_skill_path.read_text()
        # Check meta-skill content
        assert "# competitive_research" in content
        assert "Available Steps" in content
        assert "identify_competitors" in content
        assert "primary_research" in content
        assert "Skill tool" in content

    def test_generate_step_skill_exposed_step(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skill for exposed step."""
        job_dir = fixtures_dir / "jobs" / "exposed_step_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Generate the exposed step (index 1)
        skill_path = generator.generate_step_skill(job, job.steps[1], adapter, temp_dir)

        assert skill_path.exists()
        # Same filename whether exposed or not (no prefix)
        assert skill_path.name == "exposed_job.exposed_step.md"

    def test_generate_all_skills_with_exposed_steps(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating all skills with mix of hidden and exposed steps."""
        job_dir = fixtures_dir / "jobs" / "exposed_step_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skill_paths = generator.generate_all_skills(job, adapter, temp_dir)

        # Meta-skill + 2 steps
        assert len(skill_paths) == 3
        assert all(p.exists() for p in skill_paths)

        # Check filenames - all have clean names (no prefix)
        expected_names = [
            "exposed_job.md",  # Meta-skill
            "exposed_job.hidden_step.md",  # Step skill
            "exposed_job.exposed_step.md",  # Step skill
        ]
        actual_names = [p.name for p in skill_paths]
        assert actual_names == expected_names
