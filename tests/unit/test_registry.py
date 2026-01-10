"""Tests for job registry."""

from pathlib import Path

import pytest

from deepwork.core.registry import JobRegistry, JobRegistryEntry, RegistryError


class TestJobRegistryEntry:
    """Tests for JobRegistryEntry dataclass."""

    def test_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = JobRegistryEntry(
            name="test_job",
            version="1.0.0",
            description="Test job",
            job_dir="jobs/test_job",
            installed_at="2026-01-09T10:00:00",
        )

        result = entry.to_dict()

        assert result["name"] == "test_job"
        assert result["version"] == "1.0.0"
        assert result["description"] == "Test job"
        assert result["job_dir"] == "jobs/test_job"
        assert result["installed_at"] == "2026-01-09T10:00:00"

    def test_from_dict(self) -> None:
        """Test creating entry from dictionary."""
        data = {
            "name": "test_job",
            "version": "1.0.0",
            "description": "Test job",
            "job_dir": "jobs/test_job",
            "installed_at": "2026-01-09T10:00:00",
        }

        entry = JobRegistryEntry.from_dict(data)

        assert entry.name == "test_job"
        assert entry.version == "1.0.0"
        assert entry.description == "Test job"
        assert entry.job_dir == "jobs/test_job"
        assert entry.installed_at == "2026-01-09T10:00:00"


class TestJobRegistry:
    """Tests for JobRegistry class."""

    def test_register_job(self, temp_dir: Path) -> None:
        """Test registering a new job."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        entry = registry.register_job(
            name="test_job",
            version="1.0.0",
            description="A test job",
            job_dir="jobs/test_job",
        )

        assert entry.name == "test_job"
        assert entry.version == "1.0.0"
        assert entry.description == "A test job"
        assert entry.job_dir == "jobs/test_job"
        assert entry.installed_at is not None

    def test_register_creates_deepwork_dir(self, temp_dir: Path) -> None:
        """Test that register_job creates .deepwork directory."""
        deepwork_dir = temp_dir / ".deepwork"
        assert not deepwork_dir.exists()

        registry = JobRegistry(deepwork_dir)
        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        assert deepwork_dir.exists()
        assert (deepwork_dir / "registry.yml").exists()

    def test_register_raises_for_duplicate(self, temp_dir: Path) -> None:
        """Test that registering duplicate job raises error."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        with pytest.raises(RegistryError, match="already registered"):
            registry.register_job("test_job", "2.0.0", "Test again", "jobs/test_job")

    def test_unregister_job(self, temp_dir: Path) -> None:
        """Test unregistering a job."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")
        assert registry.is_registered("test_job")

        registry.unregister_job("test_job")

        assert not registry.is_registered("test_job")

    def test_unregister_raises_for_nonexistent(self, temp_dir: Path) -> None:
        """Test that unregistering nonexistent job raises error."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        with pytest.raises(RegistryError, match="not registered"):
            registry.unregister_job("nonexistent")

    def test_get_job(self, temp_dir: Path) -> None:
        """Test getting a registered job."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        entry = registry.get_job("test_job")

        assert entry is not None
        assert entry.name == "test_job"
        assert entry.version == "1.0.0"

    def test_get_job_returns_none_for_nonexistent(self, temp_dir: Path) -> None:
        """Test that get_job returns None for nonexistent job."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        entry = registry.get_job("nonexistent")

        assert entry is None

    def test_list_jobs_empty(self, temp_dir: Path) -> None:
        """Test listing jobs when registry is empty."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        jobs = registry.list_jobs()

        assert jobs == []

    def test_list_jobs_multiple(self, temp_dir: Path) -> None:
        """Test listing multiple registered jobs."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("job_c", "1.0.0", "Job C", "jobs/job_c")
        registry.register_job("job_a", "1.0.0", "Job A", "jobs/job_a")
        registry.register_job("job_b", "1.0.0", "Job B", "jobs/job_b")

        jobs = registry.list_jobs()

        assert len(jobs) == 3
        # Should be sorted by name
        assert jobs[0].name == "job_a"
        assert jobs[1].name == "job_b"
        assert jobs[2].name == "job_c"

    def test_is_registered(self, temp_dir: Path) -> None:
        """Test checking if job is registered."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        assert not registry.is_registered("test_job")

        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        assert registry.is_registered("test_job")

    def test_update_job_version(self, temp_dir: Path) -> None:
        """Test updating job version."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        updated = registry.update_job("test_job", version="2.0.0")

        assert updated.version == "2.0.0"
        assert registry.get_job("test_job").version == "2.0.0"  # type: ignore

    def test_update_job_description(self, temp_dir: Path) -> None:
        """Test updating job description."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Old description", "jobs/test_job")

        updated = registry.update_job("test_job", description="New description")

        assert updated.description == "New description"
        assert registry.get_job("test_job").description == "New description"  # type: ignore

    def test_update_job_both(self, temp_dir: Path) -> None:
        """Test updating both version and description."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        registry.register_job("test_job", "1.0.0", "Old", "jobs/test_job")

        updated = registry.update_job(
            "test_job", version="2.0.0", description="New description"
        )

        assert updated.version == "2.0.0"
        assert updated.description == "New description"

    def test_update_job_raises_for_nonexistent(self, temp_dir: Path) -> None:
        """Test that updating nonexistent job raises error."""
        deepwork_dir = temp_dir / ".deepwork"
        registry = JobRegistry(deepwork_dir)

        with pytest.raises(RegistryError, match="not registered"):
            registry.update_job("nonexistent", version="2.0.0")

    def test_persistence_across_instances(self, temp_dir: Path) -> None:
        """Test that registry persists across instances."""
        deepwork_dir = temp_dir / ".deepwork"

        # First instance
        registry1 = JobRegistry(deepwork_dir)
        registry1.register_job("test_job", "1.0.0", "Test", "jobs/test_job")

        # Second instance
        registry2 = JobRegistry(deepwork_dir)
        jobs = registry2.list_jobs()

        assert len(jobs) == 1
        assert jobs[0].name == "test_job"

    def test_handles_empty_registry_file(self, temp_dir: Path) -> None:
        """Test that registry handles empty registry file."""
        deepwork_dir = temp_dir / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "registry.yml").write_text("")

        registry = JobRegistry(deepwork_dir)
        jobs = registry.list_jobs()

        assert jobs == []

    def test_handles_missing_jobs_key(self, temp_dir: Path) -> None:
        """Test that registry handles missing 'jobs' key in file."""
        deepwork_dir = temp_dir / ".deepwork"
        deepwork_dir.mkdir()
        (deepwork_dir / "registry.yml").write_text("other_key: value\n")

        registry = JobRegistry(deepwork_dir)
        jobs = registry.list_jobs()

        assert jobs == []
