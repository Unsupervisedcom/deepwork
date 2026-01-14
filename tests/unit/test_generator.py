"""Tests for command generator."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import CommandGenerator, GeneratorError
from deepwork.core.parser import JobDefinition, Step, parse_job_definition


class TestCommandGenerator:
    """Tests for CommandGenerator class."""

    def test_init_default_templates_dir(self) -> None:
        """Test initialization with default templates directory."""
        generator = CommandGenerator()

        assert generator.templates_dir.exists()
        assert (generator.templates_dir / "claude").exists()

    def test_init_custom_templates_dir(self, temp_dir: Path) -> None:
        """Test initialization with custom templates directory."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        generator = CommandGenerator(templates_dir)

        assert generator.templates_dir == templates_dir

    def test_init_raises_for_missing_templates_dir(self, temp_dir: Path) -> None:
        """Test initialization raises error for missing templates directory."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(GeneratorError, match="Templates directory not found"):
            CommandGenerator(nonexistent)

    def test_generate_step_command_simple_job(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating command for simple job step."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_path = generator.generate_step_command(job, job.steps[0], adapter, temp_dir)

        assert command_path.exists()
        assert command_path.name == "simple_job.single_step.md"

        content = command_path.read_text()
        assert "# simple_job.single_step" in content
        # Single step with no dependencies is treated as standalone
        assert "Standalone command" in content
        assert "input_param" in content
        assert "output.md" in content

    def test_generate_step_command_complex_job_first_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating command for first step of complex job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_path = generator.generate_step_command(job, job.steps[0], adapter, temp_dir)

        content = command_path.read_text()
        assert "# competitive_research.identify_competitors" in content
        assert "Step 1 of 4" in content
        assert "market_segment" in content
        assert "product_category" in content
        # First step has no prerequisites
        assert "## Prerequisites" not in content
        # Has next step
        assert "/competitive_research.primary_research" in content

    def test_generate_step_command_complex_job_middle_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating command for middle step with dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        # Generate primary_research (step 2)
        command_path = generator.generate_step_command(job, job.steps[1], adapter, temp_dir)

        content = command_path.read_text()
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

    def test_generate_step_command_complex_job_final_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating command for final step."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        # Generate comparative_report (step 4)
        command_path = generator.generate_step_command(job, job.steps[3], adapter, temp_dir)

        content = command_path.read_text()
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

    def test_generate_step_command_raises_for_missing_step(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that generating command for non-existent step raises error."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
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
            generator.generate_step_command(job, fake_step, adapter, temp_dir)

    def test_generate_step_command_raises_for_missing_instructions(
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

            generator = CommandGenerator()
            adapter = ClaudeAdapter()

            with pytest.raises(GeneratorError, match="instructions file not found"):
                generator.generate_step_command(job, job.steps[0], adapter, temp_dir)
        finally:
            # Restore the file
            instructions_file.write_text(original_content)

    def test_generate_all_commands(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating commands for all steps in a job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_paths = generator.generate_all_commands(job, adapter, temp_dir)

        assert len(command_paths) == 4
        assert all(p.exists() for p in command_paths)

        # Check filenames
        expected_names = [
            "competitive_research.identify_competitors.md",
            "competitive_research.primary_research.md",
            "competitive_research.secondary_research.md",
            "competitive_research.comparative_report.md",
        ]
        actual_names = [p.name for p in command_paths]
        assert actual_names == expected_names


class TestSupplementaryFiles:
    """Tests for supplementary file handling."""

    def test_find_supplementary_files_empty_when_no_extras(
        self, fixtures_dir: Path
    ) -> None:
        """Test that no supplementary files are found when only step files exist."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        supplementary = generator._find_supplementary_files(job, job.steps[0])

        assert supplementary == []

    def test_find_supplementary_files_detects_extra_md_files(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test that supplementary .md files are detected."""
        # Copy simple job to temp dir and add supplementary file
        job_dir = temp_dir / ".deepwork" / "jobs" / "test_job"
        steps_dir = job_dir / "steps"
        steps_dir.mkdir(parents=True)

        # Create job.yml
        (job_dir / "job.yml").write_text("""
name: test_job
version: "1.0.0"
summary: "Test job"
description: "A test job"
steps:
  - id: step_one
    name: "Step One"
    description: "First step"
    instructions_file: steps/step_one.md
    outputs:
      - output.md
""")

        # Create step instruction file
        (steps_dir / "step_one.md").write_text("# Step One\n\nDo the thing.")

        # Create supplementary files
        (steps_dir / "reference.md").write_text("# Reference\n\nSome reference content.")
        (steps_dir / "template.md").write_text("# Template\n\nA template.")

        job = parse_job_definition(job_dir)
        generator = CommandGenerator()
        supplementary = generator._find_supplementary_files(job, job.steps[0])

        assert len(supplementary) == 2
        assert supplementary[0]["name"] == "reference.md"
        assert supplementary[0]["path"] == ".deepwork/jobs/test_job/steps/reference.md"
        assert supplementary[1]["name"] == "template.md"
        assert supplementary[1]["path"] == ".deepwork/jobs/test_job/steps/template.md"

    def test_transform_md_references_backticks(self) -> None:
        """Test transformation of backtick references."""
        generator = CommandGenerator()
        supplementary = [
            {"name": "foo.md", "path": ".deepwork/jobs/my_job/steps/foo.md"}
        ]

        content = "Read the file `foo.md` for details."
        result = generator._transform_md_references(content, supplementary)

        assert result == "Read the file `.deepwork/jobs/my_job/steps/foo.md` for details."

    def test_transform_md_references_markdown_links(self) -> None:
        """Test transformation of markdown link references."""
        generator = CommandGenerator()
        supplementary = [
            {"name": "template.md", "path": ".deepwork/jobs/my_job/steps/template.md"}
        ]

        content = "See [the template](template.md) for examples."
        result = generator._transform_md_references(content, supplementary)

        assert result == "See [the template](.deepwork/jobs/my_job/steps/template.md) for examples."

    def test_transform_md_references_quoted_strings(self) -> None:
        """Test transformation of quoted string references."""
        generator = CommandGenerator()
        supplementary = [
            {"name": "spec.md", "path": ".deepwork/jobs/my_job/steps/spec.md"}
        ]

        content = 'Load "spec.md" or \'spec.md\' for the specification.'
        result = generator._transform_md_references(content, supplementary)

        expected = 'Load ".deepwork/jobs/my_job/steps/spec.md" or \'.deepwork/jobs/my_job/steps/spec.md\' for the specification.'
        assert result == expected

    def test_transform_md_references_preserves_paths(self) -> None:
        """Test that existing paths are not double-transformed."""
        generator = CommandGenerator()
        supplementary = [
            {"name": "foo.md", "path": ".deepwork/jobs/my_job/steps/foo.md"}
        ]

        # Content with already-transformed path should not be affected
        content = "Already transformed: `.deepwork/jobs/my_job/steps/foo.md`"
        result = generator._transform_md_references(content, supplementary)

        # Should remain unchanged (the regex shouldn't match paths)
        assert result == content

    def test_transform_md_references_no_supplementary_files(self) -> None:
        """Test that content is unchanged when no supplementary files exist."""
        generator = CommandGenerator()

        content = "Read `something.md` for details."
        result = generator._transform_md_references(content, [])

        assert result == content

    def test_transform_md_references_multiple_files(self) -> None:
        """Test transformation with multiple supplementary files."""
        generator = CommandGenerator()
        supplementary = [
            {"name": "api.md", "path": ".deepwork/jobs/my_job/steps/api.md"},
            {"name": "schema.md", "path": ".deepwork/jobs/my_job/steps/schema.md"},
        ]

        content = "See `api.md` for the API and `schema.md` for the schema."
        result = generator._transform_md_references(content, supplementary)

        expected = "See `.deepwork/jobs/my_job/steps/api.md` for the API and `.deepwork/jobs/my_job/steps/schema.md` for the schema."
        assert result == expected

    def test_generate_command_includes_supplementary_files(
        self, temp_dir: Path
    ) -> None:
        """Test that generated commands include supplementary files section."""
        # Create a job with supplementary files
        job_dir = temp_dir / ".deepwork" / "jobs" / "test_job"
        steps_dir = job_dir / "steps"
        steps_dir.mkdir(parents=True)

        (job_dir / "job.yml").write_text("""
name: test_job
version: "1.0.0"
summary: "Test job"
description: "A test job"
steps:
  - id: step_one
    name: "Step One"
    description: "First step"
    instructions_file: steps/step_one.md
    outputs:
      - output.md
""")

        (steps_dir / "step_one.md").write_text("# Step One\n\nUse `reference.md` as a guide.")
        (steps_dir / "reference.md").write_text("# Reference\n\nReference content.")

        job = parse_job_definition(job_dir)
        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_path = generator.generate_step_command(job, job.steps[0], adapter, temp_dir)
        content = command_path.read_text()

        # Check that the reference was transformed
        assert ".deepwork/jobs/test_job/steps/reference.md" in content

        # Check that supplementary files section exists
        assert "Supplementary Reference Files" in content
        assert "`.deepwork/jobs/test_job/steps/reference.md`" in content
