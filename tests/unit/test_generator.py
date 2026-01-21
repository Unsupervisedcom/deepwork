"""Tests for skill generator."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import GeneratorError, SkillGenerator
from deepwork.core.parser import Step, parse_job_definition


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
        # Step skills use directory/SKILL.md format
        assert skill_path.name == "SKILL.md"
        assert skill_path.parent.name == "simple_job.single_step"

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
        assert "Step 1/4" in content
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
        assert "Step 2/4" in content
        # Has prerequisites
        assert "## Prerequisites" in content
        assert "/competitive_research.identify_competitors" in content
        # Has file input
        assert "competitors.md" in content
        assert "from `identify_competitors`" in content
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
        assert "Step 4/4" in content
        # Has prerequisites
        assert "## Prerequisites" in content
        # Has multiple file inputs
        assert "primary_research.md" in content
        assert "secondary_research.md" in content
        # Final step - no next step
        assert "**Workflow complete**" in content
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

        # Check directory names - meta-skill first, then step skills
        # All files are named SKILL.md inside skill directories
        expected_dirs = [
            "competitive_research",  # Meta-skill
            "competitive_research.identify_competitors",  # Step skills
            "competitive_research.primary_research",
            "competitive_research.secondary_research",
            "competitive_research.comparative_report",
        ]
        actual_dirs = [p.parent.name for p in skill_paths]
        assert actual_dirs == expected_dirs
        assert all(p.name == "SKILL.md" for p in skill_paths)

    def test_generate_meta_skill(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating meta-skill for a job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        meta_skill_path = generator.generate_meta_skill(job, adapter, temp_dir)

        assert meta_skill_path.exists()
        assert meta_skill_path.name == "SKILL.md"
        assert meta_skill_path.parent.name == "competitive_research"

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
        # Uses directory/SKILL.md format whether exposed or not
        assert skill_path.name == "SKILL.md"
        assert skill_path.parent.name == "exposed_job.exposed_step"

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

        # Check directory names - all use directory/SKILL.md format
        expected_dirs = [
            "exposed_job",  # Meta-skill
            "exposed_job.hidden_step",  # Step skill
            "exposed_job.exposed_step",  # Step skill
        ]
        actual_dirs = [p.parent.name for p in skill_paths]
        assert actual_dirs == expected_dirs
        assert all(p.name == "SKILL.md" for p in skill_paths)


class TestDocSpecIntegration:
    """Tests for doc spec integration in skill generation."""

    def test_load_doc_spec_returns_parsed_spec(self, fixtures_dir: Path) -> None:
        """Test that _load_doc_spec loads and parses doc spec files."""
        generator = SkillGenerator()

        # Load the valid_report doc spec from fixtures
        doc_spec = generator._load_doc_spec(fixtures_dir, "doc_specs/valid_report.md")

        assert doc_spec is not None
        assert doc_spec.name == "Monthly Report"
        assert doc_spec.description == "A monthly summary report"
        assert doc_spec.target_audience == "Team leads"
        assert len(doc_spec.quality_criteria) == 2
        assert doc_spec.quality_criteria[0].name == "Summary"

    def test_load_doc_spec_caches_result(self, fixtures_dir: Path) -> None:
        """Test that doc specs are cached after first load."""
        generator = SkillGenerator()

        # Load same doc spec twice
        doc_spec1 = generator._load_doc_spec(fixtures_dir, "doc_specs/valid_report.md")
        doc_spec2 = generator._load_doc_spec(fixtures_dir, "doc_specs/valid_report.md")

        # Should be the same cached instance
        assert doc_spec1 is doc_spec2
        # Cache should have exactly one entry
        assert len(generator._doc_spec_cache) == 1

    def test_load_doc_spec_returns_none_for_missing_file(self, temp_dir: Path) -> None:
        """Test that _load_doc_spec returns None for non-existent file."""
        generator = SkillGenerator()

        result = generator._load_doc_spec(temp_dir, "nonexistent.md")

        assert result is None

    def test_load_doc_spec_returns_none_for_invalid_spec(self, temp_dir: Path) -> None:
        """Test that _load_doc_spec returns None for invalid doc spec file."""
        generator = SkillGenerator()

        # Create an invalid doc spec file (missing required fields)
        invalid_spec = temp_dir / "invalid.md"
        invalid_spec.write_text("""---
