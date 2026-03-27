"""Tests for MCP status file writer."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from deepwork.jobs.mcp.state import StateManager
from deepwork.jobs.mcp.status import StatusWriter, _derive_display_name
from deepwork.jobs.parser import JobDefinition, Workflow, WorkflowStepEntry

SESSION_ID = "test-session-001"
AGENT_ID = "agent-abc"


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir()
    (deepwork_dir / "tmp").mkdir()
    return tmp_path


@pytest.fixture
def status_writer(project_root: Path) -> StatusWriter:
    return StatusWriter(project_root)


@pytest.fixture
def state_manager(project_root: Path) -> StateManager:
    return StateManager(project_root=project_root, platform="test")


def _make_job(
    name: str = "test_job",
    summary: str = "A test job",
    workflows: list[Workflow] | None = None,
) -> JobDefinition:
    """Create a minimal JobDefinition for testing."""
    if workflows is None:
        workflows = [
            Workflow(
                name="main",
                summary="Main workflow",
                step_entries=[
                    WorkflowStepEntry(step_ids=["step1"]),
                    WorkflowStepEntry(step_ids=["step2"]),
                ],
            )
        ]
    return JobDefinition(
        name=name,
        version="1.0.0",
        summary=summary,
        common_job_info_provided_to_all_steps_at_runtime="",
        steps=[],
        job_dir=Path("/tmp/fake"),
        workflows=workflows,
    )


class TestDeriveDisplayName:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.1, JOBS-REQ-010.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_underscore(self) -> None:
        assert _derive_display_name("competitive_research") == "Competitive Research"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_hyphen(self) -> None:
        assert _derive_display_name("ad-campaign") == "Ad Campaign"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_mixed(self) -> None:
        assert _derive_display_name("my_job-name") == "My Job Name"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_single_word(self) -> None:
        assert _derive_display_name("report") == "Report"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_already_title(self) -> None:
        assert _derive_display_name("Report") == "Report"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_empty(self) -> None:
        assert _derive_display_name("") == ""


class TestStatusDirectoryStructure:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.1.1, JOBS-REQ-010.1.4, JOBS-REQ-010.13.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_status_dir_uses_v1_path(self, status_writer: StatusWriter, project_root: Path) -> None:
        """Status directory uses versioned v1 path."""
        assert status_writer.status_dir == project_root / ".deepwork" / "tmp" / "status" / "v1"
        assert status_writer.manifest_path == status_writer.status_dir / "job_manifest.yml"
        assert status_writer.sessions_dir == status_writer.status_dir / "sessions"


class TestWriteManifest:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_manifest_file(self, status_writer: StatusWriter) -> None:
        jobs = [_make_job()]
        status_writer.write_manifest(jobs)
        assert status_writer.manifest_path.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.2.1, JOBS-REQ-010.2.2, JOBS-REQ-010.2.3, JOBS-REQ-010.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_structure(self, status_writer: StatusWriter) -> None:
        jobs = [_make_job()]
        status_writer.write_manifest(jobs)

        data = yaml.safe_load(status_writer.manifest_path.read_text())
        assert "jobs" in data
        assert len(data["jobs"]) == 1

        job = data["jobs"][0]
        assert job["name"] == "test_job"
        assert job["display_name"] == "Test Job"
        assert job["summary"] == "A test job"
        assert len(job["workflows"]) == 1

        wf = job["workflows"][0]
        assert wf["name"] == "main"
        assert wf["display_name"] == "Main"
        assert wf["summary"] == "Main workflow"
        assert len(wf["steps"]) == 2
        assert wf["steps"][0]["name"] == "step1"
        assert wf["steps"][0]["display_name"] == "Step1"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.2.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_sorted_by_name(self, status_writer: StatusWriter) -> None:
        jobs = [
            _make_job(name="zebra_job", summary="Z job"),
            _make_job(name="alpha_job", summary="A job"),
        ]
        status_writer.write_manifest(jobs)

        data = yaml.safe_load(status_writer.manifest_path.read_text())
        assert data["jobs"][0]["name"] == "alpha_job"
        assert data["jobs"][1]["name"] == "zebra_job"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_multiple_workflows_sorted(self, status_writer: StatusWriter) -> None:
        wf_b = Workflow(
            name="beta_wf",
            summary="Beta",
            step_entries=[WorkflowStepEntry(step_ids=["s1"])],
        )
        wf_a = Workflow(
            name="alpha_wf",
            summary="Alpha",
            step_entries=[WorkflowStepEntry(step_ids=["s2"])],
        )
        jobs = [_make_job(workflows=[wf_b, wf_a])]
        status_writer.write_manifest(jobs)

        data = yaml.safe_load(status_writer.manifest_path.read_text())
        wf_names = [w["name"] for w in data["jobs"][0]["workflows"]]
        assert wf_names == ["alpha_wf", "beta_wf"]

    def test_empty_jobs_list(self, status_writer: StatusWriter) -> None:
        status_writer.write_manifest([])
        data = yaml.safe_load(status_writer.manifest_path.read_text())
        assert data["jobs"] == []


class TestWriteSessionStatus:
    def _job_loader(
        self, jobs: list[JobDefinition] | None = None
    ) -> Callable[[], tuple[list[JobDefinition], list[str]]]:
        """Return a callable that returns the provided jobs."""
        if jobs is None:
            jobs = [_make_job()]

        def loader() -> tuple[list[JobDefinition], list[str]]:
            return jobs, []

        return loader

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.1.3, JOBS-REQ-010.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_writes_session_file(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        session_file = status_writer.sessions_dir / f"{SESSION_ID}.yml"
        assert session_file.exists()

        data = yaml.safe_load(session_file.read_text())
        assert data["session_id"] == SESSION_ID
        assert data["active_workflow"] is not None
        assert len(data["workflows"]) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.1, JOBS-REQ-010.5.2, JOBS-REQ-010.5.4, JOBS-REQ-010.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_session_status_structure(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        session = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())

        wf = data["workflows"][0]
        assert wf["workflow_instance_id"] == session.workflow_instance_id
        assert wf["job_name"] == "test_job"
        assert wf["status"] == "active"
        assert wf["agent_id"] is None
        assert wf["workflow"]["name"] == "main"
        assert wf["workflow"]["display_name"] == "Main"
        assert len(wf["steps"]) == 1
        assert wf["steps"][0]["step_name"] == "step1"
        assert wf["steps"][0]["started_at"] is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.2, JOBS-REQ-010.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_completed_workflow_preserved(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.complete_step(SESSION_ID, "step1", {"out": "out.md"})
        await state_manager.complete_workflow(SESSION_ID)

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        assert data["active_workflow"] is None
        assert len(data["workflows"]) == 1
        assert data["workflows"][0]["status"] == "completed"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_aborted_workflow_preserved(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.abort_workflow(SESSION_ID, "Cancelled")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        assert data["workflows"][0]["status"] == "aborted"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.2, JOBS-REQ-010.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_nested_workflows(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Goal 1",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Goal 2",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        assert len(data["workflows"]) == 2
        # Active workflow should be the top of stack (last one pushed)
        assert data["active_workflow"] == data["workflows"][1]["workflow_instance_id"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.4, JOBS-REQ-010.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_multi_agent_workflows(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Main goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Agent goal",
            first_step_id="step1",
            agent_id=AGENT_ID,
        )
        await state_manager.start_step(SESSION_ID, "step1", agent_id=AGENT_ID)

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        assert len(data["workflows"]) == 2
        agent_ids = [w["agent_id"] for w in data["workflows"]]
        assert None in agent_ids
        assert AGENT_ID in agent_ids

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.8.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_step_history_ordering(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        """Step history shows duplicates when go_to_step is used."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")
        await state_manager.complete_step(SESSION_ID, "step1", {"out": "out.md"})

        # Go back to step1
        await state_manager.go_to_step(
            session_id=SESSION_ID,
            step_id="step1",
            entry_index=0,
            invalidate_step_ids=["step1"],
        )
        await state_manager.start_step(SESSION_ID, "step1")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        steps = data["workflows"][0]["steps"]
        # step1 appears twice in history (original + re-execution)
        step_names = [s["step_name"] for s in steps]
        assert step_names == ["step1", "step1"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_last_updated_at_is_iso8601_utc(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        """last_updated_at must be an ISO 8601 timestamp in UTC."""
        from datetime import datetime, timedelta

        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Test goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        status_writer.write_session_status(SESSION_ID, state_manager, self._job_loader())

        data = yaml.safe_load((status_writer.sessions_dir / f"{SESSION_ID}.yml").read_text())
        ts = data["last_updated_at"]
        # Must parse as ISO 8601
        parsed = datetime.fromisoformat(ts)
        # Must be UTC (offset +00:00)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timedelta(0)

    def test_no_session_data_is_noop(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
    ) -> None:
        """write_session_status with non-existent session is a no-op."""
        status_writer.write_session_status("nonexistent", state_manager, self._job_loader())
        assert not status_writer.sessions_dir.exists() or not list(
            status_writer.sessions_dir.iterdir()
        )


class TestSubWorkflowInstanceTracking:
    """Tests for sub_workflow_instance_ids in status output."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-010.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_nested_workflow_records_sub_instance_id(
        self,
        status_writer: StatusWriter,
        state_manager: StateManager,
        project_root: Path,
    ) -> None:
        """When a nested workflow starts, its instance ID is recorded on the parent step."""
        await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Parent goal",
            first_step_id="step1",
        )
        await state_manager.start_step(SESSION_ID, "step1")

        child = await state_manager.create_session(
            session_id=SESSION_ID,
            job_name="test_job",
            workflow_name="main",
            goal="Child goal",
            first_step_id="step1",
        )

        # Read parent from disk to verify sub_workflow_instance_ids was set
        state_file = state_manager._state_file(SESSION_ID)
        data = json.loads(state_file.read_text())
        parent_data = data["workflow_stack"][0]
        parent_step_progress = parent_data["step_progress"]["step1"]
        assert child.workflow_instance_id in parent_step_progress["sub_workflow_instance_ids"]
