"""Tests for schedule runners."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from deepwork.cli.runners import (
    LaunchdRunner,
    ScheduleError,
    ScheduleRunner,
    SystemdRunner,
    _validate_task_name,
)


class TestValidateTaskName:
    """Tests for task name validation."""

    def test_valid_task_names(self) -> None:
        valid_names = ["test-task", "task_name", "task123", "my-task-123_test"]
        for name in valid_names:
            _validate_task_name(name)  # Should not raise

    def test_invalid_task_names(self) -> None:
        invalid_names = [
            "task name",
            "task@name",
            "task/name",
            "task.name",
            "task:name",
        ]
        for name in invalid_names:
            with pytest.raises(ScheduleError, match="Invalid task name"):
                _validate_task_name(name)


class TestScheduleRunnerRegistry:
    """Tests for runner auto-registration and detection."""

    def test_systemd_registered(self) -> None:
        assert "systemd" in ScheduleRunner.get_all()

    def test_launchd_registered(self) -> None:
        assert "launchd" in ScheduleRunner.get_all()

    def test_get_systemd(self) -> None:
        assert ScheduleRunner.get("systemd") is SystemdRunner

    def test_get_launchd(self) -> None:
        assert ScheduleRunner.get("launchd") is LaunchdRunner

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(ScheduleError, match="Unknown runner"):
            ScheduleRunner.get("nonexistent")

    @patch("deepwork.cli.runners.platform.system", return_value="Linux")
    @patch("deepwork.cli.runners.shutil.which", return_value="/usr/bin/systemctl")
    def test_detect_runner_linux_systemd(self, _which: Mock, _system: Mock) -> None:
        runner = ScheduleRunner.detect_runner()
        assert runner is not None
        assert isinstance(runner, SystemdRunner)

    @patch("deepwork.cli.runners.platform.system", return_value="Darwin")
    def test_detect_runner_macos(self, _system: Mock) -> None:
        runner = ScheduleRunner.detect_runner()
        assert runner is not None
        assert isinstance(runner, LaunchdRunner)

    @patch("deepwork.cli.runners.platform.system", return_value="Windows")
    @patch("deepwork.cli.runners.shutil.which", return_value=None)
    def test_detect_runner_unsupported(self, _which: Mock, _system: Mock) -> None:
        runner = ScheduleRunner.detect_runner()
        assert runner is None


class TestSystemdRunner:
    """Tests for SystemdRunner."""

    @patch("deepwork.cli.runners.platform.system", return_value="Linux")
    @patch("deepwork.cli.runners.shutil.which", return_value="/usr/bin/systemctl")
    def test_detect_linux_with_systemctl(self, _which: Mock, _system: Mock) -> None:
        assert SystemdRunner.detect() is True

    @patch("deepwork.cli.runners.platform.system", return_value="Linux")
    @patch("deepwork.cli.runners.shutil.which", return_value=None)
    def test_detect_linux_without_systemctl(self, _which: Mock, _system: Mock) -> None:
        assert SystemdRunner.detect() is False

    @patch("deepwork.cli.runners.platform.system", return_value="Darwin")
    def test_detect_not_linux(self, _system: Mock) -> None:
        assert SystemdRunner.detect() is False

    def test_create_service_config_basic(self, temp_dir: Path) -> None:
        service, timer = SystemdRunner.create_service_config(
            "test-task", "deepwork sync", temp_dir, "daily"
        )

        assert "Description=DeepWork task: test-task" in service
        assert f"WorkingDirectory={temp_dir}" in service
        assert "ExecStart=/bin/sh -c" in service
        assert "Type=oneshot" in service

        assert "Description=Timer for DeepWork task: test-task" in timer
        assert "OnCalendar=daily" in timer
        assert "Persistent=true" in timer
        assert "Requires=deepwork-test-task.service" in timer

    def test_create_service_config_intervals(self, temp_dir: Path) -> None:
        for interval in ["hourly", "weekly", "monthly"]:
            _, timer = SystemdRunner.create_service_config(
                "test-task", "echo test", temp_dir, interval
            )
            assert f"OnCalendar={interval}" in timer

    def test_create_service_config_invalid_name(self, temp_dir: Path) -> None:
        with pytest.raises(ScheduleError, match="Invalid task name"):
            SystemdRunner.create_service_config("test task", "echo test", temp_dir, "daily")


class TestLaunchdRunner:
    """Tests for LaunchdRunner."""

    @patch("deepwork.cli.runners.platform.system", return_value="Darwin")
    def test_detect_macos(self, _system: Mock) -> None:
        assert LaunchdRunner.detect() is True

    @patch("deepwork.cli.runners.platform.system", return_value="Linux")
    def test_detect_not_macos(self, _system: Mock) -> None:
        assert LaunchdRunner.detect() is False

    def test_parse_interval_numeric(self) -> None:
        assert LaunchdRunner.parse_interval("3600") == 3600

    def test_parse_interval_named(self) -> None:
        assert LaunchdRunner.parse_interval("hourly") == 3600
        assert LaunchdRunner.parse_interval("daily") == 86400
        assert LaunchdRunner.parse_interval("weekly") == 604800
        assert LaunchdRunner.parse_interval("monthly") == 2592000

    def test_parse_interval_case_insensitive(self) -> None:
        assert LaunchdRunner.parse_interval("Daily") == 86400
        assert LaunchdRunner.parse_interval("HOURLY") == 3600

    def test_parse_interval_invalid(self) -> None:
        with pytest.raises(ScheduleError, match="Invalid interval"):
            LaunchdRunner.parse_interval("invalid")

    def test_create_plist_basic(self, temp_dir: Path) -> None:
        plist = LaunchdRunner.create_plist("test-task", "deepwork sync", temp_dir, 86400)

        assert "<key>Label</key>" in plist
        assert "<string>com.deepwork.test-task</string>" in plist
        assert "<key>ProgramArguments</key>" in plist
        assert "<string>deepwork</string>" in plist
        assert "<string>sync</string>" in plist
        assert f"<string>{temp_dir}</string>" in plist
        assert "<key>StartInterval</key>" in plist
        assert "<integer>86400</integer>" in plist

    def test_create_plist_complex_command(self, temp_dir: Path) -> None:
        plist = LaunchdRunner.create_plist("test-task", "git fetch origin main", temp_dir, 3600)

        assert "<string>git</string>" in plist
        assert "<string>fetch</string>" in plist
        assert "<string>origin</string>" in plist
        assert "<string>main</string>" in plist

    def test_create_plist_quoted_arguments(self, temp_dir: Path) -> None:
        plist = LaunchdRunner.create_plist(
            "test-task", 'git commit -m "My commit message"', temp_dir, 3600
        )

        assert "<string>git</string>" in plist
        assert "<string>commit</string>" in plist
        assert "<string>-m</string>" in plist
        assert "<string>My commit message</string>" in plist

    def test_create_plist_xml_escaping(self, temp_dir: Path) -> None:
        plist = LaunchdRunner.create_plist(
            "test-task", 'echo "test <tag> & more"', temp_dir, 3600
        )

        assert "&lt;tag&gt; &amp; more" in plist

    def test_create_plist_logs_path(self, temp_dir: Path) -> None:
        plist = LaunchdRunner.create_plist("test-task", "echo test", temp_dir, 3600)

        assert "<key>StandardOutPath</key>" in plist
        assert f"<string>{temp_dir}/.deepwork/logs/test-task.log</string>" in plist
        assert "<key>StandardErrorPath</key>" in plist
        assert f"<string>{temp_dir}/.deepwork/logs/test-task.err</string>" in plist

    def test_create_plist_empty_command(self, temp_dir: Path) -> None:
        with pytest.raises(ValueError, match="Command cannot be empty"):
            LaunchdRunner.create_plist("test-task", "", temp_dir, 3600)

    def test_create_plist_invalid_name(self, temp_dir: Path) -> None:
        with pytest.raises(ScheduleError, match="Invalid task name"):
            LaunchdRunner.create_plist("test task", "echo test", temp_dir, 3600)
