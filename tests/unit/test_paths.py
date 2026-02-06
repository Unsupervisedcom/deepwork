"""Unit tests for paths utility module."""

import tempfile
from pathlib import Path

import pytest

from deepwork.utils.paths import (
    discover_all_jobs_dirs,
    ensure_global_jobs_dir,
    get_global_deepwork_dir,
    get_global_jobs_dir,
    get_local_deepwork_dir,
    get_local_jobs_dir,
    is_job_global,
)


def test_get_global_deepwork_dir():
    """Test getting the global DeepWork directory path."""
    global_dir = get_global_deepwork_dir()
    assert global_dir == Path.home() / ".deepwork"


def test_get_global_jobs_dir():
    """Test getting the global jobs directory path."""
    global_jobs = get_global_jobs_dir()
    assert global_jobs == Path.home() / ".deepwork" / "jobs"


def test_get_local_deepwork_dir():
    """Test getting the local DeepWork directory path."""
    project_path = Path("/tmp/test_project")
    local_dir = get_local_deepwork_dir(project_path)
    assert local_dir == project_path / ".deepwork"


def test_get_local_jobs_dir():
    """Test getting the local jobs directory path."""
    project_path = Path("/tmp/test_project")
    local_jobs = get_local_jobs_dir(project_path)
    assert local_jobs == project_path / ".deepwork" / "jobs"


def test_discover_all_jobs_dirs_empty():
    """Test discovering jobs when no jobs exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        job_dirs = discover_all_jobs_dirs(project_path)
        assert job_dirs == []


def test_discover_all_jobs_dirs_local_only():
    """Test discovering local jobs only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        local_jobs = get_local_jobs_dir(project_path)
        local_jobs.mkdir(parents=True)
        
        # Create a test job
        test_job = local_jobs / "test_job"
        test_job.mkdir()
        (test_job / "job.yml").write_text("name: test_job\nversion: 1.0.0")
        
        job_dirs = discover_all_jobs_dirs(project_path)
        assert len(job_dirs) == 1
        assert job_dirs[0][0] == test_job
        assert job_dirs[0][1] == "local"


def test_discover_all_jobs_dirs_global_only(monkeypatch):
    """Test discovering global jobs only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        fake_home = Path(tmpdir) / "fake_home"
        fake_home.mkdir()
        
        # Monkeypatch Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        global_jobs = get_global_jobs_dir()
        global_jobs.mkdir(parents=True)
        
        # Create a test job
        test_job = global_jobs / "global_test_job"
        test_job.mkdir()
        (test_job / "job.yml").write_text("name: global_test_job\nversion: 1.0.0")
        
        job_dirs = discover_all_jobs_dirs(project_path)
        assert len(job_dirs) == 1
        assert job_dirs[0][0] == test_job
        assert job_dirs[0][1] == "global"


def test_discover_all_jobs_dirs_both(monkeypatch):
    """Test discovering both local and global jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        fake_home = Path(tmpdir) / "fake_home"
        fake_home.mkdir()
        
        # Monkeypatch Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        # Create local job
        local_jobs = get_local_jobs_dir(project_path)
        local_jobs.mkdir(parents=True)
        local_job = local_jobs / "local_job"
        local_job.mkdir()
        (local_job / "job.yml").write_text("name: local_job\nversion: 1.0.0")
        
        # Create global job
        global_jobs = get_global_jobs_dir()
        global_jobs.mkdir(parents=True)
        global_job = global_jobs / "global_job"
        global_job.mkdir()
        (global_job / "job.yml").write_text("name: global_job\nversion: 1.0.0")
        
        job_dirs = discover_all_jobs_dirs(project_path)
        assert len(job_dirs) == 2
        
        # Check that we have one local and one global
        locations = [loc for _, loc in job_dirs]
        assert "local" in locations
        assert "global" in locations


def test_discover_all_jobs_dirs_ignores_non_jobs():
    """Test that discovery ignores directories without job.yml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        local_jobs = get_local_jobs_dir(project_path)
        local_jobs.mkdir(parents=True)
        
        # Create a directory without job.yml
        (local_jobs / "not_a_job").mkdir()
        
        # Create a valid job
        valid_job = local_jobs / "valid_job"
        valid_job.mkdir()
        (valid_job / "job.yml").write_text("name: valid_job\nversion: 1.0.0")
        
        job_dirs = discover_all_jobs_dirs(project_path)
        assert len(job_dirs) == 1
        assert job_dirs[0][0].name == "valid_job"


def test_is_job_global(monkeypatch):
    """Test checking if a job is global."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "fake_home"
        fake_home.mkdir()
        
        # Monkeypatch Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        # Create paths
        global_jobs = get_global_jobs_dir()
        global_jobs.mkdir(parents=True)
        global_job = global_jobs / "global_job"
        global_job.mkdir()
        
        local_job = Path(tmpdir) / ".deepwork" / "jobs" / "local_job"
        local_job.mkdir(parents=True)
        
        # Test global job
        assert is_job_global(global_job) is True
        
        # Test local job
        assert is_job_global(local_job) is False


def test_ensure_global_jobs_dir(monkeypatch):
    """Test ensuring the global jobs directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "fake_home"
        fake_home.mkdir()
        
        # Monkeypatch Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        global_jobs = get_global_jobs_dir()
        assert not global_jobs.exists()
        
        # Ensure it's created
        result = ensure_global_jobs_dir()
        assert result == global_jobs
        assert global_jobs.exists()
        assert global_jobs.is_dir()
        
        # Calling again should be idempotent
        result2 = ensure_global_jobs_dir()
        assert result2 == global_jobs
        assert global_jobs.exists()
