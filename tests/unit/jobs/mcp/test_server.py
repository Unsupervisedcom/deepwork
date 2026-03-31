"""Tests for MCP server creation and startup behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from deepwork.jobs.issues import Issue
from deepwork.jobs.mcp.server import (
    _STATIC_INSTRUCTIONS,
    _WORKFLOW_HEADER,
    _build_startup_instructions,
    _ensure_schema_available,
    create_server,
)


class TestEnsureSchemaAvailable:
    """Tests for JOBS-REQ-001.1.8: schema copy on startup."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_copies_schema_to_deepwork_dir(self, tmp_path: Path) -> None:
        """Schema file is copied to .deepwork/job.schema.json."""
        _ensure_schema_available(tmp_path)

        target = tmp_path / ".deepwork" / "job.schema.json"
        assert target.exists(), "Schema should be copied to .deepwork/job.schema.json"
        assert target.stat().st_size > 0, "Copied schema should not be empty"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.8).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_deepwork_dir_if_missing(self, tmp_path: Path) -> None:
        """The .deepwork/ directory is created if it does not exist."""
        project = tmp_path / "new_project"
        project.mkdir()

        _ensure_schema_available(project)

        assert (project / ".deepwork" / "job.schema.json").exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.8).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.1.8).
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


class TestCreateServerManifestFailure:
    """Test that create_server handles _write_manifest failure gracefully."""

    def test_manifest_write_failure_logged_not_raised(self, tmp_path: Path) -> None:
        """If _write_manifest raises, it is logged but server creation continues."""
        with patch(
            "deepwork.jobs.mcp.server.WorkflowTools._write_manifest",
            side_effect=RuntimeError("disk full"),
        ):
            # Should not raise — failure is caught and logged
            mcp = create_server(project_root=tmp_path)
            assert mcp is not None


class TestCreateServerWithIssues:
    """Test server creation when startup issues are detected."""

    def test_issue_warning_in_instructions(self, tmp_path: Path) -> None:
        """When startup issues exist, MCP instructions include issue warning."""
        issue = Issue(
            severity="error",
            job_name="broken_job",
            job_dir=str(tmp_path / "broken_job"),
            message="Schema validation failed",
            suggestion="Fix the job.yml file",
        )
        with patch("deepwork.jobs.mcp.server.detect_issues", return_value=[issue]):
            mcp = create_server(project_root=tmp_path)

        assert "ISSUE DETECTED" in mcp.instructions

    def test_no_issue_warning_when_no_issues(self, tmp_path: Path) -> None:
        """When no issues exist, instructions don't contain issue warning."""
        with patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]):
            mcp = create_server(project_root=tmp_path)

        assert "ISSUE DETECTED" not in mcp.instructions


class TestBuildStartupInstructions:
    """Tests for _build_startup_instructions."""

    def test_with_issues_returns_issue_warning(self) -> None:
        """Issues take priority and appear first in instructions."""
        issues = [
            Issue(
                severity="error",
                job_name="bad_job",
                job_dir="/some/path",
                message="parse error",
                suggestion="fix it",
            )
        ]
        result = _build_startup_instructions(Path("/fake"), issues)
        assert "ISSUE DETECTED" in result
        assert "bad_job" in result
        assert _STATIC_INSTRUCTIONS in result

    @patch("deepwork.jobs.mcp.server.load_all_jobs")
    def test_no_issues_no_jobs(self, mock_load: MagicMock) -> None:
        """When no issues and no jobs, return static instructions only."""
        mock_load.return_value = ([], [])
        result = _build_startup_instructions(Path("/fake"), [])
        assert result == _STATIC_INSTRUCTIONS

    @patch("deepwork.jobs.mcp.server.load_all_jobs")
    def test_no_issues_with_jobs(self, mock_load: MagicMock) -> None:
        """When no issues but jobs exist, instructions list workflows."""
        job = MagicMock()
        job.name = "research"
        job.summary = "Competitive research workflow"
        job.workflows = {"analyze": MagicMock(), "report": MagicMock()}

        mock_load.return_value = ([job], [])
        result = _build_startup_instructions(Path("/fake"), [])

        assert _WORKFLOW_HEADER in result
        assert "research" in result
        assert "analyze, report" in result
        assert _STATIC_INSTRUCTIONS in result

    @patch("deepwork.jobs.mcp.server.load_all_jobs")
    def test_instructions_truncated_when_too_long(self, mock_load: MagicMock) -> None:
        """When workflow list exceeds MAX_INSTRUCTIONS_SIZE, use fallback."""
        jobs = []
        for i in range(100):
            job = MagicMock()
            job.name = f"very_long_job_name_number_{i}_with_extra_padding"
            job.summary = "A" * 200
            job.workflows = {f"workflow_{j}": MagicMock() for j in range(5)}
            jobs.append(job)

        mock_load.return_value = (jobs, [])
        result = _build_startup_instructions(Path("/fake"), [])

        assert "Call `get_workflows`" in result
        assert _STATIC_INSTRUCTIONS in result


