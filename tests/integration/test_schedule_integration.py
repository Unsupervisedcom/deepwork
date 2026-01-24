"""Integration tests for schedule command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli


class TestScheduleCommand:
    """Integration tests for 'deepwork schedule' command."""

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    @patch("deepwork.cli.schedule._install_systemd_timer")
    def test_schedule_add_systemd(
        self,
        mock_install: Mock,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test scheduling a task on systemd."""
        mock_is_git.return_value = True
        mock_detect.return_value = "systemd"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "schedule",
                "add",
                "test-task",
                "deepwork sync",
                "--interval",
                "daily",
                "--path",
                str(temp_dir),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Scheduling DeepWork task: test-task" in result.output
        assert "Detected system: systemd" in result.output
        assert "scheduled successfully" in result.output

        mock_install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, "daily"
        )

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    @patch("deepwork.cli.schedule._install_launchd_agent")
    def test_schedule_add_launchd(
        self,
        mock_install: Mock,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test scheduling a task on launchd."""
        mock_is_git.return_value = True
        mock_detect.return_value = "launchd"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "schedule",
                "add",
                "test-task",
                "deepwork sync",
                "--interval",
                "hourly",
                "--path",
                str(temp_dir),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Scheduling DeepWork task: test-task" in result.output
        assert "Detected system: launchd" in result.output
        assert "scheduled successfully" in result.output

        # hourly should be converted to 3600 seconds
        mock_install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, 3600
        )

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule._uninstall_systemd_timer")
    def test_schedule_remove(
        self, mock_uninstall: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test removing a scheduled task."""
        mock_detect.return_value = "systemd"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["schedule", "remove", "test-task", "--path", str(temp_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Removing scheduled task: test-task" in result.output
        assert "unscheduled successfully" in result.output

        mock_uninstall.assert_called_once_with("test-task")

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule._list_systemd_timers")
    def test_schedule_list(
        self, mock_list: Mock, mock_detect: Mock
    ) -> None:
        """Test listing scheduled tasks."""
        mock_detect.return_value = "systemd"

        runner = CliRunner()
        result = runner.invoke(cli, ["schedule", "list"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "Scheduled DeepWork Tasks" in result.output
        assert "System: systemd" in result.output

        mock_list.assert_called_once()

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_schedule_add_not_git_repo(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test that scheduling fails when not in a git repo."""
        mock_is_git.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["schedule", "add", "test-task", "deepwork sync", "--path", str(temp_dir)],
        )

        assert result.exit_code == 1
        assert "Not a Git repository" in result.output

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_schedule_add_unsupported_system(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test that scheduling fails on unsupported systems."""
        mock_is_git.return_value = True
        mock_detect.return_value = "unsupported"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["schedule", "add", "test-task", "deepwork sync", "--path", str(temp_dir)],
        )

        assert result.exit_code == 1
        assert "Unsupported system" in result.output
