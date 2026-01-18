"""Integration tests for full job workflow."""

from pathlib import Path

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.parser import parse_job_definition


class TestJobWorkflow:
    """Integration tests for complete job workflow."""

    def test_parse_and_generate_workflow(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test complete workflow: parse job → generate skills."""
        # Step 1: Parse job definition
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        assert job.name == "competitive_research"
        assert len(job.steps) == 4

        # Step 2: Generate skills
        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # Now includes meta-skill + step skills
        assert len(skill_paths) == 5  # 1 meta + 4 steps

        # First skill is the meta-skill
        assert skill_paths[0].exists()
        meta_content = skill_paths[0].read_text()
        assert f"# {job.name}" in meta_content
        assert "Available Steps" in meta_content

        # Verify all step skill files exist and have correct content
        for i, skill_path in enumerate(skill_paths[1:]):  # Skip meta-skill
            assert skill_path.exists()
            content = skill_path.read_text()

            # Check skill name format (header)
            assert f"# {job.name}.{job.steps[i].id}" in content

            # Check step numbers
            assert f"Step {i + 1} of 4" in content

    def test_simple_job_workflow(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test workflow with simple single-step job."""
        # Parse
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        assert len(job.steps) == 1

        # Generate
        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # Now includes meta-skill + step skills
        assert len(skill_paths) == 2  # 1 meta + 1 step

        # Verify step skill content (skip meta-skill at index 0)
        content = skill_paths[1].read_text()
        assert "# simple_job.single_step" in content
        # Single step with no dependencies is treated as standalone
        assert "Standalone skill" in content
        assert "input_param" in content
        assert "Skill Complete" in content  # Standalone completion message

    def test_skill_generation_with_dependencies(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test that generated skills properly handle dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # skill_paths[0] is meta-skill, steps start at index 1

        # Check first step (no prerequisites)
        step1_content = skill_paths[1].read_text()
        assert "## Prerequisites" not in step1_content
        assert "/competitive_research.primary_research" in step1_content  # Next step

        # Check second step (has prerequisites and next step)
        step2_content = skill_paths[2].read_text()
        assert "## Prerequisites" in step2_content
        assert "/competitive_research.identify_competitors" in step2_content
        assert "/competitive_research.secondary_research" in step2_content  # Next step

        # Check last step (has prerequisites, no next step)
        step4_content = skill_paths[4].read_text()
        assert "## Prerequisites" in step4_content
        assert "## Workflow Complete" in step4_content
        assert "## Next Step" not in step4_content

    def test_skill_generation_with_file_inputs(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test that generated skills properly handle file inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # skill_paths[0] is meta-skill, steps start at index 1

        # Check step with file input
        step2_content = skill_paths[2].read_text()  # primary_research (index 2)
        assert "## Inputs" in step2_content
        assert "### Required Files" in step2_content
        assert "competitors.md" in step2_content
        assert "from step `identify_competitors`" in step2_content

        # Check step with multiple file inputs
        step4_content = skill_paths[4].read_text()  # comparative_report (index 4)
        assert "primary_research.md" in step4_content
        assert "secondary_research.md" in step4_content

    def test_skill_generation_with_user_inputs(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test that generated skills properly handle user parameter inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()
        skills_dir = temp_dir / ".claude"
        skills_dir.mkdir()

        skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

        # skill_paths[0] is meta-skill, steps start at index 1

        # Check step with user inputs
        step1_content = skill_paths[1].read_text()  # identify_competitors (index 1)
        assert "## Inputs" in step1_content
        assert "### User Parameters" in step1_content
        assert "market_segment" in step1_content
        assert "product_category" in step1_content