def _make_server_with_mocked_tools(
    tmp_path: Path,
    issues: list[Issue] | None = None,
) -> tuple[Any, MagicMock]:
    """Create a server with mocked WorkflowTools. Returns (mcp, mock_tools)."""
    mock_tools = MagicMock()
    mock_tools._write_manifest = MagicMock()

    with (
        patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
        patch("deepwork.jobs.mcp.server.detect_issues", return_value=issues or []),
    ):
        mcp = create_server(project_root=tmp_path)
    return mcp, mock_tools


class TestGetWorkflowsTool:
    """Test the get_workflows MCP tool."""

    async def test_get_workflows_returns_jobs(self, tmp_path: Path) -> None:
        """get_workflows returns job and workflow data."""
        from deepwork.jobs.mcp.schemas import GetWorkflowsResponse

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.get_workflows.return_value = GetWorkflowsResponse(jobs=[], errors=[])

        result = await mcp.call_tool("get_workflows", {})
        data = result.structured_content
        assert data["jobs"] == []
        assert data["errors"] == []

    async def test_get_workflows_appends_issues(self, tmp_path: Path) -> None:
        """When issues exist at startup, get_workflows response has issue_detected."""
        from deepwork.jobs.mcp.schemas import GetWorkflowsResponse

        issue = Issue(
            severity="error",
            job_name="broken",
            job_dir="/x",
            message="bad",
            suggestion="fix",
        )
        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path, issues=[issue])
        mock_tools.get_workflows.return_value = GetWorkflowsResponse(jobs=[], errors=[])

        result = await mcp.call_tool("get_workflows", {})
        data = result.structured_content
        assert "issue_detected" in data
        assert "broken" in data["issue_detected"]

    async def test_get_workflows_no_issues_no_issue_field(self, tmp_path: Path) -> None:
        """When no issues, get_workflows response has no issue_detected field."""
        from deepwork.jobs.mcp.schemas import GetWorkflowsResponse

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.get_workflows.return_value = GetWorkflowsResponse(jobs=[], errors=[])

        result = await mcp.call_tool("get_workflows", {})
        data = result.structured_content
        assert "issue_detected" not in data


class TestStartWorkflowTool:
    """Test the start_workflow MCP tool."""

    async def test_start_workflow_delegates_to_tools(self, tmp_path: Path) -> None:
        """start_workflow passes through to WorkflowTools.start_workflow."""
        from deepwork.jobs.mcp.schemas import ActiveStepInfo, StartWorkflowResponse

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.start_workflow = AsyncMock(
            return_value=StartWorkflowResponse(
                begin_step=ActiveStepInfo(
                    session_id="sess-1",
                    step_id="step1",
                    job_dir="/tmp/jobs/myjob",
                    step_instructions="Do the thing",
                    step_expected_outputs=[],
                ),
            )
        )

        result = await mcp.call_tool(
            "start_workflow",
            {
                "goal": "test",
                "job_name": "myjob",
                "workflow_name": "mywf",
                "session_id": "sess-1",
            },
        )
        data = result.structured_content
        assert data["begin_step"]["step_id"] == "step1"
        assert data["begin_step"]["step_instructions"] == "Do the thing"
        mock_tools.start_workflow.assert_called_once()

    async def test_start_workflow_with_inputs_and_agent_id(self, tmp_path: Path) -> None:
        """start_workflow correctly passes inputs and agent_id."""
        from deepwork.jobs.mcp.schemas import (
            ActiveStepInfo,
            StartWorkflowInput,
            StartWorkflowResponse,
        )

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.start_workflow = AsyncMock(
            return_value=StartWorkflowResponse(
                job_name="j",
                workflow_name="w",
                begin_step=ActiveStepInfo(
                    session_id="s",
                    step_id="s1",
                    job_dir="/tmp/jobs/j",
                    step_instructions="go",
                    step_expected_outputs=[],
                ),
            )
        )

        await mcp.call_tool(
            "start_workflow",
            {
                "goal": "g",
                "job_name": "j",
                "workflow_name": "w",
                "session_id": "s",
                "inputs": {"topic": "AI"},
                "agent_id": "agent-42",
            },
        )
        call_arg = mock_tools.start_workflow.call_args[0][0]
        assert isinstance(call_arg, StartWorkflowInput)
        assert call_arg.inputs == {"topic": "AI"}
        assert call_arg.agent_id == "agent-42"


