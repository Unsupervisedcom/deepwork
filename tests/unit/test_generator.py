"""Tests for command generator."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import CommandGenerator, GeneratorError
from deepwork.core.parser import parse_job_definition


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
        """Test generating command for simple job step (hidden by default)."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_path = generator.generate_step_command(job, job.steps[0], adapter, temp_dir)

        assert command_path.exists()
        # Step commands are hidden by default (underscore prefix)
        assert command_path.name == "_simple_job.single_step.md"

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
        """Test generating commands for all steps in a job (meta + hidden steps)."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_paths = generator.generate_all_commands(job, adapter, temp_dir)

        # Now includes meta-command plus step commands
        assert len(command_paths) == 5  # 1 meta + 4 steps
        assert all(p.exists() for p in command_paths)

        # Check filenames - meta-command first, then hidden step commands
        expected_names = [
            "competitive_research.md",  # Meta-command
            "_competitive_research.identify_competitors.md",  # Hidden steps
            "_competitive_research.primary_research.md",
            "_competitive_research.secondary_research.md",
            "_competitive_research.comparative_report.md",
        ]
        actual_names = [p.name for p in command_paths]
        assert actual_names == expected_names

    def test_generate_meta_command(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating meta-command for a job."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        meta_command_path = generator.generate_meta_command(job, adapter, temp_dir)

        assert meta_command_path.exists()
        assert meta_command_path.name == "competitive_research.md"

        content = meta_command_path.read_text()
        # Check meta-command content
        assert "# competitive_research" in content
        assert "Available Steps" in content
        assert "identify_competitors" in content
        assert "primary_research" in content
        assert "Skill tool" in content

    def test_generate_step_command_exposed_step(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test generating command for exposed step (no underscore prefix)."""
        job_dir = fixtures_dir / "jobs" / "exposed_step_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        # Generate the exposed step (index 1)
        command_path = generator.generate_step_command(job, job.steps[1], adapter, temp_dir)

        assert command_path.exists()
        # Exposed step should NOT have underscore prefix
        assert command_path.name == "exposed_job.exposed_step.md"

    def test_generate_all_commands_with_exposed_steps(
        self, fixtures_dir: Path, temp_dir: Path
    ) -> None:
        """Test generating all commands with mix of hidden and exposed steps."""
        job_dir = fixtures_dir / "jobs" / "exposed_step_job"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        command_paths = generator.generate_all_commands(job, adapter, temp_dir)

        # Meta-command + 2 steps (1 hidden, 1 exposed)
        assert len(command_paths) == 3
        assert all(p.exists() for p in command_paths)

        # Check filenames - hidden step has underscore, exposed doesn't
        expected_names = [
            "exposed_job.md",  # Meta-command
            "_exposed_job.hidden_step.md",  # Hidden step
            "exposed_job.exposed_step.md",  # Exposed step (no underscore)
        ]
        actual_names = [p.name for p in command_paths]
        assert actual_names == expected_names
