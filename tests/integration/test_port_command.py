"""Integration tests for the port command."""

import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from deepwork.cli.port import port
from deepwork.utils.paths import get_global_jobs_dir, get_local_jobs_dir


@pytest.fixture
def temp_project(monkeypatch):
    """Create a temporary project with DeepWork structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "project"
        project_path.mkdir()
        
        # Create .deepwork/jobs directory
        local_jobs = get_local_jobs_dir(project_path)
        local_jobs.mkdir(parents=True)
        
        # Set up fake home for global jobs
        fake_home = Path(tmpdir) / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        yield project_path


def create_test_job(jobs_dir: Path, job_name: str) -> Path:
    """Create a test job in the specified jobs directory."""
    job_dir = jobs_dir / job_name
    job_dir.mkdir()
    
    # Create job.yml
    (job_dir / "job.yml").write_text(
        f"""name: {job_name}
version: 1.0.0
summary: Test job
steps:
  - id: test_step
    name: Test Step
    description: A test step
    instructions_file: steps/test_step.md
    outputs:
      - output.txt
"""
    )
    
    # Create steps directory and file
    steps_dir = job_dir / "steps"
    steps_dir.mkdir()
    (steps_dir / "test_step.md").write_text("# Test Step\n\nThis is a test step.")
    
    return job_dir


def test_port_local_to_global(temp_project):
    """Test porting a job from local to global."""
    runner = CliRunner()
    
    # Create a local job
    local_jobs = get_local_jobs_dir(temp_project)
    create_test_job(local_jobs, "test_job")
    
    # Port to global
    result = runner.invoke(port, ["test_job", "--to", "global", "--path", str(temp_project)])
    
    assert result.exit_code == 0
    assert "ported to global" in result.output.lower()
    
    # Verify job exists in global location
    global_jobs = get_global_jobs_dir()
    global_job = global_jobs / "test_job"
    assert global_job.exists()
    assert (global_job / "job.yml").exists()
    assert (global_job / "steps" / "test_step.md").exists()
    
    # Verify job removed from local location
    local_job = local_jobs / "test_job"
    assert not local_job.exists()


def test_port_global_to_local(temp_project):
    """Test porting a job from global to local."""
    runner = CliRunner()
    
    # Create a global job
    global_jobs = get_global_jobs_dir()
    global_jobs.mkdir(parents=True, exist_ok=True)
    create_test_job(global_jobs, "global_job")
    
    # Port to local
    result = runner.invoke(port, ["global_job", "--to", "local", "--path", str(temp_project)])
    
    assert result.exit_code == 0
    assert "ported to local" in result.output.lower()
    
    # Verify job exists in local location
    local_jobs = get_local_jobs_dir(temp_project)
    local_job = local_jobs / "global_job"
    assert local_job.exists()
    assert (local_job / "job.yml").exists()
    assert (local_job / "steps" / "test_step.md").exists()
    
    # Verify job removed from global location
    global_job = global_jobs / "global_job"
    assert not global_job.exists()


def test_port_job_not_found(temp_project):
    """Test porting a non-existent job."""
    runner = CliRunner()
    
    result = runner.invoke(port, ["nonexistent_job", "--to", "global", "--path", str(temp_project)])
    
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_port_already_at_destination(temp_project):
    """Test porting a job that's already at the destination."""
    runner = CliRunner()
    
    # Create a local job
    local_jobs = get_local_jobs_dir(temp_project)
    create_test_job(local_jobs, "local_job")
    
    # Try to port to local (where it already is)
    result = runner.invoke(port, ["local_job", "--to", "local", "--path", str(temp_project)])
    
    assert result.exit_code == 0
    assert "already in local" in result.output.lower()


def test_port_destination_exists(temp_project):
    """Test porting when destination already has a job with the same name."""
    runner = CliRunner()
    
    # Create a local job
    local_jobs = get_local_jobs_dir(temp_project)
    create_test_job(local_jobs, "duplicate_job")
    
    # Create a global job with the same name
    global_jobs = get_global_jobs_dir()
    global_jobs.mkdir(parents=True, exist_ok=True)
    create_test_job(global_jobs, "duplicate_job")
    
    # Try to port local to global
    result = runner.invoke(port, ["duplicate_job", "--to", "global", "--path", str(temp_project)])
    
    assert result.exit_code != 0
    assert "already exists at destination" in result.output.lower()


def test_port_preserves_job_structure(temp_project):
    """Test that porting preserves the complete job structure."""
    runner = CliRunner()
    
    # Create a job with multiple files
    local_jobs = get_local_jobs_dir(temp_project)
    job_dir = create_test_job(local_jobs, "complex_job")
    
    # Add additional files
    (job_dir / "hooks").mkdir()
    (job_dir / "hooks" / "validate.sh").write_text("#!/bin/bash\necho 'validate'")
    (job_dir / "templates").mkdir()
    (job_dir / "templates" / "template.md").write_text("# Template")
    (job_dir / "AGENTS.md").write_text("# Agents\nGuidance here")
    
    # Port to global
    result = runner.invoke(port, ["complex_job", "--to", "global", "--path", str(temp_project)])
    
    assert result.exit_code == 0
    
    # Verify all files were copied
    global_jobs = get_global_jobs_dir()
    global_job = global_jobs / "complex_job"
    assert (global_job / "job.yml").exists()
    assert (global_job / "steps" / "test_step.md").exists()
    assert (global_job / "hooks" / "validate.sh").exists()
    assert (global_job / "templates" / "template.md").exists()
    assert (global_job / "AGENTS.md").exists()
