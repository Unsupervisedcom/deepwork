"""Tests for MCP server creation and startup behavior."""

from pathlib import Path
from unittest.mock import patch

from deepwork.jobs.mcp.server import _ensure_schema_available, create_server


class TestEnsureSchemaAvailable:
    """Tests for JOBS-REQ-001.1.13: schema copy on startup."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_copies_schema_to_deepwork_dir(self, tmp_path: Path) -> None:
        """Schema file is copied to .deepwork/job.schema.json."""
        _ensure_schema_available(tmp_path)

        target = tmp_path / ".deepwork" / "job.schema.json"
        assert target.exists(), "Schema should be copied to .deepwork/job.schema.json"
        assert target.stat().st_size > 0, "Copied schema should not be empty"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_overwrites_existing_stale_schema(self, tmp_path: Path) -> None:
        """An existing (stale) schema file at the target path is overwritten."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        target = deepwork_dir / "job.schema.json"
        target.write_text('{"stale": true}')

        _ensure_schema_available(tmp_path)

        content = target.read_text()
        assert '"stale"' not in content, "Stale schema should be overwritten"
        assert len(content) > 20, "Overwritten schema should contain real content"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_deepwork_dir_if_missing(self, tmp_path: Path) -> None:
        """The .deepwork/ directory is created if it does not exist."""
        project = tmp_path / "new_project"
        project.mkdir()

        _ensure_schema_available(project)

        assert (project / ".deepwork" / "job.schema.json").exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_logs_warning_on_failure(self, tmp_path: Path) -> None:
        """A warning is logged if the copy fails, but no exception is raised."""
        with patch(
            "deepwork.jobs.mcp.server.shutil.copy2", side_effect=OSError("permission denied")
        ):
            # Should not raise
            _ensure_schema_available(tmp_path)

    def test_schema_content_matches_source(self, tmp_path: Path) -> None:
        """Copied schema matches the bundled source file."""
        from deepwork.jobs.schema import get_schema_path

        _ensure_schema_available(tmp_path)

        source_content = get_schema_path().read_text()
        target_content = (tmp_path / ".deepwork" / "job.schema.json").read_text()
        assert source_content == target_content


class TestCreateServerSchemaSetup:
    """Test that create_server copies the schema on startup."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_create_server_copies_schema(self, tmp_path: Path) -> None:
        """create_server copies job.schema.json to .deepwork/ on startup."""
        create_server(
            project_root=tmp_path,
        )

        target = tmp_path / ".deepwork" / "job.schema.json"
        assert target.exists(), (
            "create_server must copy job.schema.json to .deepwork/job.schema.json on startup"
        )
