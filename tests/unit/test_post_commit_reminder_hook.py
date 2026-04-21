"""Tests for the post_commit_reminder hook.

Validates PLUG-REQ-001.7.2, PLUG-REQ-001.7.3, PLUG-REQ-001.7.4.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from deepwork.hooks.post_commit_reminder import (
    ALL_PASSED_CONTEXT,
    REMINDER_CONTEXT,
    _committed_files,
    main,
    post_commit_reminder_hook,
)
from deepwork.hooks.wrapper import HookInput, HookOutput, NormalizedEvent, Platform

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_hook_input(
    event: NormalizedEvent = NormalizedEvent.AFTER_TOOL,
    tool_name: str = "shell",
    command: str = "git commit -m 'test'",
    cwd: str = "/project",
) -> HookInput:
    return HookInput(
        platform=Platform.CLAUDE,
        event=event,
        session_id="sess1",
        transcript_path="",
        cwd=cwd,
        tool_name=tool_name,
        tool_input={"command": command},
        prompt="",
        raw_input={},
    )


# ---------------------------------------------------------------------------
# Early returns
# ---------------------------------------------------------------------------


class TestPostCommitReminderEarlyReturns:
    def test_ignores_non_after_tool_event(self) -> None:
        inp = _make_hook_input(event=NormalizedEvent.BEFORE_TOOL)
        assert post_commit_reminder_hook(inp) == HookOutput()

    def test_ignores_non_shell_tool(self) -> None:
        inp = _make_hook_input(tool_name="write_file")
        assert post_commit_reminder_hook(inp) == HookOutput()

    def test_ignores_non_git_commit_command(self) -> None:
        inp = _make_hook_input(command="git status")
        assert post_commit_reminder_hook(inp) == HookOutput()


# ---------------------------------------------------------------------------
# Review-aware paths
# ---------------------------------------------------------------------------


class TestPostCommitReminderReviewPaths:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch(
        "deepwork.review.mcp.all_reviews_passed_for_files",
        return_value=True,
    )
    @patch(
        "deepwork.hooks.post_commit_reminder._committed_files",
        return_value=["src/app.py"],
    )
    def test_all_passed_returns_all_passed_context(
        self, mock_files: object, mock_passed: object
    ) -> None:
        result = post_commit_reminder_hook(_make_hook_input())
        assert result == HookOutput(context=ALL_PASSED_CONTEXT)

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch(
        "deepwork.review.mcp.all_reviews_passed_for_files",
        return_value=True,
    )
    @patch(
        "deepwork.hooks.post_commit_reminder._committed_files",
        return_value=["README.md"],
    )
    def test_no_applicable_reviews_returns_all_passed_context(
        self, mock_files: object, mock_passed: object
    ) -> None:
        """No non-catch-all rules match → vacuously True → ALL_PASSED_CONTEXT."""
        result = post_commit_reminder_hook(_make_hook_input())
        assert result == HookOutput(context=ALL_PASSED_CONTEXT)

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch(
        "deepwork.review.mcp.all_reviews_passed_for_files",
        return_value=False,
    )
    @patch(
        "deepwork.hooks.post_commit_reminder._committed_files",
        return_value=["src/app.py"],
    )
    def test_not_all_passed_returns_reminder(self, mock_files: object, mock_passed: object) -> None:
        result = post_commit_reminder_hook(_make_hook_input())
        assert result == HookOutput(context=REMINDER_CONTEXT)

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch(
        "deepwork.hooks.post_commit_reminder._committed_files",
        return_value=None,
    )
    def test_git_failure_falls_back_to_reminder(self, mock_files: object) -> None:
        result = post_commit_reminder_hook(_make_hook_input())
        assert result == HookOutput(context=REMINDER_CONTEXT)

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-001.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch(
        "deepwork.review.mcp.all_reviews_passed_for_files",
        side_effect=RuntimeError("boom"),
    )
    @patch(
        "deepwork.hooks.post_commit_reminder._committed_files",
        return_value=["src/app.py"],
    )
    def test_exception_in_passed_check_falls_back_to_reminder(
        self, mock_files: object, mock_passed: object
    ) -> None:
        result = post_commit_reminder_hook(_make_hook_input())
        assert result == HookOutput(context=REMINDER_CONTEXT)


# ---------------------------------------------------------------------------
# _committed_files
# ---------------------------------------------------------------------------


class TestCommittedFiles:
    def test_returns_file_list_on_success(self, tmp_path: Path) -> None:
        with patch("deepwork.hooks.post_commit_reminder.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="src/a.py\nsrc/b.py\n"
            )
            result = _committed_files(tmp_path)
        assert result == ["src/a.py", "src/b.py"]

    def test_returns_none_on_called_process_error(self, tmp_path: Path) -> None:
        with patch(
            "deepwork.hooks.post_commit_reminder.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            assert _committed_files(tmp_path) is None

    def test_returns_none_on_os_error(self, tmp_path: Path) -> None:
        with patch(
            "deepwork.hooks.post_commit_reminder.subprocess.run",
            side_effect=OSError("no git"),
        ):
            assert _committed_files(tmp_path) is None

    def test_uses_diff_tree_not_show(self, tmp_path: Path) -> None:
        """git show --no-patch --name-only are incompatible flags; verify we use diff-tree."""
        with patch("deepwork.hooks.post_commit_reminder.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="a.py\n"
            )
            _committed_files(tmp_path)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "git"
        assert cmd[1] == "diff-tree"
        assert "--no-patch" not in cmd, "--no-patch conflicts with --name-only"

    def test_strips_blank_lines(self, tmp_path: Path) -> None:
        with patch("deepwork.hooks.post_commit_reminder.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="a.py\n\n  \nb.py\n"
            )
            result = _committed_files(tmp_path)
        assert result == ["a.py", "b.py"]


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_delegates_to_run_hook(self) -> None:
        with patch("deepwork.hooks.post_commit_reminder.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {"DEEPWORK_HOOK_PLATFORM": "gemini"}):
                ret = main()
        assert ret == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] == Platform("gemini")

    def test_main_defaults_to_claude(self) -> None:
        with patch("deepwork.hooks.post_commit_reminder.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {}, clear=True):
                main()
        assert mock_run.call_args[0][1] == Platform.CLAUDE

    def test_dunder_main_runs_as_script(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "deepwork.hooks.post_commit_reminder"],
            capture_output=True,
            text=True,
            timeout=10,
            input="{}",
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert isinstance(output, dict)
