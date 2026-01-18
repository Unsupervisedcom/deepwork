"""Integration tests for the fruits CI test workflow.

This module tests the fruits job - a simple, deterministic workflow
designed for automated CI testing of the DeepWork framework.
"""

from pathlib import Path

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import CommandGenerator
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
        assert identify_step.outputs == ["identified_fruits.md"]

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
        assert classify_step.outputs == ["classified_fruits.md"]

        # Depends on identify step
        assert classify_step.dependencies == ["identify"]

    def test_fruits_command_generation(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test that fruits job generates valid Claude commands."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()
        commands_dir = temp_dir / ".claude"
        commands_dir.mkdir()

        command_paths = generator.generate_all_commands(job, adapter, commands_dir)

        # Now includes meta-command + step commands
        assert len(command_paths) == 3  # 1 meta + 2 steps

        # Verify command files exist
        meta_cmd = commands_dir / "commands" / "fruits.md"
        identify_cmd = commands_dir / "commands" / "uw.fruits.identify.md"
        classify_cmd = commands_dir / "commands" / "uw.fruits.classify.md"
        assert meta_cmd.exists()
        assert identify_cmd.exists()
        assert classify_cmd.exists()

    def test_fruits_identify_command_content(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test the identify command has correct content."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()
        commands_dir = temp_dir / ".claude"
        commands_dir.mkdir()

        generator.generate_all_commands(job, adapter, commands_dir)

        # Step commands now have uw. prefix
        identify_cmd = commands_dir / "commands" / "uw.fruits.identify.md"
        content = identify_cmd.read_text()

        # Check header
        assert "# fruits.identify" in content

        # Check step info
        assert "Step 1 of 2" in content

        # Check user input is mentioned
        assert "raw_items" in content

        # Check output is mentioned
        assert "identified_fruits.md" in content

        # Check next step is suggested
        assert "/fruits.classify" in content

    def test_fruits_classify_command_content(self, fixtures_dir: Path, temp_dir: Path) -> None:
        """Test the classify command has correct content."""
        job_dir = fixtures_dir / "jobs" / "fruits"
        job = parse_job_definition(job_dir)

        generator = CommandGenerator()
        adapter = ClaudeAdapter()
        commands_dir = temp_dir / ".claude"
        commands_dir.mkdir()

        generator.generate_all_commands(job, adapter, commands_dir)

        # Step commands now have uw. prefix
        classify_cmd = commands_dir / "commands" / "uw.fruits.classify.md"
        content = classify_cmd.read_text()

        # Check header
        assert "# fruits.classify" in content

        # Check step info
        assert "Step 2 of 2" in content

        # Check file input is mentioned
        assert "identified_fruits.md" in content
        assert "from step `identify`" in content

        # Check output is mentioned
        assert "classified_fruits.md" in content

        # Check workflow complete (last step)
        assert "Workflow Complete" in content

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
        assert identify_step.outputs == ["identified_fruits.md"]
        assert classify_step.outputs == ["classified_fruits.md"]
