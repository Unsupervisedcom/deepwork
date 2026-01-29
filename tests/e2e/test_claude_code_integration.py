"""End-to-end tests for DeepWork with Claude Code integration.

These tests validate that DeepWork-generated skills work correctly
with Claude Code. The tests can run in two modes:

1. **Generation-only mode** (default): Tests skill generation and structure
2. **Full e2e mode**: Actually executes skills with Claude Code

Set ANTHROPIC_API_KEY and DEEPWORK_E2E_FULL=true to run full e2e tests.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import SkillGenerator
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


class TestSkillGenerationE2E:
    """End-to-end tests for skill generation."""

    def test_generate_fruits_skills_in_temp_project(self) -> None:
        """Test generating fruits skills in a realistic project structure."""
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

            # Parse job and generate skills
            job = parse_job_definition(deepwork_dir / "fruits")
            generator = SkillGenerator()
            adapter = ClaudeAdapter()

            skills_dir = project_dir / ".claude"
            skills_dir.mkdir()

            skill_paths = generator.generate_all_skills(job, adapter, skills_dir)

            # Validate skills were generated (meta + steps)
            assert len(skill_paths) == 3  # 1 meta + 2 steps

            meta_skill = skills_dir / "skills" / "fruits" / "SKILL.md"
            identify_skill = skills_dir / "skills" / "fruits.identify" / "SKILL.md"
            classify_skill = skills_dir / "skills" / "fruits.classify" / "SKILL.md"

            assert meta_skill.exists()
            assert identify_skill.exists()
            assert classify_skill.exists()

            # Validate skill content
            identify_content = identify_skill.read_text()
            assert "# fruits.identify" in identify_content
            assert "raw_items" in identify_content
            assert "identified_fruits.md" in identify_content

            classify_content = classify_skill.read_text()
            assert "# fruits.classify" in classify_content
            assert "identified_fruits.md" in classify_content
            assert "classified_fruits.md" in classify_content

    def test_skill_structure_matches_claude_code_expectations(self) -> None:
        """Test that generated skills have the structure Claude Code expects."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
        job = parse_job_definition(fixtures_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / ".claude"
            skills_dir.mkdir()

            generator = SkillGenerator()
            adapter = ClaudeAdapter()
            generator.generate_all_skills(job, adapter, skills_dir)

            # Step skills use directory/SKILL.md format
            identify_skill = skills_dir / "skills" / "fruits.identify" / "SKILL.md"
            content = identify_skill.read_text()

            # Claude Code expects specific sections
            assert "# fruits.identify" in content  # Skill name header
            assert "## Instructions" in content  # Instructions section
            assert "## Required Inputs" in content  # Inputs section
            assert "## Outputs" in content  # Outputs section

            # Check for user input prompt
            assert "raw_items" in content

    def test_dependency_chain_in_skills(self) -> None:
        """Test that dependency chain is correctly represented in skills."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "jobs" / "fruits"
        job = parse_job_definition(fixtures_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / ".claude"
            skills_dir.mkdir()

            generator = SkillGenerator()
            adapter = ClaudeAdapter()
            generator.generate_all_skills(job, adapter, skills_dir)

            # Step skills use directory/SKILL.md format
            # First step should have no prerequisites
            identify_skill = skills_dir / "skills" / "fruits.identify" / "SKILL.md"
            identify_content = identify_skill.read_text()
            assert "## Prerequisites" not in identify_content

            # Second step should reference first step
            classify_skill = skills_dir / "skills" / "fruits.classify" / "SKILL.md"
            classify_content = classify_skill.read_text()
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
    def project_with_skills(self) -> Path:
        """Create a test project with generated skills."""
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

        # Generate skills
        job = parse_job_definition(deepwork_dir / "fruits")
        generator = SkillGenerator()
        adapter = ClaudeAdapter()

        skills_dir = project_dir / ".claude"
        skills_dir.mkdir()
        generator.generate_all_skills(job, adapter, skills_dir)

        yield project_dir

        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_fruits_workflow_execution(self, project_with_skills: Path) -> None:
        """Test executing the complete fruits workflow with Claude Code.

        Invokes /fruits once, which automatically runs all steps (identify + classify).
        """
        # Run Claude Code with the fruits skill - this executes the full workflow
        result = subprocess.run(
            ["claude", "--print", "/fruits"],
            input=f"raw_items: {TEST_INPUT}",
            cwd=project_with_skills,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for full workflow
        )

        assert result.returncode == 0, f"Claude Code failed: {result.stderr}"

        # Verify identify step output was created
        identify_output = project_with_skills / "identified_fruits.md"
        assert identify_output.exists(), "identified_fruits.md was not created"

        # Validate identify output content
        identify_content = identify_output.read_text().lower()
        for fruit in EXPECTED_FRUITS:
            assert fruit in identify_content, (
                f"Expected fruit '{fruit}' not found in identified_fruits.md"
            )

        # Verify classify step output was created
        classify_output = project_with_skills / "classified_fruits.md"
        assert classify_output.exists(), "classified_fruits.md was not created"

        # Validate classify output has category structure
        classify_content = classify_output.read_text().lower()
        categories = ["citrus", "tropical", "pome", "berries", "grape"]
        has_category = any(cat in classify_content for cat in categories)
        assert has_category, f"No fruit categories found in output: {classify_content[:500]}"

        # Validate final output quality
        assert len(classify_content) > 100, "Output seems too short"
        assert "##" in classify_output.read_text(), "Output lacks markdown structure"
