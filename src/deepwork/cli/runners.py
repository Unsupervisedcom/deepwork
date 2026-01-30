"""Schedule runners for DeepWork CLI.

Each runner represents a platform-specific execution backend for scheduled tasks
(e.g., systemd timers on Linux, launchd agents on macOS). Runners auto-register
via __init_subclass__, following the same pattern as AgentAdapter.
"""

from __future__ import annotations

import html
import platform
import re
import shlex
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from rich.console import Console

console = Console()


class ScheduleError(Exception):
    """Exception raised for scheduling errors."""

    pass


def _validate_task_name(task_name: str) -> None:
    """Validate that task name contains only safe characters.

    Args:
        task_name: Name to validate

    Raises:
        ScheduleError: If task name contains unsafe characters
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', task_name):
        raise ScheduleError(
            f"Invalid task name '{task_name}'. "
            "Task names must contain only alphanumeric characters, hyphens, and underscores."
        )


class ScheduleRunner(ABC):
    """Base class for schedule runners.

    Subclasses are automatically registered when defined, enabling dynamic
    discovery of available scheduling backends.
    """

    _registry: ClassVar[dict[str, type[ScheduleRunner]]] = {}

    name: ClassVar[str]
    display_name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Auto-register subclasses."""
        super().__init_subclass__(**kwargs)
        if "name" in cls.__dict__ and cls.name:
            ScheduleRunner._registry[cls.name] = cls

    @classmethod
    def get_all(cls) -> dict[str, type[ScheduleRunner]]:
        """Return all registered runner classes."""
        return cls._registry.copy()

    @classmethod
    def get(cls, name: str) -> type[ScheduleRunner]:
        """Get runner class by name.

        Raises:
            ScheduleError: If runner name is not registered
        """
        if name not in cls._registry:
            raise ScheduleError(
                f"Unknown runner '{name}'. "
                f"Available runners: {', '.join(cls._registry.keys())}"
            )
        return cls._registry[name]

    @classmethod
    def detect_runner(cls) -> ScheduleRunner | None:
        """Detect and return a runner instance for the current system.

        Returns:
            A runner instance, or None if no runner supports this system.
        """
        for runner_cls in cls._registry.values():
            if runner_cls.detect():
                return runner_cls()
        return None

    @staticmethod
    @abstractmethod
    def detect() -> bool:
        """Check if this runner can operate on the current system."""

    @abstractmethod
    def install(self, task_name: str, command: str, project_path: Path, interval: str) -> None:
        """Install a scheduled task.

        Args:
            task_name: Unique name for the task (alphanumeric, hyphens, underscores)
            command: Command to execute
            project_path: Path to the project directory
            interval: Schedule interval (e.g., 'daily', 'hourly', or seconds)

        Raises:
            ScheduleError: If installation fails
        """

    @abstractmethod
    def uninstall(self, task_name: str) -> None:
        """Remove a scheduled task.

        Args:
            task_name: Name of the task to remove

        Raises:
            ScheduleError: If removal fails
        """

    @abstractmethod
    def list_tasks(self) -> None:
        """List scheduled tasks for this runner."""


class SystemdRunner(ScheduleRunner):
    """Runner for systemd timers on Linux."""

    name = "systemd"
    display_name = "Systemd Timer"

    @staticmethod
    def detect() -> bool:
        return platform.system() == "Linux" and shutil.which("systemctl") is not None

    @staticmethod
    def create_service_config(
        task_name: str, command: str, project_path: Path, interval: str
    ) -> tuple[str, str]:
        """Create systemd service and timer unit file contents.

        Args:
            task_name: Name of the scheduled task (must be validated)
            command: Command to execute (will be shell-escaped)
            project_path: Path to the project directory
            interval: Systemd timer interval (e.g., 'daily', 'weekly', 'hourly')

        Returns:
            Tuple of (service_content, timer_content)
        """
        _validate_task_name(task_name)
        service_name = f"deepwork-{task_name}"
        safe_command = shlex.quote(command)

        service_content = f"""[Unit]
Description=DeepWork task: {task_name}
After=network.target

[Service]
Type=oneshot
WorkingDirectory={project_path}
ExecStart=/bin/sh -c {safe_command}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

        timer_content = f"""[Unit]
