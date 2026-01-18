"""End-to-end tests for DeepWork with Claude Code integration.

These tests validate that DeepWork-generated commands work correctly
with Claude Code. The tests can run in two modes:

1. **Generation-only mode** (default): Tests command generation and structure
2. **Full e2e mode**: Actually executes commands with Claude Code

Set ANTHROPIC_API_KEY and DEEPWORK_E2E_FULL=true to run full e2e tests.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import CommandGenerator
from deepwork.core.parser import parse_job_definition

# Test input for deterministic validation
TEST_INPUT = "apple, car, banana, chair, orange, table, mango, laptop, grape, bicycle"

# Expected fruits from test input (for validation)
EXPECTED_FRUITS = {"apple", "banana", "orange", "mango", "grape"}


def has_claude_code() -> bool:
    """Check if Claude Code CLI is available."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def has_api_key() -> bool:
    """Check if Anthropic API key is set."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def run_full_e2e() -> bool:
    """Check if full e2e tests should run."""
    return (
        os.environ.get("DEEPWORK_E2E_FULL", "").lower() == "true"
        and has_api_key()
        and has_claude_code()
    )


class TestCommandGenerationE2E:
    """End-to-end tests for command generation."""

    def test_generate_fruits_commands_in_temp_project(self) -> None:
        """Test generating fruits commands in a realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Set up project structure
            deepwork_dir = project_dir / ".deepwork" / "jobs"
            deepwork_dir.mkdir(parents=True)

            # Copy fruits job fixture
            fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
            shutil.copytree(fixtures_dir, deepwork_dir / "fruits")

            # Initialize git repo (required for some operations)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=project_dir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=project_dir,
                capture_output=True,
            )

            # Parse job and generate commands
            job = parse_job_definition(deepwork_dir / "fruits")
            generator = CommandGenerator()
            adapter = ClaudeAdapter()

            commands_dir = project_dir / ".claude"
            commands_dir.mkdir()

            command_paths = generator.generate_all_commands(job, adapter, commands_dir)

            # Validate commands were generated (1 meta + 2 steps)
            assert len(command_paths) == 3

            meta_cmd = commands_dir / "commands" / "fruits.md"
            identify_cmd = commands_dir / "commands" / "uw.fruits.identify.md"
            classify_cmd = commands_dir / "commands" / "uw.fruits.classify.md"

            assert meta_cmd.exists()
            assert identify_cmd.exists()
            assert classify_cmd.exists()

            # Validate command content
            identify_content = identify_cmd.read_text()
            assert "# fruits.identify" in identify_content
            assert "raw_items" in identify_content
            assert "identified_fruits.md" in identify_content

            classify_content = classify_cmd.read_text()
            assert "# fruits.classify" in classify_content
            assert "identified_fruits.md" in classify_content
            assert "classified_fruits.md" in classify_content

    def test_command_structure_matches_claude_code_expectations(self) -> None:
        """Test that generated commands have the structure Claude Code expects."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
        job = parse_job_definition(fixtures_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            commands_dir = Path(tmpdir) / ".claude"
            commands_dir.mkdir()

            generator = CommandGenerator()
            adapter = ClaudeAdapter()
            generator.generate_all_commands(job, adapter, commands_dir)

            # Step commands are now hidden (uw. prefix)
            identify_cmd = commands_dir / "commands" / "uw.fruits.identify.md"
            content = identify_cmd.read_text()

            # Claude Code expects specific sections
            assert "# fruits.identify" in content  # Command name header
            assert "## Instructions" in content  # Instructions section
            assert "## Inputs" in content  # Inputs section
            assert "## Output" in content  # Output section

            # Check for user input prompt
            assert "raw_items" in content

    def test_dependency_chain_in_commands(self) -> None:
        """Test that dependency chain is correctly represented in commands."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
        job = parse_job_definition(fixtures_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            commands_dir = Path(tmpdir) / ".claude"
            commands_dir.mkdir()

            generator = CommandGenerator()
            adapter = ClaudeAdapter()
            generator.generate_all_commands(job, adapter, commands_dir)

            # Step commands are now hidden (uw. prefix)
            # First step should have no prerequisites
            identify_cmd = commands_dir / "commands" / "uw.fruits.identify.md"
            identify_content = identify_cmd.read_text()
            assert "## Prerequisites" not in identify_content

            # Second step should reference first step
            classify_cmd = commands_dir / "commands" / "uw.fruits.classify.md"
            classify_content = classify_cmd.read_text()
            assert "## Prerequisites" in classify_content
            assert "identify" in classify_content.lower()


@pytest.mark.skipif(
    not run_full_e2e(),
    reason="Full e2e requires ANTHROPIC_API_KEY, DEEPWORK_E2E_FULL=true, and claude CLI",
)
class TestClaudeCodeExecution:
    """End-to-end tests that actually execute with Claude Code.

    These tests only run when:
    - ANTHROPIC_API_KEY is set
    - DEEPWORK_E2E_FULL=true
    - Claude Code CLI is installed
    """

    @pytest.fixture
    def project_with_commands(self) -> Path:
        """Create a test project with generated commands."""
        tmpdir = tempfile.mkdtemp()
        project_dir = Path(tmpdir)

        # Set up project structure
        deepwork_dir = project_dir / ".deepwork" / "jobs"
        deepwork_dir.mkdir(parents=True)

        # Copy fruits job fixture
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
        shutil.copytree(fixtures_dir, deepwork_dir / "fruits")

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=project_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=project_dir,
            capture_output=True,
        )

        # Create README
        (project_dir / "README.md").write_text("# Test Project\n")
        subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=project_dir,
            capture_output=True,
        )

        # Generate commands
        job = parse_job_definition(deepwork_dir / "fruits")
        generator = CommandGenerator()
        adapter = ClaudeAdapter()

        commands_dir = project_dir / ".claude"
        commands_dir.mkdir()
        generator.generate_all_commands(job, adapter, commands_dir)

        yield project_dir

        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_identify_step_execution(self, project_with_commands: Path) -> None:
        """Test executing the identify step with Claude Code."""
        # Run Claude Code with the identify command
        result = subprocess.run(
            [
                "claude",
                "--yes",
                "--print",
                f"/fruits.identify raw_items: {TEST_INPUT}",
            ],
            cwd=project_with_commands,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"Claude Code failed: {result.stderr}"

        # Check output file was created
        output_file = project_with_commands / "identified_fruits.md"
        assert output_file.exists(), "identified_fruits.md was not created"

        # Validate content
        content = output_file.read_text().lower()
        for fruit in EXPECTED_FRUITS:
            assert fruit in content, f"Expected fruit '{fruit}' not found in output"

    def test_classify_step_execution(self, project_with_commands: Path) -> None:
        """Test executing the classify step with Claude Code."""
        # First, create the input file (simulate identify step output)
        identify_output = project_with_commands / "identified_fruits.md"
        identify_output.write_text(
            "# Identified Fruits\n\n- apple\n- banana\n- orange\n- mango\n- grape\n"
        )

        # Run Claude Code with the classify command
        result = subprocess.run(
            ["claude", "--yes", "--print", "/fruits.classify"],
            cwd=project_with_commands,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"Claude Code failed: {result.stderr}"

        # Check output file was created
        output_file = project_with_commands / "classified_fruits.md"
        assert output_file.exists(), "classified_fruits.md was not created"

        # Validate content has category structure
        content = output_file.read_text().lower()
        # Should have at least one category mentioned
        categories = ["citrus", "tropical", "pome", "berries", "grape"]
        has_category = any(cat in content for cat in categories)
        assert has_category, f"No fruit categories found in output: {content[:500]}"

    def test_full_workflow_execution(self, project_with_commands: Path) -> None:
        """Test executing the complete fruits workflow with Claude Code."""
        # Run identify step
        result1 = subprocess.run(
            [
                "claude",
                "--yes",
                "--print",
                f"/fruits.identify raw_items: {TEST_INPUT}",
            ],
            cwd=project_with_commands,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result1.returncode == 0, f"Identify step failed: {result1.stderr}"

        # Verify identify output exists
        identify_output = project_with_commands / "identified_fruits.md"
        assert identify_output.exists(), "Identify step did not create output"

        # Run classify step
        result2 = subprocess.run(
            ["claude", "--yes", "--print", "/fruits.classify"],
            cwd=project_with_commands,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result2.returncode == 0, f"Classify step failed: {result2.stderr}"

        # Verify classify output exists
        classify_output = project_with_commands / "classified_fruits.md"
        assert classify_output.exists(), "Classify step did not create output"

        # Validate final output quality
        content = classify_output.read_text()
        assert len(content) > 100, "Output seems too short"
        assert "##" in content, "Output lacks markdown structure"