name: "Test"
---
Body content
""")

        result = generator._load_doc_spec(temp_dir, "invalid.md")

        assert result is None

    def test_generate_step_skill_with_doc_spec(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skill for step with doc spec-referenced output."""
        # Set up the directory structure so the doc spec can be found
        doc_specs_dir = temp_dir / ".deepwork" / "doc_specs"
        doc_specs_dir.mkdir(parents=True)

        # Copy the valid_report.md fixture to the expected location
        source_doc_spec = fixtures_dir / "doc_specs" / "valid_report.md"
        target_doc_spec = doc_specs_dir / "valid_report.md"
        target_doc_spec.write_text(source_doc_spec.read_text())

        # Parse the job with doc spec
        job_dir = fixtures_dir / "jobs" / "job_with_doc_spec"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Generate skill with project_root set to temp_dir so it finds doc specs
        skill_path = generator.generate_step_skill(
            job, job.steps[0], adapter, temp_dir, project_root=temp_dir
        )

        assert skill_path.exists()
        content = skill_path.read_text()

        # Verify doc spec info is injected into the skill
        assert "Doc Spec" in content
        assert "Monthly Report" in content
        assert "A monthly summary report" in content
        assert "Target Audience" in content
        assert "Team leads" in content
        assert "Quality Criteria" in content
        assert "Summary" in content
        assert "Must include executive summary" in content

    def test_generate_step_skill_without_doc_spec(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating skill for step without doc spec reference."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skill_path = generator.generate_step_skill(job, job.steps[0], adapter, temp_dir)

        content = skill_path.read_text()
        # Should not have doc spec section
        assert "Doc Spec:" not in content

    def test_generate_step_skill_with_missing_doc_spec_file(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating skill when doc spec file doesn't exist."""
        # Parse the job with doc spec but don't create the doc spec file
        job_dir = fixtures_dir / "jobs" / "job_with_doc_spec"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Generate skill without the doc spec file present
        # This should work but not include doc spec info
        skill_path = generator.generate_step_skill(
            job, job.steps[0], adapter, temp_dir, project_root=temp_dir
        )

        assert skill_path.exists()
        content = skill_path.read_text()

        # Should still generate the skill, just without doc spec details
        assert "job_with_doc_spec.generate_report" in content
        # Doc spec section should not appear since file is missing
        assert "Monthly Report" not in content

    def test_build_step_context_includes_doc_spec_info(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that _build_step_context includes doc spec info in outputs."""
        # Set up the directory structure
        doc_specs_dir = temp_dir / ".deepwork" / "doc_specs"
        doc_specs_dir.mkdir(parents=True)

        source_doc_spec = fixtures_dir / "doc_specs" / "valid_report.md"
        target_doc_spec = doc_specs_dir / "valid_report.md"
        target_doc_spec.write_text(source_doc_spec.read_text())

        job_dir = fixtures_dir / "jobs" / "job_with_doc_spec"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        context = generator._build_step_context(
            job, job.steps[0], 0, adapter, project_root=temp_dir
        )

        # Check outputs context has doc spec info
        assert "outputs" in context
        assert len(context["outputs"]) == 1

        output_ctx = context["outputs"][0]
        assert output_ctx["file"] == "report.md"
        assert output_ctx["has_doc_spec"] is True
        assert "doc_spec" in output_ctx

        doc_spec_ctx = output_ctx["doc_spec"]
        assert doc_spec_ctx["name"] == "Monthly Report"
        assert doc_spec_ctx["description"] == "A monthly summary report"
        assert doc_spec_ctx["target_audience"] == "Team leads"
        assert len(doc_spec_ctx["quality_criteria"]) == 2
        assert doc_spec_ctx["quality_criteria"][0]["name"] == "Summary"
        assert "example_document" in doc_spec_ctx

    def test_build_step_context_without_project_root(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that _build_step_context handles missing project_root."""
        job_dir = fixtures_dir / "jobs" / "job_with_doc_spec"
        job = parse_job_definition(job_dir)

        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        # Build context without project_root - should still work but no doc spec
        context = generator._build_step_context(job, job.steps[0], 0, adapter)

        output_ctx = context["outputs"][0]
        assert output_ctx["has_doc_spec"] is True  # Job still declares it
        # But doc_spec info won't be loaded since no project_root
        assert "doc_spec" not in output_ctx
