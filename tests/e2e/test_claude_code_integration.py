"""End-to-end tests for DeepWork with Claude Code integration.

These tests validate that DeepWork MCP-based workflows work correctly.
The tests can run in two modes:

1. **MCP tools mode** (default): Tests MCP skill generation and workflow tools
2. **Full e2e mode**: Actually executes workflows with Claude Code via MCP

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
from deepwork.mcp.state import StateManager
from deepwork.mcp.tools import WorkflowTools

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


class TestMCPSkillGeneration:
    """Tests for MCP entry point skill generation."""

    def test_generate_deepwork_skill_in_temp_project(self) -> None:
        """Test generating the /deepwork MCP skill in a realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Set up project structure
            deepwork_dir = project_dir / ".deepwork" / "jobs"
            deepwork_dir.mkdir(parents=True)

            # Copy fruits job fixture (for job discovery testing)
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

            # Generate MCP entry point skill
            generator = SkillGenerator()
            adapter = ClaudeAdapter(project_root=project_dir)

            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            skill_path = generator.generate_deepwork_skill(adapter, claude_dir)

            # Validate skill was generated
            assert skill_path.exists()
            expected_path = claude_dir / "skills" / "deepwork" / "SKILL.md"
            assert skill_path == expected_path

    def test_deepwork_skill_structure(self) -> None:
        """Test that the generated /deepwork skill has the expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir(parents=True)

            generator = SkillGenerator()
            adapter = ClaudeAdapter(project_root=project_dir)
            skill_path = generator.generate_deepwork_skill(adapter, claude_dir)

            content = skill_path.read_text()

            # Check frontmatter
            assert "---" in content
            assert "name: deepwork" in content

            # Check MCP tool references
            assert "get_workflows" in content
            assert "start_workflow" in content
            assert "finished_step" in content

            # Check structure sections
            assert "# DeepWork" in content
            assert "MCP" in content

    def test_deepwork_skill_mcp_instructions(self) -> None:
        """Test that the /deepwork skill properly instructs use of MCP tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir(parents=True)

            generator = SkillGenerator()
            adapter = ClaudeAdapter(project_root=project_dir)
            skill_path = generator.generate_deepwork_skill(adapter, claude_dir)

            content = skill_path.read_text()

            # Should instruct to use MCP tools, not read files
            assert "MCP" in content
            assert "tool" in content.lower()

            # Should describe the workflow execution flow
            assert "start_workflow" in content
            assert "finished_step" in content


class TestMCPWorkflowTools:
    """Tests for MCP workflow tools functionality."""

    @pytest.fixture
    def project_with_job(self) -> Path:
        """Create a test project with a job definition."""
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

        # Create README and initial commit
        (project_dir / "README.md").write_text("# Test Project\n")
        subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=project_dir,
            capture_output=True,
        )

        yield project_dir

        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_workflows_returns_jobs(self, project_with_job: Path) -> None:
        """Test that get_workflows returns available jobs and workflows."""
        state_manager = StateManager(project_with_job)
        tools = WorkflowTools(project_with_job, state_manager)

        response = tools.get_workflows()

        # Should find the fruits job
        assert len(response.jobs) >= 1
        job_names = [job.name for job in response.jobs]
        assert "fruits" in job_names

        # Find fruits job and check structure
        fruits_job = next(j for j in response.jobs if j.name == "fruits")
        assert fruits_job.description is not None

        # The fruits fixture has a "full" workflow
        assert len(fruits_job.workflows) >= 1
        full_workflow = fruits_job.workflows[0]
        assert full_workflow.name == "full"
        assert full_workflow.summary is not None

    async def test_start_workflow_creates_session(self, project_with_job: Path) -> None:
        """Test that start_workflow creates a new workflow session."""
        state_manager = StateManager(project_with_job)
        tools = WorkflowTools(project_with_job, state_manager)

        # Get available workflows first
        workflows_response = tools.get_workflows()
        fruits_job = next(j for j in workflows_response.jobs if j.name == "fruits")

        # Should have the "full" workflow
        assert len(fruits_job.workflows) >= 1
        workflow_name = fruits_job.workflows[0].name

        from deepwork.mcp.schemas import StartWorkflowInput

        input_data = StartWorkflowInput(
            goal="Test identifying and classifying fruits",
            job_name="fruits",
            workflow_name=workflow_name,
            instance_id="test-instance",
        )

        response = await tools.start_workflow(input_data)

        # Should return session info
        assert response.begin_step.session_id is not None
        assert response.begin_step.branch_name is not None
        assert "deepwork" in response.begin_step.branch_name.lower()
        assert "fruits" in response.begin_step.branch_name.lower()

        # Should return first step instructions
        assert response.begin_step.step_id is not None
        assert response.begin_step.step_instructions is not None
        assert len(response.begin_step.step_instructions) > 0

    async def test_workflow_step_progression(self, project_with_job: Path) -> None:
        """Test that finished_step progresses through workflow steps."""
        state_manager = StateManager(project_with_job)
        tools = WorkflowTools(project_with_job, state_manager)

        # Get workflows and start
        workflows_response = tools.get_workflows()
        fruits_job = next(j for j in workflows_response.jobs if j.name == "fruits")

        # Should have the "full" workflow
        assert len(fruits_job.workflows) >= 1
        workflow_name = fruits_job.workflows[0].name

        from deepwork.mcp.schemas import FinishedStepInput, StartWorkflowInput

        start_input = StartWorkflowInput(
            goal="Test workflow progression",
            job_name="fruits",
            workflow_name=workflow_name,
        )
        await tools.start_workflow(start_input)

        # Create mock output file for first step
        output_file = project_with_job / "identified_fruits.md"
        output_file.write_text("# Identified Fruits\n\n- apple\n- banana\n- orange\n")

        # Report first step completion
        finish_input = FinishedStepInput(
            outputs=[str(output_file)],
            notes="Identified fruits from test input",
        )
        finish_response = await tools.finished_step(finish_input)

        # Should either advance to next step or complete
        assert finish_response.status in ["next_step", "workflow_complete", "needs_work"]

        if finish_response.status == "next_step":
            # Should have instructions for next step
            assert finish_response.begin_step is not None
            assert finish_response.begin_step.step_instructions is not None
            assert finish_response.begin_step.step_id is not None


