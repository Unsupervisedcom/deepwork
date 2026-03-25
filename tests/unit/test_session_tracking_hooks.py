"""Tests for learning-agents session tracking hooks.

Covers LA-REQ-004 requirements for both post_task.sh (subagent tracking)
and session_stop.sh (top-level agent tracking + pending learning detection).
"""

import json
import os
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
POST_TASK_SCRIPT = REPO_ROOT / "learning_agents" / "hooks" / "post_task.sh"
SESSION_STOP_SCRIPT = REPO_ROOT / "learning_agents" / "hooks" / "session_stop.sh"
HOOKS_JSON = REPO_ROOT / "learning_agents" / "hooks" / "hooks.json"


@pytest.fixture
def work_dir() -> Generator[Path, None, None]:
    """Create a temp directory simulating a project with a learning agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir)
        # Create a learning agent directory
        agent_dir = work / ".deepwork" / "learning-agents" / "test-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "core-knowledge.md").write_text("You are a test agent.")
        yield work


def run_hook(script: Path, hook_input: dict[str, Any] | None, cwd: Path) -> tuple[int, str]:
    """Run a hook script with JSON input on stdin, return (exit_code, stdout)."""
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO_ROOT / "learning_agents")
    result = subprocess.run(
        ["bash", str(script)],
        input=json.dumps(hook_input) if hook_input else "",
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    return result.returncode, result.stdout.strip()


# ===========================================================================
# hooks.json configuration tests (LA-REQ-004.1, LA-REQ-004.12)
# ===========================================================================


class TestHooksJsonConfig:
    """Tests for hooks.json hook configuration."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_post_tool_use_task_matcher(self) -> None:
        hooks_config = json.loads(HOOKS_JSON.read_text())
        post_tool_use = hooks_config["hooks"]["PostToolUse"]
        task_hooks = [h for h in post_tool_use if h["matcher"] == "Task"]
        assert len(task_hooks) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.12).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_stop_hook_empty_matcher(self) -> None:
        hooks_config = json.loads(HOOKS_JSON.read_text())
        stop_hooks = hooks_config["hooks"]["Stop"]
        assert any(h["matcher"] == "" for h in stop_hooks)


# ===========================================================================
# post_task.sh tests (LA-REQ-004.2 through LA-REQ-004.11)
# ===========================================================================


