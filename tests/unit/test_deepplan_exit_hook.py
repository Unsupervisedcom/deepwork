"""Tests for the deepplan_exit PreToolUse hook."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepwork.hooks.deepplan_exit import _read_deepplan_state, deepplan_exit_hook
from deepwork.hooks.wrapper import HookInput, NormalizedEvent, Platform


def _make_hook_input(
    *,
    event: NormalizedEvent = NormalizedEvent.BEFORE_TOOL,
    tool_name: str = "exit_plan_mode",
    session_id: str = "test-session",
    cwd: str = "",
) -> HookInput:
    return HookInput(
        platform=Platform.CLAUDE,
        event=event,
        session_id=session_id,
        tool_name=tool_name,
        cwd=cwd,
    )


def _write_state(session_dir: Path, filename: str, data: dict) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / filename).write_text(json.dumps(data), encoding="utf-8")


class TestGuardConditions:
    """Hook should return empty HookOutput (allow) for non-matching events."""

    def test_wrong_event_type(self) -> None:
        hook_input = _make_hook_input(event=NormalizedEvent.AFTER_TOOL)
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""

    def test_wrong_tool_name(self) -> None:
        hook_input = _make_hook_input(tool_name="write_file")
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""

    def test_missing_session_id(self) -> None:
        hook_input = _make_hook_input(session_id="")
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""


class TestBlockCases:
    """Hook should block when deepplan workflow is not at present_plan."""

    def test_no_session_directory(self, tmp_path: Path) -> None:
        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == "block"
        assert "start_workflow" in result.reason

    def test_active_deepplan_not_at_present_plan(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        _write_state(
            session_dir,
            "state.json",
            {
                "workflow_stack": [
                    {
                        "job_name": "deepplan",
                        "workflow_name": "create_deep_plan",
                        "current_step_id": "initial_understanding",
                        "status": "active",
                    }
                ]
            },
        )

        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == "block"
        assert "finished_step" in result.reason

    def test_empty_workflow_stack(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        _write_state(session_dir, "state.json", {"workflow_stack": []})

        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == "block"
        assert "start_workflow" in result.reason


class TestAllowCases:
    """Hook should allow when deepplan is at present_plan or completed."""

    def test_active_deepplan_at_present_plan(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        _write_state(
            session_dir,
            "state.json",
            {
                "workflow_stack": [
                    {
                        "job_name": "deepplan",
                        "workflow_name": "create_deep_plan",
                        "current_step_id": "present_plan",
                        "status": "active",
                    }
                ]
            },
        )

        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""

    def test_completed_deepplan(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        _write_state(
            session_dir,
            "state.json",
            {
                "workflow_stack": [],
                "completed_workflows": [
                    {
                        "job_name": "deepplan",
                        "workflow_name": "create_deep_plan",
                        "current_step_id": "present_plan",
                        "status": "completed",
                    }
                ],
            },
        )

        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""


class TestAgentStateFiles:
    """Hook should detect deepplan in agent-specific state files."""

    def test_deepplan_in_agent_state_file(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        # Main state has no deepplan
        _write_state(session_dir, "state.json", {"workflow_stack": []})
        # Agent state has deepplan at present_plan
        _write_state(
            session_dir,
            "agent_abc123.json",
            {
                "workflow_stack": [
                    {
                        "job_name": "deepplan",
                        "workflow_name": "create_deep_plan",
                        "current_step_id": "present_plan",
                        "status": "active",
                    }
                ]
            },
        )

        hook_input = _make_hook_input(cwd=str(tmp_path))
        result = deepplan_exit_hook(hook_input)
        assert result.decision == ""


class TestReadDeepplanState:
    """Direct tests of the _read_deepplan_state helper."""

    def test_nonexistent_session_dir(self, tmp_path: Path) -> None:
        assert _read_deepplan_state(tmp_path, "nonexistent") == "none"

    def test_corrupt_json(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        session_dir.mkdir(parents=True)
        (session_dir / "state.json").write_text("not json", encoding="utf-8")
        assert _read_deepplan_state(tmp_path, "test-session") == "none"

    def test_non_deepplan_workflow(self, tmp_path: Path) -> None:
        session_dir = (
            tmp_path / ".deepwork" / "tmp" / "sessions" / "claude" / "session-test-session"
        )
        _write_state(
            session_dir,
            "state.json",
            {
                "workflow_stack": [
                    {
                        "job_name": "other_job",
                        "current_step_id": "some_step",
                        "status": "active",
                    }
                ]
            },
        )
        assert _read_deepplan_state(tmp_path, "test-session") == "none"
