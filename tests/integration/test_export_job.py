"""Integration tests for the export-job command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli


@pytest.fixture
def mock_installed_project(mock_claude_project: Path) -> Path:
    """Create a mock project with DeepWork already installed and a job defined."""
    # Install DeepWork first
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["install", "--platform", "claude", "--path", str(mock_claude_project)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Create a simple test job
    jobs_dir = mock_claude_project / ".deepwork" / "jobs"
    test_job_dir = jobs_dir / "test_export_job"
    test_job_dir.mkdir(exist_ok=True)

    job_yml_content = """name: test_export_job
version: "1.0.0"
summary: "Test job for export functionality"
description: |
  This is a test job used to verify the export-job command.

steps:
  - id: step_one
    name: "First Step"
    description: "A simple first step"
    instructions_file: steps/step_one.md
    inputs:
      - name: input_param
        description: "An input parameter"
    outputs:
      - output.txt
    dependencies: []
"""
    (test_job_dir / "job.yml").write_text(job_yml_content)

    # Create steps directory
    steps_dir = test_job_dir / "steps"
    steps_dir.mkdir(exist_ok=True)
    (steps_dir / "step_one.md").write_text("# Step One Instructions\nDo something.")

    # Note: We don't need to run sync here, the export command will generate skills itself

    return mock_claude_project


@pytest.fixture
def clean_global_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock the global Claude directory to a temporary location."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    return fake_home


class TestExportJobCommand:
    """Integration tests for 'deepwork export-job' command."""

    def test_export_job_basic(
        self, mock_installed_project: Path, clean_global_claude: Path
    ) -> None:
        """Test basic job export functionality."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Exporting Job to Global Claude Settings" in result.output
        assert "Job 'test_export_job' validated" in result.output
        assert "Job copied to" in result.output
        assert "Generated" in result.output
        assert "skills" in result.output
        assert "exported successfully" in result.output

        # Verify job was copied to global directory
        global_job_dir = clean_global_claude / ".deepwork" / "jobs" / "test_export_job"
        assert global_job_dir.exists()
        assert (global_job_dir / "job.yml").exists()
        assert (global_job_dir / "steps" / "step_one.md").exists()

        # Verify skills were generated in global Claude directory
        global_skills_dir = clean_global_claude / ".claude" / "skills"
        assert global_skills_dir.exists()
        assert (global_skills_dir / "test_export_job" / "SKILL.md").exists()
        assert (global_skills_dir / "test_export_job.step_one" / "SKILL.md").exists()

        # Verify global Claude settings.json was updated
        global_settings_file = clean_global_claude / ".claude" / "settings.json"
        assert global_settings_file.exists()
        with open(global_settings_file, encoding="utf-8") as f:
            settings = json.load(f)
        assert "permissions" in settings
        assert "allow" in settings["permissions"]
        # Check for DeepWork permissions
        assert any("deepwork" in perm for perm in settings["permissions"]["allow"])

    def test_export_job_not_found(self, mock_claude_project: Path, clean_global_claude: Path) -> None:
        """Test exporting a non-existent job."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["export-job", "nonexistent_job", "--path", str(mock_claude_project)],
        )

        assert result.exit_code != 0
        assert "Job 'nonexistent_job' not found" in result.output

    def test_export_job_overwrite_prompt(
        self, mock_installed_project: Path, clean_global_claude: Path
    ) -> None:
        """Test overwrite prompt when job already exists globally."""
        runner = CliRunner()

        # Export job first time
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Try to export again without force flag (answer 'n' to prompt)
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            input="n\n",
        )
        assert result.exit_code != 0  # Aborted
        assert "already exists in global settings" in result.output
        assert "Export cancelled" in result.output

    def test_export_job_overwrite_with_confirmation(
        self, mock_installed_project: Path, clean_global_claude: Path
    ) -> None:
        """Test overwrite with user confirmation."""
        runner = CliRunner()

        # Export job first time
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Modify the global job to verify it gets overwritten
        global_job_yml = clean_global_claude / ".deepwork" / "jobs" / "test_export_job" / "job.yml"
        original_content = global_job_yml.read_text()
        global_job_yml.write_text("modified: true\n")

        # Try to export again with confirmation (answer 'y' to prompt)
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            input="y\n",
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "already exists in global settings" in result.output
        assert "exported successfully" in result.output

        # Verify the file was overwritten (not modified)
        assert global_job_yml.read_text() == original_content

    def test_export_job_force_flag(
        self, mock_installed_project: Path, clean_global_claude: Path
    ) -> None:
        """Test export with force flag skips confirmation."""
        runner = CliRunner()

        # Export job first time
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Export again with --force flag
        result = runner.invoke(
            cli,
            ["export-job", "test_export_job", "--path", str(mock_installed_project), "--force"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "already exists" not in result.output  # No prompt shown
        assert "exported successfully" in result.output

    def test_export_job_with_doc_specs(
        self, mock_installed_project: Path, clean_global_claude: Path
    ) -> None:
        """Test exporting a job with doc specs."""
        # Create a job with doc specs
        jobs_dir = mock_installed_project / ".deepwork" / "jobs"
        test_job_dir = jobs_dir / "job_with_docspec"
        test_job_dir.mkdir(exist_ok=True)

        job_yml_content = """name: job_with_docspec
version: "1.0.0"
summary: "Test job with doc specs"
description: "Test job with doc specs"

steps:
  - id: create_report
    name: "Create Report"
    description: "Creates a report"
    instructions_file: steps/create_report.md
    inputs: []
    outputs:
      - file: report.md
        doc_spec: .deepwork/doc_specs/report_spec.md
    dependencies: []
"""
        (test_job_dir / "job.yml").write_text(job_yml_content)

        # Create steps directory
        steps_dir = test_job_dir / "steps"
        steps_dir.mkdir(exist_ok=True)
        (steps_dir / "create_report.md").write_text("# Create Report\nGenerate a report.")

        # Create doc spec
        doc_specs_dir = mock_installed_project / ".deepwork" / "doc_specs"
        doc_specs_dir.mkdir(exist_ok=True)
        doc_spec_content = """---
name: Report Specification
---
# Quality Criteria
- Must have a title
- Must have content
"""
        (doc_specs_dir / "report_spec.md").write_text(doc_spec_content)

        # Export the job (no need to sync first)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["export-job", "job_with_docspec", "--path", str(mock_installed_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Copying doc specs" in result.output
        assert "Copied report_spec.md" in result.output

        # Verify doc spec was copied
        global_doc_spec = clean_global_claude / ".deepwork" / "doc_specs" / "report_spec.md"
        assert global_doc_spec.exists()
        assert "Quality Criteria" in global_doc_spec.read_text()