Description=Timer for DeepWork task: {task_name}
Requires={service_name}.service

[Timer]
OnCalendar={interval}
Persistent=true

[Install]
WantedBy=timers.target
"""

        return service_content, timer_content

    def install(
        self,
        task_name: str,
        command: str,
        project_path: Path,
        interval: str,
        user_mode: bool = True,
    ) -> None:
        service_name = f"deepwork-{task_name}"
        service_content, timer_content = self.create_service_config(
            task_name, command, project_path, interval
        )

        if user_mode:
            systemd_dir = Path.home() / ".config" / "systemd" / "user"
        else:
            systemd_dir = Path("/etc/systemd/system")

        systemd_dir.mkdir(parents=True, exist_ok=True)

        service_file = systemd_dir / f"{service_name}.service"
        service_file.write_text(service_content)
        console.print(f"  [green]✓[/green] Created {service_file}")

        timer_file = systemd_dir / f"{service_name}.timer"
        timer_file.write_text(timer_content)
        console.print(f"  [green]✓[/green] Created {timer_file}")

        try:
            systemctl_cmd = ["systemctl"]
            if user_mode:
                systemctl_cmd.append("--user")

            subprocess.run([*systemctl_cmd, "daemon-reload"], check=True, capture_output=True)
            subprocess.run(
                [*systemctl_cmd, "enable", f"{service_name}.timer"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [*systemctl_cmd, "start", f"{service_name}.timer"],
                check=True,
                capture_output=True,
            )
            console.print(f"  [green]✓[/green] Enabled and started {service_name}.timer")
        except subprocess.CalledProcessError as e:
            raise ScheduleError(f"Failed to enable systemd timer: {e.stderr.decode()}") from e

    def uninstall(self, task_name: str, user_mode: bool = True) -> None:
        service_name = f"deepwork-{task_name}"

        if user_mode:
            systemd_dir = Path.home() / ".config" / "systemd" / "user"
        else:
            systemd_dir = Path("/etc/systemd/system")

        systemctl_cmd = ["systemctl"]
        if user_mode:
            systemctl_cmd.append("--user")

        try:
            subprocess.run(
                [*systemctl_cmd, "stop", f"{service_name}.timer"],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                [*systemctl_cmd, "disable", f"{service_name}.timer"],
                check=False,
                capture_output=True,
            )
            console.print(f"  [green]✓[/green] Stopped and disabled {service_name}.timer")
        except (FileNotFoundError, OSError) as e:
            console.print(f"  [dim]•[/dim] Could not stop timer: {e}")

        service_file = systemd_dir / f"{service_name}.service"
        timer_file = systemd_dir / f"{service_name}.timer"

        if service_file.exists():
            service_file.unlink()
            console.print(f"  [green]✓[/green] Removed {service_file}")

        if timer_file.exists():
            timer_file.unlink()
            console.print(f"  [green]✓[/green] Removed {timer_file}")

        try:
            subprocess.run([*systemctl_cmd, "daemon-reload"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass

    def list_tasks(self) -> None:
        try:
            result = subprocess.run(
                ["systemctl", "--user", "list-timers", "--all"],
                capture_output=True,
                text=True,
                check=True,
            )

            lines = result.stdout.split("\n")
            deepwork_timers = [line for line in lines if "deepwork-" in line]

            if deepwork_timers:
                for line in deepwork_timers:
                    console.print(f"  {line}")
            else:
                console.print("[dim]No scheduled DeepWork tasks found[/dim]")
        except subprocess.CalledProcessError:
            console.print("[yellow]Failed to list systemd timers[/yellow]")


class LaunchdRunner(ScheduleRunner):
    """Runner for launchd agents on macOS."""

    name = "launchd"
    display_name = "macOS LaunchAgent"

    INTERVAL_MAP: ClassVar[dict[str, int]] = {
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
        "monthly": 2592000,
    }

    @staticmethod
    def detect() -> bool:
        return platform.system() == "Darwin"

    @staticmethod
    def parse_interval(interval: str) -> int:
        """Parse an interval string into seconds.

        Args:
            interval: Interval as seconds (numeric) or named ('hourly', 'daily', etc.)

        Returns:
            Interval in seconds

        Raises:
            ScheduleError: If interval is invalid
        """
        try:
            return int(interval)
        except ValueError:
            pass

        key = interval.lower()
        if key not in LaunchdRunner.INTERVAL_MAP:
            raise ScheduleError(
                f"Invalid interval '{interval}'. "
                f"Valid options are: {', '.join(LaunchdRunner.INTERVAL_MAP.keys())}, "
                "or a number of seconds."
            )
        return LaunchdRunner.INTERVAL_MAP[key]

    @staticmethod
    def create_plist(task_name: str, command: str, project_path: Path, interval: int) -> str:
        """Create launchd plist content.

        Args:
            task_name: Name of the scheduled task (must be validated)
            command: Command to execute (will be parsed and escaped)
            project_path: Path to the project directory
            interval: Interval in seconds

        Returns:
            Plist XML content
        """
        _validate_task_name(task_name)
        label = f"com.deepwork.{task_name}"

        try:
            command_parts = shlex.split(command)
        except ValueError as e:
            raise ScheduleError(f"Invalid command syntax: {e}") from e

        if not command_parts:
            raise ValueError("Command cannot be empty")

        escaped_args = [html.escape(arg) for arg in command_parts]
        args_xml = "\n        ".join(f"<string>{arg}</string>" for arg in escaped_args)

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>
    <array>
        {args_xml}
    </array>

    <key>WorkingDirectory</key>
    <string>{project_path}</string>

    <key>StartInterval</key>
    <integer>{interval}</integer>

    <key>StandardOutPath</key>
    <string>{project_path}/.deepwork/logs/{task_name}.log</string>

    <key>StandardErrorPath</key>
    <string>{project_path}/.deepwork/logs/{task_name}.err</string>
</dict>
</plist>
"""

        return plist_content

    def install(self, task_name: str, command: str, project_path: Path, interval: str) -> None:
        interval_seconds = self.parse_interval(interval)
        label = f"com.deepwork.{task_name}"
        plist_content = self.create_plist(task_name, command, project_path, interval_seconds)

        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(parents=True, exist_ok=True)

        plist_file = launch_agents_dir / f"{label}.plist"
        plist_file.write_text(plist_content)
        console.print(f"  [green]✓[/green] Created {plist_file}")

        logs_dir = project_path / ".deepwork" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["launchctl", "load", str(plist_file)], check=True, capture_output=True
            )
            console.print(f"  [green]✓[/green] Loaded {label}")
        except subprocess.CalledProcessError as e:
            raise ScheduleError(f"Failed to load launchd agent: {e.stderr.decode()}") from e

    def uninstall(self, task_name: str) -> None:
        label = f"com.deepwork.{task_name}"
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_file = launch_agents_dir / f"{label}.plist"

        try:
            subprocess.run(
                ["launchctl", "unload", str(plist_file)], check=False, capture_output=True
            )
            console.print(f"  [green]✓[/green] Unloaded {label}")
        except (FileNotFoundError, OSError) as e:
            console.print(f"  [dim]•[/dim] Could not unload agent: {e}")

        if plist_file.exists():
            plist_file.unlink()
            console.print(f"  [green]✓[/green] Removed {plist_file}")

    def list_tasks(self) -> None:
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"

        if not launch_agents_dir.exists():
            console.print("[dim]No scheduled DeepWork tasks found[/dim]")
            return

        plist_files = sorted(launch_agents_dir.glob("com.deepwork.*.plist"))

        if plist_files:
            for plist_file in plist_files:
                task_name = plist_file.stem.replace("com.deepwork.", "")
                console.print(f"  [green]✓[/green] {task_name} ({plist_file.name})")
        else:
            console.print("[dim]No scheduled DeepWork tasks found[/dim]")
