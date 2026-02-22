"""Tests for job folder discovery (deepwork.jobs.discovery)."""

from pathlib import Path

import pytest

from deepwork.jobs.discovery import (
    ENV_ADDITIONAL_JOBS_FOLDERS,
    find_job_dir,
    get_job_folders,
    load_all_jobs,
)


def _create_minimal_job(parent: Path, job_name: str) -> Path:
    """Create a minimal valid job directory for testing."""
    job_dir = parent / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    steps_dir = job_dir / "steps"
    steps_dir.mkdir(exist_ok=True)
    (steps_dir / "step1.md").write_text("# Step 1\n\nDo step 1.")
    (job_dir / "job.yml").write_text(
        f"""
name: {job_name}
version: "1.0.0"
summary: Test job {job_name}
common_job_info_provided_to_all_steps_at_runtime: A test job

steps:
  - id: step1
    name: Step 1
    description: First step
    instructions_file: steps/step1.md
    outputs: {{}}
    reviews: []

workflows:
  - name: main
    summary: Main workflow
    steps:
      - step1
"""
    )
    return job_dir


class TestGetJobFolders:
    """Tests for get_job_folders."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_folders_include_project_jobs(self, tmp_path: Path) -> None:
        folders = get_job_folders(tmp_path)
        assert tmp_path / ".deepwork" / "jobs" in folders

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.3, REQ-008.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_folders_include_standard_jobs(self, tmp_path: Path) -> None:
        from deepwork.jobs.discovery import _STANDARD_JOBS_DIR

        folders = get_job_folders(tmp_path)
        assert _STANDARD_JOBS_DIR in folders

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.5, REQ-008.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_env_var_appends_folders(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV_ADDITIONAL_JOBS_FOLDERS, "/extra/a:/extra/b")
        folders = get_job_folders(tmp_path)
        assert Path("/extra/a") in folders
        assert Path("/extra/b") in folders
        # Defaults should still be present
        assert tmp_path / ".deepwork" / "jobs" in folders

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_env_var_empty_is_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_ADDITIONAL_JOBS_FOLDERS, "")
        folders = get_job_folders(tmp_path)
        # Should only have the two defaults
        assert len(folders) == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_env_var_strips_whitespace(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_ADDITIONAL_JOBS_FOLDERS, " /extra/a : /extra/b ")
        folders = get_job_folders(tmp_path)
        assert Path("/extra/a") in folders
        assert Path("/extra/b") in folders


class TestLoadAllJobs:
    """Tests for load_all_jobs."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.2.1, REQ-008.2.4, REQ-008.2.7, REQ-008.2.8, REQ-008.2.11).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loads_from_project_jobs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        jobs_dir = tmp_path / ".deepwork" / "jobs"
        _create_minimal_job(jobs_dir, "my_job")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [pr / ".deepwork" / "jobs"],
        )
        jobs, errors = load_all_jobs(tmp_path)
        assert len(jobs) == 1
        assert jobs[0].name == "my_job"
        assert len(errors) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loads_from_multiple_folders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        folder_a = tmp_path / "folder_a"
        folder_b = tmp_path / "folder_b"
        _create_minimal_job(folder_a, "job_a")
        _create_minimal_job(folder_b, "job_b")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder_a, folder_b],
        )
        jobs, errors = load_all_jobs(tmp_path)
        names = {j.name for j in jobs}
        assert names == {"job_a", "job_b"}
        assert len(errors) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.2.5, REQ-008.2.6, REQ-008.4.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_first_folder_wins_for_duplicate_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        folder_a = tmp_path / "folder_a"
        folder_b = tmp_path / "folder_b"
        _create_minimal_job(folder_a, "same_name")
        _create_minimal_job(folder_b, "same_name")
        # Patch folder_b's job to have a different summary so we can distinguish
        (folder_b / "same_name" / "job.yml").write_text(
            (folder_b / "same_name" / "job.yml")
            .read_text()
            .replace("Test job same_name", "SHOULD NOT APPEAR")
        )
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder_a, folder_b],
        )
        jobs, errors = load_all_jobs(tmp_path)
        assert len(jobs) == 1
        assert jobs[0].summary == "Test job same_name"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_nonexistent_folders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [tmp_path / "does_not_exist"],
        )
        jobs, errors = load_all_jobs(tmp_path)
        assert len(jobs) == 0
        assert len(errors) == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.2.9, REQ-008.2.11, REQ-008.5.1, REQ-008.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_invalid_jobs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        folder = tmp_path / "jobs"
        bad_job = folder / "bad_job"
        bad_job.mkdir(parents=True)
        (bad_job / "job.yml").write_text("invalid: [yaml")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder],
        )
        jobs, errors = load_all_jobs(tmp_path)
        assert len(jobs) == 0
        assert len(errors) == 1
        assert errors[0].job_name == "bad_job"
        assert errors[0].job_dir == str(bad_job)
        assert errors[0].error  # non-empty error message


class TestFindJobDir:
    """Tests for find_job_dir."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.1, REQ-008.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_finds_in_first_folder(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        folder = tmp_path / "jobs"
        _create_minimal_job(folder, "target")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder],
        )
        result = find_job_dir(tmp_path, "target")
        assert result == folder / "target"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.1, REQ-008.3.2, REQ-008.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_finds_in_second_folder(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        folder_a = tmp_path / "a"
        folder_b = tmp_path / "b"
        folder_a.mkdir()
        _create_minimal_job(folder_b, "target")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder_a, folder_b],
        )
        result = find_job_dir(tmp_path, "target")
        assert result == folder_b / "target"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_none_when_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [tmp_path],
        )
        result = find_job_dir(tmp_path, "nonexistent")
        assert result is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.1, REQ-008.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_prefers_first_folder_on_duplicate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        folder_a = tmp_path / "a"
        folder_b = tmp_path / "b"
        _create_minimal_job(folder_a, "dup")
        _create_minimal_job(folder_b, "dup")
        monkeypatch.setattr(
            "deepwork.jobs.discovery.get_job_folders",
            lambda pr: [folder_a, folder_b],
        )
        result = find_job_dir(tmp_path, "dup")
        assert result == folder_a / "dup"