@pytest.mark.skipif(
    not run_full_e2e(),
    reason="Full e2e requires ANTHROPIC_API_KEY, DEEPWORK_E2E_FULL=true, and claude CLI",
)
class TestClaudeCodeMCPExecution:
    """End-to-end tests that actually execute with Claude Code via MCP.

    These tests only run when:
    - ANTHROPIC_API_KEY is set
    - DEEPWORK_E2E_FULL=true
    - Claude Code CLI is installed
    """

    @pytest.fixture
    def project_with_mcp(self) -> Path:
        """Create a test project with MCP server configured."""
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

        # Generate /deepwork skill
        generator = SkillGenerator()
        adapter = ClaudeAdapter(project_root=project_dir)

        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        generator.generate_deepwork_skill(adapter, claude_dir)

        # Register MCP server
        adapter.register_mcp_server(project_dir)

        yield project_dir

        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_fruits_workflow_via_mcp(self, project_with_mcp: Path) -> None:
        """Test executing the fruits workflow via MCP tools.

        Uses /deepwork skill which instructs Claude to use MCP tools
        for workflow orchestration.
        """
        # Run Claude Code with the /deepwork skill
        # The skill instructs Claude to use MCP tools
        result = subprocess.run(
            [
                "claude",
                "--print",
                f"Use /deepwork to start a fruits workflow. "
                f"For the identify step, use these items: {TEST_INPUT}",
            ],
            cwd=project_with_mcp,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for full workflow
        )

        assert result.returncode == 0, f"Claude Code failed: {result.stderr}"

        # Verify identify step output was created
        identify_output = project_with_mcp / "identified_fruits.md"
        assert identify_output.exists(), "identified_fruits.md was not created"

        # Validate identify output content
        identify_content = identify_output.read_text().lower()
        for fruit in EXPECTED_FRUITS:
            assert fruit in identify_content, (
                f"Expected fruit '{fruit}' not found in identified_fruits.md"
            )

        # Verify classify step output was created
        classify_output = project_with_mcp / "classified_fruits.md"
        assert classify_output.exists(), "classified_fruits.md was not created"

        # Validate classify output has category structure
        classify_content = classify_output.read_text().lower()
        categories = ["citrus", "tropical", "pome", "berries", "grape"]
        has_category = any(cat in classify_content for cat in categories)
        assert has_category, f"No fruit categories found in output: {classify_content[:500]}"

        # Validate final output quality
        assert len(classify_content) > 100, "Output seems too short"
        assert "##" in classify_output.read_text(), "Output lacks markdown structure"
