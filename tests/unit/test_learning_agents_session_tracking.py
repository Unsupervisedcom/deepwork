"""Tests for session tracking hooks.

Validates requirements: LA-REQ-004, LA-REQ-004.1, LA-REQ-004.2, LA-REQ-004.3,
LA-REQ-004.4, LA-REQ-004.5, LA-REQ-004.6, LA-REQ-004.7, LA-REQ-004.8, LA-REQ-004.9,
LA-REQ-004.10, LA-REQ-004.11, LA-REQ-004.12, LA-REQ-004.13, LA-REQ-004.14,
LA-REQ-004.15, LA-REQ-004.16, LA-REQ-004.17, LA-REQ-004.18.

Each test maps to a numbered requirement in
specs/learning-agents/LA-REQ-004-session-tracking.md.

Tests validate hook script content (jq commands, file paths, variable handling)
and behavioral logic (script execution with controlled inputs).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_DIR = PROJECT_ROOT / "learning_agents" / "hooks"
POST_TASK_SCRIPT = HOOKS_DIR / "post_task.sh"
SESSION_STOP_SCRIPT = HOOKS_DIR / "session_stop.sh"
HOOKS_JSON = HOOKS_DIR / "hooks.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_script(path: Path) -> str:
    return path.read_text()


def _run_post_task(
    stdin_data: str = "",
    env_overrides: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run post_task.sh with given stdin and environment."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(POST_TASK_SCRIPT)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
    )


def _run_session_stop(
    stdin_data: str = "",
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run session_stop.sh with given stdin and cwd."""
    return subprocess.run(
        ["bash", str(SESSION_STOP_SCRIPT)],
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def _make_hook_input(
    session_id: str = "sess-123",
    agent_name: str = "test-agent",
    agent_id: str = "agent-456",
    transcript_path: str | None = None,
) -> str:
    """Build a valid hook input JSON string."""
    data: dict[str, Any] = {
        "session_id": session_id,
        "tool_input": {"name": agent_name},
        "tool_response": {"agentId": agent_id},
    }
    if transcript_path is not None:
        data["transcript_path"] = transcript_path
    return json.dumps(data)


# ===========================================================================
# LA-REQ-004.1: PostToolUse Hook Trigger
# ===========================================================================


class TestPostToolUseHookTrigger:
    def test_hooks_json_has_post_tool_use_section(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """hooks.json must contain a PostToolUse section."""
        config = json.loads(HOOKS_JSON.read_text())
        assert "PostToolUse" in config["hooks"]

    def test_hooks_json_post_tool_use_matcher_is_task(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PostToolUse hook matcher MUST be 'Task'."""
        config = json.loads(HOOKS_JSON.read_text())
        matchers = [entry["matcher"] for entry in config["hooks"]["PostToolUse"]]
        assert "Task" in matchers

    def test_hooks_json_post_tool_use_runs_post_task_sh(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """PostToolUse hook must invoke post_task.sh."""
        config = json.loads(HOOKS_JSON.read_text())
        for entry in config["hooks"]["PostToolUse"]:
            if entry["matcher"] == "Task":
                commands = [h["command"] for h in entry["hooks"]]
                assert any("post_task.sh" in cmd for cmd in commands)


# ===========================================================================
# LA-REQ-004.2: Post-Task Input Parsing
# ===========================================================================


class TestPostTaskInputParsing:
    def test_script_reads_stdin(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """post_task.sh reads JSON from stdin."""
        script = _read_script(POST_TASK_SCRIPT)
        assert "cat" in script or "read" in script, "Script must read from stdin"

    def test_empty_stdin_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Empty stdin must produce '{}' and exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_post_task(stdin_data="", cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}

    def test_interactive_terminal_check(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script checks if stdin is a terminal ([ ! -t 0 ])."""
        script = _read_script(POST_TASK_SCRIPT)
        assert "! -t 0" in script


# ===========================================================================
# LA-REQ-004.3: Session ID Extraction
# ===========================================================================


class TestSessionIdExtraction:
    def test_script_extracts_session_id_via_jq(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must use jq to extract .session_id."""
        script = _read_script(POST_TASK_SCRIPT)
        assert ".session_id" in script

    def test_missing_session_id_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Missing session_id must produce '{}' and exit 0."""
        data = json.dumps({"tool_input": {"name": "foo"}, "tool_response": {"agentId": "a1"}})
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_post_task(stdin_data=data, cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}


# ===========================================================================
# LA-REQ-004.4: Agent Name Extraction
# ===========================================================================


class TestAgentNameExtraction:
    def test_script_extracts_agent_name_from_tool_input(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must extract agent name from .tool_input.name."""
        script = _read_script(POST_TASK_SCRIPT)
        assert ".tool_input.name" in script

    def test_missing_agent_name_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Missing agent name must produce '{}' and exit 0."""
        data = json.dumps(
            {"session_id": "s1", "tool_input": {}, "tool_response": {"agentId": "a1"}}
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_post_task(stdin_data=data, cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}


# ===========================================================================
# LA-REQ-004.5: Agent ID Extraction
# ===========================================================================


class TestAgentIdExtraction:
    def test_script_extracts_agent_id_with_fallback(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must extract from .tool_response.agentId with fallback to .tool_response.agent_id."""
        script = _read_script(POST_TASK_SCRIPT)
        assert ".tool_response.agentId" in script
        assert ".tool_response.agent_id" in script

    def test_missing_agent_id_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Missing agent ID must produce '{}' and exit 0."""
        data = json.dumps({"session_id": "s1", "tool_input": {"name": "foo"}, "tool_response": {}})
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_post_task(stdin_data=data, cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}

    def test_agent_id_fallback_to_snake_case(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """agent_id (snake_case) fallback must work when agentId is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the agent dir so detection passes
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "foo"
            agent_dir.mkdir(parents=True)
            data = json.dumps(
                {
                    "session_id": "s1",
                    "tool_input": {"name": "foo"},
                    "tool_response": {"agent_id": "fallback-id"},
                }
            )
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            result = _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            assert result.returncode == 0
            session_dir = (
                Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / "s1" / "fallback-id"
            )
            assert session_dir.is_dir(), "Session dir should be created using fallback agent_id"


# ===========================================================================
# LA-REQ-004.6: LearningAgent Detection
# ===========================================================================


class TestLearningAgentDetection:
    def test_script_checks_agent_directory_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must check for .deepwork/learning-agents/<agent-name>/ directory."""
        script = _read_script(POST_TASK_SCRIPT)
        assert ".deepwork/learning-agents/" in script
        assert "! -d" in script

    def test_non_learning_agent_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Non-LearningAgent (no directory) must produce '{}' and exit 0, no files created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Do NOT create .deepwork/learning-agents/foo/
            data = _make_hook_input(agent_name="nonexistent-agent")
            result = _run_post_task(stdin_data=data, cwd=tmpdir)
            assert result.returncode == 0
            assert json.loads(result.stdout.strip()) == {}
            # No session files should have been created
            sessions_dir = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions"
            assert not sessions_dir.exists()


# ===========================================================================
# LA-REQ-004.7: Session Directory Creation
# ===========================================================================


class TestSessionDirectoryCreation:
    def test_script_creates_session_dir_with_mkdir_p(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must use mkdir -p for session directory."""
        script = _read_script(POST_TASK_SCRIPT)
        assert "mkdir -p" in script

    def test_session_dir_created_at_correct_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Session dir must be .deepwork/tmp/agent_sessions/<session_id>/<agent_id>/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(
                session_id="sess-abc",
                agent_name="my-agent",
                agent_id="agent-xyz",
            )
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            result = _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            assert result.returncode == 0
            expected_dir = (
                Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / "sess-abc" / "agent-xyz"
            )
            assert expected_dir.is_dir(), f"Expected session dir at {expected_dir}"


# ===========================================================================
# LA-REQ-004.8: Needs Learning Timestamp File
# ===========================================================================


class TestNeedsLearningTimestamp:
    def test_timestamp_file_created(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """needs_learning_as_of_timestamp file must be created in session dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            result = _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            assert result.returncode == 0
            ts_file = (
                Path(tmpdir)
                / ".deepwork"
                / "tmp"
                / "agent_sessions"
                / "sess-123"
                / "agent-456"
                / "needs_learning_as_of_timestamp"
            )
            assert ts_file.is_file()

    def test_timestamp_file_contains_iso8601_utc(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Timestamp file must contain ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)."""
        import re

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            ts_file = (
                Path(tmpdir)
                / ".deepwork"
                / "tmp"
                / "agent_sessions"
                / "sess-123"
                / "agent-456"
                / "needs_learning_as_of_timestamp"
            )
            content = ts_file.read_text().strip()
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", content), (
                f"Timestamp '{content}' does not match ISO 8601 UTC format"
            )

    def test_script_uses_date_u_for_utc(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must use 'date -u' for UTC timestamps."""
        script = _read_script(POST_TASK_SCRIPT)
        assert "date -u" in script


# ===========================================================================
# LA-REQ-004.9: Agent Used File
# ===========================================================================


class TestAgentUsedFile:
    def test_agent_used_file_created(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.9).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """agent_used file must be created in session dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            agent_file = (
                Path(tmpdir)
                / ".deepwork"
                / "tmp"
                / "agent_sessions"
                / "sess-123"
                / "agent-456"
                / "agent_used"
            )
            assert agent_file.is_file()

    def test_agent_used_file_contains_agent_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.9).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """agent_used file must contain the agent name matching the directory name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            agent_file = (
                Path(tmpdir)
                / ".deepwork"
                / "tmp"
                / "agent_sessions"
                / "sess-123"
                / "agent-456"
                / "agent_used"
            )
            assert agent_file.read_text().strip() == "my-agent"


# ===========================================================================
# LA-REQ-004.10: Post-Task Reminder Message
# ===========================================================================


class TestPostTaskReminderMessage:
    def test_script_reads_reminder_file(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must read learning_agent_post_task_reminder.md from CLAUDE_PLUGIN_ROOT/doc/."""
        script = _read_script(POST_TASK_SCRIPT)
        assert "learning_agent_post_task_reminder.md" in script
        assert "CLAUDE_PLUGIN_ROOT" in script

    def test_reminder_present_outputs_system_message(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """When reminder file exists, output must contain hookSpecificOutput with additionalContext."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            # Create a fake plugin root with the reminder file
            plugin_root = Path(tmpdir) / "plugin"
            doc_dir = plugin_root / "doc"
            doc_dir.mkdir(parents=True)
            (doc_dir / "learning_agent_post_task_reminder.md").write_text("Remember to review.")
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(plugin_root)}
            result = _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "Remember to review." in output["hookSpecificOutput"]["additionalContext"]

    def test_missing_reminder_file_outputs_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """When reminder file does not exist, output must be '{}'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            # Point CLAUDE_PLUGIN_ROOT to a dir with no doc/ subdirectory
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            result = _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}


# ===========================================================================
# LA-REQ-004.11: Post-Task Reminder Content
# ===========================================================================


class TestPostTaskReminderContent:
    def test_reminder_file_exists_in_repo(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """The post-task reminder file must exist in the plugin."""
        reminder_path = (
            PROJECT_ROOT / "learning_agents" / "doc" / "learning_agent_post_task_reminder.md"
        )
        assert reminder_path.is_file(), f"Expected reminder file at {reminder_path}"

    def test_reminder_mentions_resume_task(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Reminder must instruct users to resume the same task rather than starting a new one."""
        reminder_path = (
            PROJECT_ROOT / "learning_agents" / "doc" / "learning_agent_post_task_reminder.md"
        )
        if not reminder_path.is_file():
            # Try alternate location
            from glob import glob

            matches = glob(
                str(PROJECT_ROOT / "**/learning_agent_post_task_reminder.md"), recursive=True
            )
            assert matches, "Cannot find learning_agent_post_task_reminder.md anywhere"
            reminder_path = Path(matches[0])
        content = reminder_path.read_text().lower()
        assert "resume" in content or "same task" in content, (
            "Reminder must mention resuming the same task"
        )

    def test_reminder_mentions_report_issue(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Reminder must mention /learning-agents report_issue or resuming for mistakes."""
        reminder_path = (
            PROJECT_ROOT / "learning_agents" / "doc" / "learning_agent_post_task_reminder.md"
        )
        if not reminder_path.is_file():
            from glob import glob

            matches = glob(
                str(PROJECT_ROOT / "**/learning_agent_post_task_reminder.md"), recursive=True
            )
            assert matches, "Cannot find learning_agent_post_task_reminder.md anywhere"
            reminder_path = Path(matches[0])
        content = reminder_path.read_text().lower()
        assert "report" in content or "issue" in content, "Reminder must mention reporting issues"


# ===========================================================================
# LA-REQ-004.12: Stop Hook Trigger
# ===========================================================================


class TestStopHookTrigger:
    def test_hooks_json_has_stop_section(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.12).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """hooks.json must contain a Stop section."""
        config = json.loads(HOOKS_JSON.read_text())
        assert "Stop" in config["hooks"]

    def test_stop_hook_matcher_is_empty_string(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.12).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Stop hook matcher MUST be empty string to trigger for all stop events."""
        config = json.loads(HOOKS_JSON.read_text())
        matchers = [entry["matcher"] for entry in config["hooks"]["Stop"]]
        assert "" in matchers

    def test_stop_hook_runs_session_stop_sh(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.12).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Stop hook must invoke session_stop.sh."""
        config = json.loads(HOOKS_JSON.read_text())
        for entry in config["hooks"]["Stop"]:
            if entry["matcher"] == "":
                commands = [h["command"] for h in entry["hooks"]]
                assert any("session_stop.sh" in cmd for cmd in commands)


# ===========================================================================
# LA-REQ-004.13: Stop Hook -- No Sessions Directory
# ===========================================================================


class TestStopHookNoSessionsDir:
    def test_no_sessions_dir_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """If .deepwork/tmp/agent_sessions does not exist, output '{}' and exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_session_stop(cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}

    def test_script_checks_sessions_dir_existence(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must check for .deepwork/tmp/agent_sessions directory."""
        script = _read_script(SESSION_STOP_SCRIPT)
        assert ".deepwork/tmp/agent_sessions" in script
        assert "! -d" in script


# ===========================================================================
# LA-REQ-004.14: Stop Hook -- Pending Session Detection
# ===========================================================================


class TestStopHookPendingDetection:
    def test_script_searches_for_needs_learning_files(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.14).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must search for needs_learning_as_of_timestamp files."""
        script = _read_script(SESSION_STOP_SCRIPT)
        assert "needs_learning_as_of_timestamp" in script
        assert "find" in script

    def test_no_pending_files_returns_empty_json(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.14).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """If no needs_learning_as_of_timestamp files, output '{}' and exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions"
            sessions_dir.mkdir(parents=True)
            # Directory exists but is empty
            result = _run_session_stop(cwd=tmpdir)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {}


# ===========================================================================
# LA-REQ-004.15: Stop Hook -- Agent Name Resolution
# ===========================================================================


class TestStopHookAgentNameResolution:
    def test_script_reads_agent_used_file(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.15).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must read agent_used file to determine agent name."""
        script = _read_script(SESSION_STOP_SCRIPT)
        assert "agent_used" in script

    def test_script_deduplicates_agent_names(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.15).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must deduplicate agent names (sort -u or equivalent)."""
        script = _read_script(SESSION_STOP_SCRIPT)
        assert "sort -u" in script or "uniq" in script


# ===========================================================================
# LA-REQ-004.16: Stop Hook -- Learning Suggestion Message
# ===========================================================================


class TestStopHookLearningSuggestion:
    def test_pending_sessions_output_system_message(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.16).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """When pending sessions exist, output must contain systemMessage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / "s1" / "a1"
            session_dir.mkdir(parents=True)
            (session_dir / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
            (session_dir / "agent_used").write_text("my-agent")
            result = _run_session_stop(cwd=tmpdir)
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert "systemMessage" in output

    def test_suggestion_lists_agent_names(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.16).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Suggestion message must list the unique agent names used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for sid, aid, name in [("s1", "a1", "agent-a"), ("s1", "a2", "agent-b")]:
                d = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / sid / aid
                d.mkdir(parents=True)
                (d / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
                (d / "agent_used").write_text(name)
            result = _run_session_stop(cwd=tmpdir)
        output = json.loads(result.stdout.strip())
        msg = output["systemMessage"]
        assert "agent-a" in msg
        assert "agent-b" in msg

    def test_suggestion_mentions_learn_command(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.16).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Suggestion must mention /learning-agents learn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / "s1" / "a1"
            session_dir.mkdir(parents=True)
            (session_dir / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
            (session_dir / "agent_used").write_text("my-agent")
            result = _run_session_stop(cwd=tmpdir)
        output = json.loads(result.stdout.strip())
        assert (
            "/learning-agents learn" in output["systemMessage"]
            or "learning-agents learn" in output["systemMessage"]
        )

    def test_deduplication_in_message(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.16).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Duplicate agent names from multiple invocations must be deduplicated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for sid, aid in [("s1", "a1"), ("s2", "a2")]:
                d = Path(tmpdir) / ".deepwork" / "tmp" / "agent_sessions" / sid / aid
                d.mkdir(parents=True)
                (d / "needs_learning_as_of_timestamp").write_text("2026-01-01T00:00:00Z")
                (d / "agent_used").write_text("same-agent")
            result = _run_session_stop(cwd=tmpdir)
        output = json.loads(result.stdout.strip())
        msg = output["systemMessage"]
        # "same-agent" should appear only once
        assert msg.count("same-agent") == 1


# ===========================================================================
# LA-REQ-004.17: Session Directory Location
# ===========================================================================


class TestSessionDirectoryLocation:
    def test_post_task_uses_correct_base_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.17).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Session tracking files must be under .deepwork/tmp/agent_sessions/."""
        script = _read_script(POST_TASK_SCRIPT)
        assert ".deepwork/tmp/agent_sessions/" in script

    def test_stop_hook_uses_correct_base_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.17).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Stop hook must look under .deepwork/tmp/agent_sessions/."""
        script = _read_script(SESSION_STOP_SCRIPT)
        assert ".deepwork/tmp/agent_sessions" in script


# ===========================================================================
# LA-REQ-004.18: Timestamp File Update Semantics
# ===========================================================================


class TestTimestampFileUpdateSemantics:
    def test_timestamp_overwritten_not_appended(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.18).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Running the hook twice for the same agent/session must overwrite the timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".deepwork" / "learning-agents" / "my-agent"
            agent_dir.mkdir(parents=True)
            data = _make_hook_input(agent_name="my-agent")
            env = {"CLAUDE_PLUGIN_ROOT": str(Path(tmpdir) / "nonexistent-plugin")}
            # First invocation
            _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            ts_file = (
                Path(tmpdir)
                / ".deepwork"
                / "tmp"
                / "agent_sessions"
                / "sess-123"
                / "agent-456"
                / "needs_learning_as_of_timestamp"
            )
            first_content = ts_file.read_text()
            # Second invocation
            _run_post_task(stdin_data=data, cwd=tmpdir, env_overrides=env)
            second_content = ts_file.read_text()
        # File should contain exactly one timestamp line (overwritten, not appended)
        assert second_content.count("\n") <= 1, (
            "Timestamp file should contain a single line (overwrite, not append)"
        )
        # Both should be valid single timestamps
        assert first_content.strip().count("T") == 1
        assert second_content.strip().count("T") == 1

    def test_script_uses_overwrite_redirect(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-004.18).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Script must use '>' (overwrite) not '>>' (append) for timestamp file."""
        script = _read_script(POST_TASK_SCRIPT)
        # Find the line that writes the timestamp
        for line in script.splitlines():
            if "needs_learning_as_of_timestamp" in line and "date" in line:
                assert ">" in line, "Must use redirect to write timestamp"
                assert ">>" not in line, "Must use '>' (overwrite) not '>>' (append)"
                break