class TestPostTaskHook:
    """Tests for post_task.sh — subagent session tracking."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_empty_stdin_returns_empty_json(self, work_dir: Path) -> None:
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, None, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_session_id(self, work_dir: Path) -> None:
        hook_input = {
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-123"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_agent_name(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {},
            "tool_response": {"agentId": "agent-123"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_agent_id(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {"name": "test-agent"},
            "tool_response": {},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_non_learning_agent_exits_silently(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {"name": "not-a-learning-agent"},
            "tool_response": {"agentId": "agent-123"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"
        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-1"
        assert not session_dir.exists()

    # THIS TEST VALIDATES HARD REQUIREMENTS (LA-REQ-004.7, LA-REQ-004.8, LA-REQ-004.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENTS CHANGE
    def test_creates_session_tracking_files(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-abc"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-1" / "agent-abc"
        assert session_dir.is_dir()  # LA-REQ-004.7

        # LA-REQ-004.8: timestamp file exists with ISO 8601 content
        ts_file = session_dir / "needs_learning_as_of_timestamp"
        assert ts_file.exists()
        ts_content = ts_file.read_text().strip()
        assert ts_content.endswith("Z")
        assert "T" in ts_content

        # LA-REQ-004.9: agent_used file
        agent_file = session_dir / "agent_used"
        assert agent_file.exists()
        assert agent_file.read_text().strip() == "test-agent"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_name_normalization(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-2",
            "tool_input": {"name": "Test Agent"},
            "tool_response": {"agentId": "agent-xyz"},
        }
        exit_code, _ = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-2" / "agent-xyz"
        agent_file = session_dir / "agent_used"
        assert agent_file.read_text().strip() == "test-agent"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_id_fallback(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-3",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agent_id": "fallback-id"},
        }
        exit_code, _ = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-3" / "fallback-id"
        assert session_dir.is_dir()

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_post_task_reminder_output(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-reminder",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-rem"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        output = json.loads(stdout)
        assert "hookSpecificOutput" in output
        ctx = output["hookSpecificOutput"].get("additionalContext", "")
        # LA-REQ-004.11: reminder must mention resuming and reporting issues
        assert "resume" in ctx.lower() or "Resume" in ctx
        assert "report" in ctx.lower() or "/learning-agents" in ctx

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.18).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_timestamp_overwritten_on_repeat(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-4",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-repeat"},
        }
        run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-4" / "agent-repeat"
        (session_dir / "needs_learning_as_of_timestamp").read_text()

        # Run again — file should be overwritten (not appended)
        run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        ts2 = (session_dir / "needs_learning_as_of_timestamp").read_text()

        # Content should be a single timestamp line (not two lines)
        assert ts2.count("\n") <= 1

    # Transcript symlink creation
    def test_transcript_symlink_created(self, work_dir: Path) -> None:
        # Create a fake transcript file
        transcript = work_dir / "transcripts" / "sess-5"
        transcript.mkdir(parents=True)
        subagent_transcript = transcript / "subagents" / "agent-agent-sym.jsonl"
        subagent_transcript.parent.mkdir(parents=True)
        subagent_transcript.write_text('{"type":"test"}\n')

        hook_input = {
            "session_id": "sess-5",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-sym"},
            "transcript_path": str(work_dir / "transcripts" / "sess-5.jsonl"),
        }
        # Create the parent transcript file so the path math works
        (work_dir / "transcripts" / "sess-5.jsonl").write_text("")

        exit_code, _ = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-5" / "agent-sym"
        symlink = session_dir / "conversation_transcript.jsonl"
        assert symlink.is_symlink() or symlink.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.17).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_session_files_under_correct_base_dir(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-loc",
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-loc"},
        }
        run_hook(POST_TASK_SCRIPT, hook_input, work_dir)

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "sess-loc" / "agent-loc"
        assert session_dir.is_dir()
        # Verify the path is under .deepwork/tmp/agent_sessions/
        assert ".deepwork/tmp/agent_sessions" in str(session_dir)


# ===========================================================================
# session_stop.sh tests (LA-REQ-004.12 through LA-REQ-004.23)
# ===========================================================================


class TestSessionStopHook:
    """Tests for session_stop.sh — top-level tracking + pending detection."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.13).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_sessions_dir_returns_empty(self, work_dir: Path) -> None:
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "s1"}, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.14).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_pending_files_returns_empty(self, work_dir: Path) -> None:
        sessions_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions"
        sessions_dir.mkdir(parents=True)
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "s1"}, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # THIS TEST VALIDATES HARD REQUIREMENTS (LA-REQ-004.19, LA-REQ-004.20, LA-REQ-004.21, LA-REQ-004.22).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENTS CHANGE
    def test_top_level_agent_creates_tracking(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "top-sess-1",
            "agent_type": "test-agent",
            "transcript_path": "/tmp/nonexistent.jsonl",
        }
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-sess-1" / "top-level"
        assert session_dir.is_dir()
        assert (session_dir / "needs_learning_as_of_timestamp").exists()
        assert (session_dir / "agent_used").read_text().strip() == "test-agent"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.20).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_agent_name_normalization(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "top-sess-2",
            "agent_type": "Test Agent",
            "transcript_path": "/tmp/nonexistent.jsonl",
        }
        exit_code, _ = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-sess-2" / "top-level"
        assert (session_dir / "agent_used").read_text().strip() == "test-agent"

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.20).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_non_learning_agent_ignored(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "top-sess-3",
            "agent_type": "not-a-learning-agent",
        }
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"
        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-sess-3"
        assert not session_dir.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.23).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_transcript_symlink(self, work_dir: Path) -> None:
        transcript_file = work_dir / "my-transcript.jsonl"
        transcript_file.write_text('{"type":"test"}\n')

        hook_input = {
            "session_id": "top-sess-4",
            "agent_type": "test-agent",
            "transcript_path": str(transcript_file),
        }
        exit_code, _ = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-sess-4" / "top-level"
        symlink = session_dir / "conversation_transcript.jsonl"
        assert symlink.is_symlink()
        assert symlink.resolve() == transcript_file.resolve()

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.23).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_no_symlink_when_transcript_missing(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "top-sess-5",
            "agent_type": "test-agent",
            "transcript_path": "/tmp/does-not-exist.jsonl",
        }
        exit_code, _ = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-sess-5" / "top-level"
        assert session_dir.is_dir()
        assert not (session_dir / "conversation_transcript.jsonl").exists()

    # THIS TEST VALIDATES HARD REQUIREMENTS (LA-REQ-004.14, LA-REQ-004.15, LA-REQ-004.16).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENTS CHANGE
    def test_pending_sessions_trigger_suggestion(self, work_dir: Path) -> None:
        # Pre-create a pending session
        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "old-sess" / "agent-old"
        session_dir.mkdir(parents=True)
        (session_dir / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
        (session_dir / "agent_used").write_text("test-agent")

        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "s1"}, work_dir)
        assert exit_code == 0

        output = json.loads(stdout)
        assert "systemMessage" in output
        assert "test-agent" in output["systemMessage"]
        assert "/learning-agents learn" in output["systemMessage"]

    # Combined: top-level tracking AND pending detection in same invocation
    def test_top_level_tracking_and_pending_detection(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "combined-sess",
            "agent_type": "test-agent",
            "transcript_path": "/tmp/nonexistent.jsonl",
        }
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0

        # Should have created tracking files
        session_dir = (
            work_dir / ".deepwork" / "tmp" / "agent_sessions" / "combined-sess" / "top-level"
        )
        assert session_dir.is_dir()

        # AND should suggest learning (the session it just created is pending)
        output = json.loads(stdout)
        assert "systemMessage" in output
        assert "test-agent" in output["systemMessage"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.19).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_agent_type_skips_tracking(self, work_dir: Path) -> None:
        hook_input = {"session_id": "normal-sess"}
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"
        assert not (work_dir / ".deepwork" / "tmp" / "agent_sessions" / "normal-sess").exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.15).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_name_deduplication(self, work_dir: Path) -> None:
        base = work_dir / ".deepwork" / "tmp" / "agent_sessions"
        for i in range(3):
            d = base / f"sess-{i}" / f"agent-{i}"
            d.mkdir(parents=True)
            (d / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
            (d / "agent_used").write_text("test-agent")

        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "x"}, work_dir)
        assert exit_code == 0
        output = json.loads(stdout)
        # Agent name should appear only once despite 3 sessions
        msg = output["systemMessage"]
        assert msg.count("test-agent") == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.17).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_session_files_under_correct_base_dir(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "top-loc",
            "agent_type": "test-agent",
            "transcript_path": "/tmp/nonexistent.jsonl",
        }
        run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)

        session_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions" / "top-loc" / "top-level"
        assert session_dir.is_dir()
        assert ".deepwork/tmp/agent_sessions" in str(session_dir)
