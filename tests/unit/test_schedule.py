"""Tests for schedule command (CLI layer)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from deepwork.cli.runners import ScheduleError


class TestScheduleAdd:
    """Tests for schedule add command."""

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_systemd(
        self,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test adding a schedule on systemd."""
        from deepwork.cli.schedule import _add_schedule

        mock_runner = Mock()
        mock_runner.name = "systemd"
        mock_runner.display_name = "Systemd Timer"
        mock_detect.return_value = mock_runner
        mock_is_git.return_value = True

        (temp_dir / ".deepwork").mkdir()

        _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

        mock_runner.install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, "daily"
        )

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_launchd(
        self,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test adding a schedule on launchd."""
        from deepwork.cli.schedule import _add_schedule

        mock_runner = Mock()
        mock_runner.name = "launchd"
        mock_runner.display_name = "macOS LaunchAgent"
        mock_detect.return_value = mock_runner
        mock_is_git.return_value = True

        (temp_dir / ".deepwork").mkdir()

        _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

        mock_runner.install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, "daily"
        )

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_not_git_repo(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test adding schedule fails when not a git repo."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = False

        with pytest.raises(ScheduleError, match="Not a Git repository"):
            _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_unsupported_system(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test adding schedule fails on unsupported system."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = True
        mock_detect.return_value = None

        (temp_dir / ".deepwork").mkdir()

        with pytest.raises(ScheduleError, match="Unsupported system"):
            _add_schedule("test-task", "deepwork sync", "daily", temp_dir)


class TestScheduleRemove:
    """Tests for schedule remove command."""

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    def test_remove_schedule(self, mock_detect: Mock, temp_dir: Path) -> None:
        """Test removing a schedule."""
        from deepwork.cli.schedule import _remove_schedule

        mock_runner = Mock()
        mock_runner.name = "systemd"
        mock_runner.display_name = "Systemd Timer"
        mock_detect.return_value = mock_runner

        _remove_schedule("test-task", temp_dir)

        mock_runner.uninstall.assert_called_once_with("test-task")

    @patch("deepwork.cli.schedule.ScheduleRunner.detect_runner")
    def test_remove_schedule_unsupported_system(
        self, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test removing schedule fails on unsupported system."""
        from deepwork.cli.schedule import _remove_schedule

        mock_detect.return_value = None

        with pytest.raises(ScheduleError, match="Unsupported system"):
            _remove_schedule("test-task", temp_dir)