class TestFinishedStepTool:
    """Test the finished_step MCP tool."""

    async def test_finished_step_workflow_complete(self, tmp_path: Path) -> None:
        """finished_step returns workflow_complete status."""
        from deepwork.jobs.mcp.schemas import FinishedStepResponse, StepStatus

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.finished_step = AsyncMock(
            return_value=FinishedStepResponse(status=StepStatus.WORKFLOW_COMPLETE)
        )

        result = await mcp.call_tool(
            "finished_step",
            {
                "outputs": {"report": "/tmp/report.md"},
                "session_id": "sess-1",
            },
        )
        data = result.structured_content
        assert data["status"] == "workflow_complete"

    async def test_finished_step_passes_optional_params(self, tmp_path: Path) -> None:
        """finished_step forwards work_summary and override_reason."""
        from deepwork.jobs.mcp.schemas import FinishedStepInput, FinishedStepResponse, StepStatus

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.finished_step = AsyncMock(
            return_value=FinishedStepResponse(status=StepStatus.NEXT_STEP)
        )

        await mcp.call_tool(
            "finished_step",
            {
                "outputs": {"out": "val"},
                "session_id": "s",
                "work_summary": "Did stuff",
                "quality_review_override_reason": "Tests pass",
                "agent_id": "a1",
            },
        )
        call_arg = mock_tools.finished_step.call_args[0][0]
        assert isinstance(call_arg, FinishedStepInput)
        assert call_arg.work_summary == "Did stuff"
        assert call_arg.quality_review_override_reason == "Tests pass"
        assert call_arg.agent_id == "a1"


class TestAbortWorkflowTool:
    """Test the abort_workflow MCP tool."""

    async def test_abort_workflow_delegates(self, tmp_path: Path) -> None:
        """abort_workflow passes through to WorkflowTools."""
        from deepwork.jobs.mcp.schemas import AbortWorkflowResponse

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.abort_workflow = AsyncMock(
            return_value=AbortWorkflowResponse(
                aborted_workflow="j/w",
                aborted_step="step1",
                explanation="cancelled",
            )
        )

        result = await mcp.call_tool(
            "abort_workflow",
            {
                "explanation": "cancelled",
                "session_id": "s",
                "agent_id": "a1",
            },
        )
        data = result.structured_content
        assert data["aborted_workflow"] == "j/w"
        mock_tools.abort_workflow.assert_called_once()


class TestGoToStepTool:
    """Test the go_to_step MCP tool."""

    async def test_go_to_step_delegates(self, tmp_path: Path) -> None:
        """go_to_step passes through to WorkflowTools."""
        from deepwork.jobs.mcp.schemas import ActiveStepInfo, GoToStepResponse

        mcp, mock_tools = _make_server_with_mocked_tools(tmp_path)
        mock_tools.go_to_step = AsyncMock(
            return_value=GoToStepResponse(
                begin_step=ActiveStepInfo(
                    session_id="s",
                    step_id="step1",
                    job_dir="/tmp/jobs/j",
                    step_instructions="Redo",
                    step_expected_outputs=[],
                ),
                invalidated_steps=["step1", "step2"],
            )
        )

        result = await mcp.call_tool(
            "go_to_step",
            {"step_id": "step1", "session_id": "s"},
        )
        data = result.structured_content
        assert data["invalidated_steps"] == ["step1", "step2"]


