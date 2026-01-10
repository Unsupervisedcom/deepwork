"""Integration tests for full job workflow."""

from pathlib import Path

import pytest

from deepwork.core.detector import PLATFORMS
from deepwork.core.generator import SkillGenerator
from deepwork.core.parser import parse_job_definition
from deepwork.core.registry import JobRegistry


class TestJobWorkflow:
    """Integration tests for complete job workflow."""

    def test_parse_register_generate_workflow(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test complete workflow: parse job → register → generate skills."""
        # Step 1: Parse job definition
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        assert job.name == "competitive_research"
        assert len(job.steps) == 4

        # Step 2: Register job
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        entry = registry.register_job(
            job.name, job.version, job.description, str(job_dir)
        )

        assert entry.name == job.name
        assert registry.is_registered(job.name)

        # Step 3: Generate skills
        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, platform, skills_dir)

        assert len(skill_paths) == 4

        # Verify all skill files exist and have correct content
        for i, skill_path in enumerate(skill_paths):
            assert skill_path.exists()
            content = skill_path.read_text()

            # Check skill name format
            assert f"Name: {job.name}.{job.steps[i].id}" in content

            # Check step numbers
            assert f"step {i+1} of 4" in content

        # Step 4: Verify can read registry
        loaded_entry = registry.get_job(job.name)
        assert loaded_entry is not None
        assert loaded_entry.version == job.version

    def test_simple_job_workflow(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test workflow with simple single-step job."""
        # Parse
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        assert len(job.steps) == 1

        # Register
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)
        registry.register_job(job.name, job.version, job.description, str(job_dir))

        # Generate
        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, platform, skills_dir)

        assert len(skill_paths) == 1

        # Verify skill content
        content = skill_paths[0].read_text()
        assert "Name: simple_job.single_step" in content
        assert "step 1 of 1" in content
        assert "input_param" in content
        assert "Workflow Complete" in content  # Final step message

    def test_multiple_jobs_registration(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test registering multiple jobs."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        # Parse and register first job
        job1_dir = fixtures_dir / "jobs" / "simple_job"
        job1 = parse_job_definition(job1_dir)
        registry.register_job(job1.name, job1.version, job1.description, str(job1_dir))

        # Parse and register second job
        job2_dir = fixtures_dir / "jobs" / "complex_job"
        job2 = parse_job_definition(job2_dir)
        registry.register_job(job2.name, job2.version, job2.description, str(job2_dir))

        # List all jobs
        jobs = registry.list_jobs()
        assert len(jobs) == 2

        # Jobs should be sorted by name
        assert jobs[0].name == "competitive_research"
        assert jobs[1].name == "simple_job"

    def test_job_update_workflow(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test updating a registered job."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        # Register job
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)
        registry.register_job(job.name, job.version, job.description, str(job_dir))

        # Update version
        updated = registry.update_job(job.name, version="2.0.0")
        assert updated.version == "2.0.0"

        # Verify update persisted
        loaded = registry.get_job(job.name)
        assert loaded is not None
        assert loaded.version == "2.0.0"

    def test_skill_generation_with_dependencies(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that generated skills properly handle dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, platform, skills_dir)

        # Check first step (no prerequisites)
        step1_content = skill_paths[0].read_text()
        assert "## Prerequisites" not in step1_content
        assert "/competitive_research.primary_research" in step1_content  # Next step

        # Check second step (has prerequisites and next step)
        step2_content = skill_paths[1].read_text()
        assert "## Prerequisites" in step2_content
        assert "/competitive_research.identify_competitors" in step2_content
        assert "/competitive_research.secondary_research" in step2_content  # Next step

        # Check last step (has prerequisites, no next step)
        step4_content = skill_paths[3].read_text()
        assert "## Prerequisites" in step4_content
        assert "## Workflow Complete" in step4_content
        assert "## Next Step" not in step4_content

    def test_skill_generation_with_file_inputs(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that generated skills properly handle file inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, platform, skills_dir)

        # Check step with file input
        step2_content = skill_paths[1].read_text()  # primary_research
        assert "## Inputs" in step2_content
        assert "### Required Files" in step2_content
        assert "competitors.md" in step2_content
        assert "from step `identify_competitors`" in step2_content

        # Check step with multiple file inputs
        step4_content = skill_paths[3].read_text()  # comparative_report
        assert "primary_research.md" in step4_content
        assert "secondary_research.md" in step4_content

    def test_skill_generation_with_user_inputs(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that generated skills properly handle user parameter inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, platform, skills_dir)

        # Check step with user inputs
        step1_content = skill_paths[0].read_text()  # identify_competitors
        assert "## Inputs" in step1_content
        assert "### User Parameters" in step1_content
        assert "market_segment" in step1_content
        assert "product_category" in step1_content

    def test_core_skills_generation(self, temp_dir: Path) -> None:
        """Test generation of core DeepWork skills."""
        generator = SkillGenerator()
        platform = PLATFORMS["claude"]
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_core_skills(platform, skills_dir)

        assert len(skill_paths) == 2

        # Check define skill
        define_path = skills_dir / "skill-deepwork.define.md"
        assert define_path.exists()
        define_content = define_path.read_text()
        assert "Name: deepwork.define" in define_content
        assert "Interactive job definition wizard" in define_content

        # Check refine skill
        refine_path = skills_dir / "skill-deepwork.refine.md"
        assert refine_path.exists()
        refine_content = refine_path.read_text()
        assert "Name: deepwork.refine" in refine_content
        assert "Refine and update existing job definitions" in refine_content
