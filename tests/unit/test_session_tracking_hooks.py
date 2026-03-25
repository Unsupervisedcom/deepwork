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
# post_task.sh tests (LA-REQ-004.1 through LA-REQ-004.11)
# ===========================================================================


class TestPostTaskHook:
    """Tests for post_task.sh — subagent session tracking."""

    # LA-REQ-004.2: empty stdin
    def test_empty_stdin_returns_empty_json(self, work_dir: Path) -> None:
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, None, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # LA-REQ-004.3: missing session_id
    def test_missing_session_id(self, work_dir: Path) -> None:
        hook_input = {
            "tool_input": {"name": "test-agent"},
            "tool_response": {"agentId": "agent-123"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # LA-REQ-004.4: missing agent name
    def test_missing_agent_name(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {},
            "tool_response": {"agentId": "agent-123"},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # LA-REQ-004.5: missing agent_id
    def test_missing_agent_id(self, work_dir: Path) -> None:
        hook_input = {
            "session_id": "sess-1",
            "tool_input": {"name": "test-agent"},
            "tool_response": {},
        }
        exit_code, stdout = run_hook(POST_TASK_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # LA-REQ-004.6: non-learning-agent exits silently
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

    # LA-REQ-004.7, LA-REQ-004.8, LA-REQ-004.9: session directory and files created
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

    # LA-REQ-004.4 (normalization): uppercase and spaces normalized
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

    # LA-REQ-004.5: agentId fallback to agent_id
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

    # LA-REQ-004.18: timestamp overwritten on repeated invocation
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


# ===========================================================================
# session_stop.sh tests (LA-REQ-004.12 through LA-REQ-004.18 + top-level)
# ===========================================================================


class TestSessionStopHook:
    """Tests for session_stop.sh — top-level tracking + pending detection."""

    # LA-REQ-004.13: no agent_sessions dir
    def test_no_sessions_dir_returns_empty(self, work_dir: Path) -> None:
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "s1"}, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # LA-REQ-004.14: no pending files
    def test_no_pending_files_returns_empty(self, work_dir: Path) -> None:
        sessions_dir = work_dir / ".deepwork" / "tmp" / "agent_sessions"
        sessions_dir.mkdir(parents=True)
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, {"session_id": "s1"}, work_dir)
        assert exit_code == 0
        assert stdout == "{}"

    # Top-level agent tracking: creates session files when agent_type is a learning agent
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

    # Top-level agent tracking: agent_type normalization
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

    # Top-level agent tracking: non-learning agent is ignored
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

    # Top-level agent tracking: transcript symlink created when file exists
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

    # Top-level agent tracking: no symlink when transcript file doesn't exist
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

    # LA-REQ-004.14, LA-REQ-004.15, LA-REQ-004.16: pending detection and suggestion
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

    # No agent_type means no top-level tracking
    def test_no_agent_type_skips_tracking(self, work_dir: Path) -> None:
        hook_input = {"session_id": "normal-sess"}
        exit_code, stdout = run_hook(SESSION_STOP_SCRIPT, hook_input, work_dir)
        assert exit_code == 0
        assert stdout == "{}"
        assert not (work_dir / ".deepwork" / "tmp" / "agent_sessions" / "normal-sess").exists()

    # LA-REQ-004.15: deduplication of agent names in suggestion
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