class TestGetNamedSchemasTool:
    """Test get_named_schemas MCP tool."""

    async def test_returns_discovered_schemas(self, tmp_path: Path) -> None:
        """get_named_schemas returns parsed schema info."""
        mock_schema = MagicMock()
        mock_schema.name = "job_definition"
        mock_schema.summary = "Schema for job.yml files"
        mock_schema.matchers = ["*.yml"]

        mock_manifest_path = MagicMock()
        mock_manifest_path.parent.name = "job_definition"

        mcp, _ = _make_server_with_mocked_tools(tmp_path)

        with (
            patch(
                "deepwork.deepschema.discovery.find_named_schemas",
                return_value=[mock_manifest_path],
            ),
            patch(
                "deepwork.deepschema.config.parse_deepschema_file",
                return_value=mock_schema,
            ),
        ):
            result = await mcp.call_tool("get_named_schemas", {})

        data = result.structured_content["result"]
        assert len(data) == 1
        assert data[0]["name"] == "job_definition"
        assert data[0]["summary"] == "Schema for job.yml files"

    async def test_handles_parse_error_gracefully(self, tmp_path: Path) -> None:
        """get_named_schemas handles DeepSchemaError without crashing."""
        from deepwork.deepschema.config import DeepSchemaError

        mock_manifest_path = MagicMock()
        mock_manifest_path.parent.name = "bad_schema"

        mcp, _ = _make_server_with_mocked_tools(tmp_path)

        with (
            patch(
                "deepwork.deepschema.discovery.find_named_schemas",
                return_value=[mock_manifest_path],
            ),
            patch(
                "deepwork.deepschema.config.parse_deepschema_file",
                side_effect=DeepSchemaError("bad yaml"),
            ),
        ):
            result = await mcp.call_tool("get_named_schemas", {})

        data = result.structured_content["result"]
        assert len(data) == 1
        assert data[0]["name"] == "bad_schema"
        assert "failed to parse" in data[0]["summary"]


class TestReviewTools:
    """Test review-related MCP tools.

    Review functions are imported inside create_server, so we patch them
    at the source (deepwork.review.mcp) BEFORE creating the server.
    """

    async def test_get_review_instructions_success(self, tmp_path: Path) -> None:
        """get_review_instructions returns review output on success."""
        mock_tools = MagicMock()
        mock_tools._write_manifest = MagicMock()

        with (
            patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
            patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]),
            patch("deepwork.review.mcp.run_review", return_value="Review task list"),
        ):
            mcp = create_server(project_root=tmp_path)
            result = await mcp.call_tool("get_review_instructions", {"files": ["src/foo.py"]})

        data = result.structured_content["result"]
        assert data == "Review task list"

    async def test_get_review_instructions_error(self, tmp_path: Path) -> None:
        """get_review_instructions catches ReviewToolError and returns error string."""
        from deepwork.review.mcp import ReviewToolError

        mock_tools = MagicMock()
        mock_tools._write_manifest = MagicMock()

        with (
            patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
            patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]),
            patch(
                "deepwork.review.mcp.run_review",
                side_effect=ReviewToolError("git not found"),
            ),
        ):
            mcp = create_server(project_root=tmp_path)
            result = await mcp.call_tool("get_review_instructions", {})

        data = result.structured_content["result"]
        assert "Review error" in data
        assert "git not found" in data

    async def test_get_configured_reviews(self, tmp_path: Path) -> None:
        """get_configured_reviews passes through to the underlying function."""
        mock_tools = MagicMock()
        mock_tools._write_manifest = MagicMock()

        with (
            patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
            patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]),
            patch(
                "deepwork.review.mcp.get_configured_reviews",
                return_value=[{"name": "rule1", "description": "Check tests"}],
            ),
        ):
            mcp = create_server(project_root=tmp_path)
            result = await mcp.call_tool(
                "get_configured_reviews",
                {"only_rules_matching_files": ["test.py"]},
            )

        data = result.structured_content["result"]
        assert len(data) == 1
        assert data[0]["name"] == "rule1"

    async def test_mark_review_as_passed_success(self, tmp_path: Path) -> None:
        """mark_review_as_passed returns success message."""
        mock_tools = MagicMock()
        mock_tools._write_manifest = MagicMock()

        with (
            patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
            patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]),
            patch(
                "deepwork.review.mcp.mark_passed",
                return_value="Marked review abc123 as passed",
            ),
        ):
            mcp = create_server(project_root=tmp_path)
            result = await mcp.call_tool("mark_review_as_passed", {"review_id": "abc123"})

        data = result.structured_content["result"]
        assert "abc123" in data

    async def test_mark_review_as_passed_validation_error(self, tmp_path: Path) -> None:
        """mark_review_as_passed catches ValueError and returns validation error."""
        mock_tools = MagicMock()
        mock_tools._write_manifest = MagicMock()

        with (
            patch("deepwork.jobs.mcp.server.WorkflowTools", return_value=mock_tools),
            patch("deepwork.jobs.mcp.server.detect_issues", return_value=[]),
            patch(
                "deepwork.review.mcp.mark_passed",
                side_effect=ValueError("Invalid review_id"),
            ),
        ):
            mcp = create_server(project_root=tmp_path)
            result = await mcp.call_tool("mark_review_as_passed", {"review_id": "bad"})

        data = result.structured_content["result"]
        assert "Validation error" in data
        assert "Invalid review_id" in data
