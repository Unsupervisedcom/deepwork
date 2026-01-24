"""Tests for schedule command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from deepwork.cli.schedule import (
    ScheduleError,
    _create_launchd_plist,
    _create_systemd_service,
    _detect_system,
)


class TestDetectSystem:
    """Tests for system detection."""

    @patch("platform.system")
    @patch("shutil.which")
    def test_detect_darwin(self, mock_which: Mock, mock_system: Mock) -> None:
        """Test detecting macOS."""
        mock_system.return_value = "Darwin"
        assert _detect_system() == "launchd"

    @patch("platform.system")
    @patch("shutil.which")
    def test_detect_linux_with_systemd(self, mock_which: Mock, mock_system: Mock) -> None:
        """Test detecting Linux with systemd."""
        mock_system.return_value = "Linux"
        mock_which.return_value = "/usr/bin/systemctl"
        assert _detect_system() == "systemd"

    @patch("platform.system")
    @patch("shutil.which")
    def test_detect_linux_without_systemd(self, mock_which: Mock, mock_system: Mock) -> None:
        """Test detecting Linux without systemd."""
        mock_system.return_value = "Linux"
        mock_which.return_value = None
        assert _detect_system() == "unsupported"

    @patch("platform.system")
    def test_detect_unsupported_system(self, mock_system: Mock) -> None:
        """Test detecting unsupported system."""
        mock_system.return_value = "Windows"
        assert _detect_system() == "unsupported"


class TestCreateSystemdService:
    """Tests for systemd service and timer generation."""

    def test_create_systemd_service_basic(self, temp_dir: Path) -> None:
        """Test creating basic systemd service and timer."""
        task_name = "test-task"
        command = "deepwork sync"
        interval = "daily"

        service_content, timer_content = _create_systemd_service(
            task_name, command, temp_dir, interval
        )

        # Check service content
        assert "Description=DeepWork task: test-task" in service_content
        assert f"WorkingDirectory={temp_dir}" in service_content
        assert f"ExecStart={command}" in service_content
        assert "Type=oneshot" in service_content

        # Check timer content
        assert "Description=Timer for DeepWork task: test-task" in timer_content
        assert "OnCalendar=daily" in timer_content
        assert "Persistent=true" in timer_content
        assert "Requires=deepwork-test-task.service" in timer_content

    def test_create_systemd_service_with_different_intervals(self, temp_dir: Path) -> None:
        """Test creating systemd timer with different intervals."""
        for interval in ["hourly", "weekly", "monthly"]:
            _, timer_content = _create_systemd_service(
                "test-task", "echo test", temp_dir, interval
            )
            assert f"OnCalendar={interval}" in timer_content


class TestCreateLaunchdPlist:
    """Tests for launchd plist generation."""

    def test_create_launchd_plist_basic(self, temp_dir: Path) -> None:
        """Test creating basic launchd plist."""
        task_name = "test-task"
        command = "deepwork sync"
        interval = 86400  # daily in seconds

        plist_content = _create_launchd_plist(task_name, command, temp_dir, interval)

        # Check plist content
        assert "<key>Label</key>" in plist_content
        assert "<string>com.deepwork.test-task</string>" in plist_content
        assert "<key>ProgramArguments</key>" in plist_content
        assert "<string>deepwork</string>" in plist_content
        assert "<string>sync</string>" in plist_content
        assert f"<string>{temp_dir}</string>" in plist_content
        assert "<key>StartInterval</key>" in plist_content
        assert "<integer>86400</integer>" in plist_content

    def test_create_launchd_plist_with_complex_command(self, temp_dir: Path) -> None:
        """Test creating launchd plist with multi-part command."""
        task_name = "test-task"
        command = "git fetch origin main"
        interval = 3600

        plist_content = _create_launchd_plist(task_name, command, temp_dir, interval)

        # Check that command is split correctly
        assert "<string>git</string>" in plist_content
        assert "<string>fetch</string>" in plist_content
        assert "<string>origin</string>" in plist_content
        assert "<string>main</string>" in plist_content

    def test_create_launchd_plist_logs_path(self, temp_dir: Path) -> None:
        """Test that launchd plist includes log paths."""
        plist_content = _create_launchd_plist(
            "test-task", "echo test", temp_dir, 3600
        )

        assert "<key>StandardOutPath</key>" in plist_content
        assert f"<string>{temp_dir}/.deepwork/logs/test-task.log</string>" in plist_content
        assert "<key>StandardErrorPath</key>" in plist_content
        assert f"<string>{temp_dir}/.deepwork/logs/test-task.err</string>" in plist_content


class TestScheduleAdd:
    """Tests for schedule add command."""

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    @patch("deepwork.cli.schedule._install_systemd_timer")
    def test_add_schedule_systemd(
        self,
        mock_install: Mock,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test adding a schedule on systemd."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = True
        mock_detect.return_value = "systemd"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

        mock_install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, "daily"
        )

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    @patch("deepwork.cli.schedule._install_launchd_agent")
    def test_add_schedule_launchd(
        self,
        mock_install: Mock,
        mock_is_git: Mock,
        mock_detect: Mock,
        temp_dir: Path,
    ) -> None:
        """Test adding a schedule on launchd."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = True
        mock_detect.return_value = "launchd"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

        # Daily should be converted to 86400 seconds
        mock_install.assert_called_once_with(
            "test-task", "deepwork sync", temp_dir, 86400
        )

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_not_git_repo(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test adding schedule fails when not a git repo."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = False

        with pytest.raises(ScheduleError, match="Not a Git repository"):
            _add_schedule("test-task", "deepwork sync", "daily", temp_dir)

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule.is_git_repo")
    def test_add_schedule_unsupported_system(
        self, mock_is_git: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test adding schedule fails on unsupported system."""
        from deepwork.cli.schedule import _add_schedule

        mock_is_git.return_value = True
        mock_detect.return_value = "unsupported"

        # Create .deepwork directory
        (temp_dir / ".deepwork").mkdir()

        with pytest.raises(ScheduleError, match="Unsupported system"):
            _add_schedule("test-task", "deepwork sync", "daily", temp_dir)


class TestScheduleRemove:
    """Tests for schedule remove command."""

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule._uninstall_systemd_timer")
    def test_remove_schedule_systemd(
        self, mock_uninstall: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test removing a schedule on systemd."""
        from deepwork.cli.schedule import _remove_schedule

        mock_detect.return_value = "systemd"

        _remove_schedule("test-task", temp_dir)

        mock_uninstall.assert_called_once_with("test-task")

    @patch("deepwork.cli.schedule._detect_system")
    @patch("deepwork.cli.schedule._uninstall_launchd_agent")
    def test_remove_schedule_launchd(
        self, mock_uninstall: Mock, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test removing a schedule on launchd."""
        from deepwork.cli.schedule import _remove_schedule

        mock_detect.return_value = "launchd"

        _remove_schedule("test-task", temp_dir)

        mock_uninstall.assert_called_once_with("test-task")

    @patch("deepwork.cli.schedule._detect_system")
    def test_remove_schedule_unsupported_system(
        self, mock_detect: Mock, temp_dir: Path
    ) -> None:
        """Test removing schedule fails on unsupported system."""
        from deepwork.cli.schedule import _remove_schedule

        mock_detect.return_value = "unsupported"

        with pytest.raises(ScheduleError, match="Unsupported system"):
            _remove_schedule("test-task", temp_dir)
