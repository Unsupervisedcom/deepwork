"""Tests for skill generator."""

from pathlib import Path

import pytest

from deepwork.core.detector import PLATFORMS
from deepwork.core.generator import GeneratorError, SkillGenerator
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

    def test_generate_step_skill_simple_job(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for simple job step."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]

        skill_path = generator.generate_step_skill(
            job, job.steps[0], platform, temp_dir
        )

        assert skill_path.exists()
        assert skill_path.name == "skill-simple_job.single_step.md"

        content = skill_path.read_text()
        assert "Name: simple_job.single_step" in content
        assert "step 1 of 1" in content
        assert "input_param" in content
        assert "output.md" in content

    def test_generate_step_skill_complex_job_first_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for first step of complex job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]

        skill_path = generator.generate_step_skill(
            job, job.steps[0], platform, temp_dir
        )

        content = skill_path.read_text()
        assert "Name: competitive_research.identify_competitors" in content
        assert "step 1 of 4" in content
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
        platform = PLATFORMS["claude"]

        # Generate primary_research (step 2)
        skill_path = generator.generate_step_skill(
            job, job.steps[1], platform, temp_dir
        )

        content = skill_path.read_text()
        assert "Name: competitive_research.primary_research" in content
        assert "step 2 of 4" in content
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
        platform = PLATFORMS["claude"]

        # Generate comparative_report (step 4)
        skill_path = generator.generate_step_skill(
            job, job.steps[3], platform, temp_dir
        )

        content = skill_path.read_text()
        assert "Name: competitive_research.comparative_report" in content
        assert "step 4 of 4" in content
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
        platform = PLATFORMS["claude"]

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
            generator.generate_step_skill(job, fake_step, platform, temp_dir)

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
            platform = PLATFORMS["claude"]

            with pytest.raises(GeneratorError, match="instructions file not found"):
                generator.generate_step_skill(job, job.steps[0], platform, temp_dir)
        finally:
            # Restore the file
            instructions_file.write_text(original_content)

    def test_generate_all_skills(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skills for all steps in a job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]

        skill_paths = generator.generate_all_skills(job, platform, temp_dir)

        assert len(skill_paths) == 4
        assert all(p.exists() for p in skill_paths)

        # Check filenames
        expected_names = [
            "skill-competitive_research.identify_competitors.md",
            "skill-competitive_research.primary_research.md",
            "skill-competitive_research.secondary_research.md",
            "skill-competitive_research.comparative_report.md",
        ]
        actual_names = [p.name for p in skill_paths]
        assert actual_names == expected_names

    def test_generate_core_skills(self, temp_dir: Path) -> None:
        """Test generating core DeepWork skills."""
        generator = SkillGenerator()
        platform = PLATFORMS["claude"]

        skill_paths = generator.generate_core_skills(platform, temp_dir)

        assert len(skill_paths) == 2
        assert all(p.exists() for p in skill_paths)

        # Check filenames
        expected_names = [
            "skill-deepwork.define.md",
            "skill-deepwork.refine.md",
        ]
        actual_names = [p.name for p in skill_paths]
        assert actual_names == expected_names

        # Check content
        define_content = skill_paths[0].read_text()
        assert "Name: deepwork.define" in define_content
        assert "Interactive job definition wizard" in define_content

        refine_content = skill_paths[1].read_text()
        assert "Name: deepwork.refine" in refine_content
        assert "Refine and update existing job definitions" in refine_content

    def test_generate_step_skill_different_platform(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill for different platform (Gemini)."""
        # Create .gemini templates directory by copying from claude
        import shutil

        templates_dir = Path(__file__).parent.parent.parent / "src" / "deepwork" / "templates"
        gemini_templates = templates_dir / "gemini"
        gemini_templates.mkdir(exist_ok=True)

        try:
            # Copy templates from claude to gemini
            for template_file in (templates_dir / "claude").glob("*.jinja"):
                shutil.copy(template_file, gemini_templates / template_file.name)

            job_dir = fixtures_dir / "jobs" / "simple_job"
            job = parse_job_definition(job_dir)

            generator = SkillGenerator()
            platform = PLATFORMS["gemini"]

            skill_path = generator.generate_step_skill(
                job, job.steps[0], platform, temp_dir
            )

            # Gemini uses same prefix, just different directory
            assert skill_path.name == "skill-simple_job.single_step.md"
            assert skill_path.exists()
        finally:
            # Cleanup
            if gemini_templates.exists():
                shutil.rmtree(gemini_templates)

    def test_generate_raises_for_missing_platform_templates(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that missing platform templates raises error."""
        import shutil

        # Ensure gemini templates don't exist
        templates_dir = Path(__file__).parent.parent.parent / "src" / "deepwork" / "templates"
        gemini_templates = templates_dir / "gemini"
        if gemini_templates.exists():
            shutil.rmtree(gemini_templates)

        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        # Gemini templates don't exist
        platform = PLATFORMS["gemini"]

        with pytest.raises(GeneratorError, match="Templates for platform"):
            generator.generate_step_skill(job, job.steps[0], platform, temp_dir)
