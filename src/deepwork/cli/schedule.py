"""Schedule command for DeepWork CLI."""

import html
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import click
from rich.console import Console

from deepwork.utils.git import is_git_repo

console = Console()


class ScheduleError(Exception):
    """Exception raised for scheduling errors."""

    pass


def _validate_task_name(task_name: str) -> None:
    """
    Validate that task name contains only safe characters.

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


def _detect_system() -> str:
    """
    Detect the system scheduler type.

    Returns:
        'systemd' for Linux with systemd, 'launchd' for macOS, or 'unsupported'
    """
    system = platform.system()

    if system == "Darwin":
        return "launchd"
    elif system == "Linux":
        # Check if systemd is available
        if shutil.which("systemctl"):
            return "systemd"
        return "unsupported"
    else:
        return "unsupported"


def _create_systemd_service(
    task_name: str, command: str, project_path: Path, interval: str
) -> tuple[str, str]:
    """
    Create systemd service and timer content.

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

    # Use sh -c to properly handle complex commands
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


def _create_launchd_plist(
    task_name: str, command: str, project_path: Path, interval: int
) -> str:
    """
    Create launchd plist content.

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

    # Parse command properly using shlex to handle quoted arguments
    try:
        command_parts = shlex.split(command)
    except ValueError as e:
        raise ScheduleError(f"Invalid command syntax: {e}") from e

    if not command_parts:
        raise ValueError("Command cannot be empty")

    # Escape each argument for XML
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


def _install_systemd_timer(
    task_name: str, command: str, project_path: Path, interval: str, user_mode: bool = True
) -> None:
    """
    Install systemd service and timer.

    Args:
        task_name: Name of the scheduled task
        command: Command to execute
        project_path: Path to the project directory
        interval: Systemd timer interval
        user_mode: If True, install as user service, else system service

    Raises:
        ScheduleError: If installation fails
    """
    service_name = f"deepwork-{task_name}"
    service_content, timer_content = _create_systemd_service(
        task_name, command, project_path, interval
    )

    # Determine systemd directory
    if user_mode:
        systemd_dir = Path.home() / ".config" / "systemd" / "user"
    else:
        systemd_dir = Path("/etc/systemd/system")

    systemd_dir.mkdir(parents=True, exist_ok=True)

    # Write service file
    service_file = systemd_dir / f"{service_name}.service"
    service_file.write_text(service_content)
    console.print(f"  [green]✓[/green] Created {service_file}")

    # Write timer file
    timer_file = systemd_dir / f"{service_name}.timer"
    timer_file.write_text(timer_content)
    console.print(f"  [green]✓[/green] Created {timer_file}")

    # Reload systemd and enable timer
    try:
        systemctl_cmd = ["systemctl"]
        if user_mode:
            systemctl_cmd.append("--user")

        subprocess.run([*systemctl_cmd, "daemon-reload"], check=True, capture_output=True)
        subprocess.run(
            [*systemctl_cmd, "enable", f"{service_name}.timer"], check=True, capture_output=True
        )
        subprocess.run(
            [*systemctl_cmd, "start", f"{service_name}.timer"], check=True, capture_output=True
        )
        console.print(f"  [green]✓[/green] Enabled and started {service_name}.timer")
    except subprocess.CalledProcessError as e:
        raise ScheduleError(f"Failed to enable systemd timer: {e.stderr.decode()}") from e


def _install_launchd_agent(
    task_name: str, command: str, project_path: Path, interval: int
) -> None:
    """
    Install launchd agent.

    Args:
        task_name: Name of the scheduled task
        command: Command to execute
        project_path: Path to the project directory
        interval: Interval in seconds

    Raises:
        ScheduleError: If installation fails
    """
    label = f"com.deepwork.{task_name}"
    plist_content = _create_launchd_plist(task_name, command, project_path, interval)

    # LaunchAgents directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    # Write plist file
    plist_file = launch_agents_dir / f"{label}.plist"
    plist_file.write_text(plist_content)
    console.print(f"  [green]✓[/green] Created {plist_file}")

    # Ensure logs directory exists
    logs_dir = project_path / ".deepwork" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Load the agent
    try:
        subprocess.run(["launchctl", "load", str(plist_file)], check=True, capture_output=True)
        console.print(f"  [green]✓[/green] Loaded {label}")
    except subprocess.CalledProcessError as e:
        raise ScheduleError(f"Failed to load launchd agent: {e.stderr.decode()}") from e


def _uninstall_systemd_timer(task_name: str, user_mode: bool = True) -> None:
    """
    Uninstall systemd service and timer.

    Args:
        task_name: Name of the scheduled task
        user_mode: If True, uninstall from user services, else system services

    Raises:
        ScheduleError: If uninstallation fails
    """
    service_name = f"deepwork-{task_name}"

    # Determine systemd directory
    if user_mode:
        systemd_dir = Path.home() / ".config" / "systemd" / "user"
    else:
        systemd_dir = Path("/etc/systemd/system")

    systemctl_cmd = ["systemctl"]
    if user_mode:
        systemctl_cmd.append("--user")

    # Stop and disable timer (ignore errors as timer may not exist)
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
        # systemctl may not be available or file system errors - continue cleanup
        console.print(f"  [dim]•[/dim] Could not stop timer: {e}")

    # Remove files
    service_file = systemd_dir / f"{service_name}.service"
    timer_file = systemd_dir / f"{service_name}.timer"

    if service_file.exists():
        service_file.unlink()
        console.print(f"  [green]✓[/green] Removed {service_file}")

    if timer_file.exists():
        timer_file.unlink()
        console.print(f"  [green]✓[/green] Removed {timer_file}")

    # Reload systemd
    try:
        subprocess.run([*systemctl_cmd, "daemon-reload"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass


def _uninstall_launchd_agent(task_name: str) -> None:
    """
    Uninstall launchd agent.

    Args:
        task_name: Name of the scheduled task

    Raises:
        ScheduleError: If uninstallation fails
    """
    label = f"com.deepwork.{task_name}"
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = launch_agents_dir / f"{label}.plist"

    # Unload the agent (ignore errors as agent may not be loaded)
    try:
        subprocess.run(["launchctl", "unload", str(plist_file)], check=False, capture_output=True)
        console.print(f"  [green]✓[/green] Unloaded {label}")
    except (FileNotFoundError, OSError) as e:
        # launchctl may not be available or file system errors - continue cleanup
        console.print(f"  [dim]•[/dim] Could not unload agent: {e}")

    # Remove plist file
    if plist_file.exists():
        plist_file.unlink()
        console.print(f"  [green]✓[/green] Removed {plist_file}")


@click.group()
def schedule() -> None:
    """Manage scheduled DeepWork jobs."""
    pass


@schedule.command()
@click.argument("task_name")
@click.argument("command")
@click.option(
    "--interval",
    "-i",
    default="daily",
    help="Schedule interval (systemd: 'daily', 'weekly', 'hourly'; launchd: seconds)",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def add(task_name: str, command: str, interval: str, path: Path) -> None:
    """
    Schedule a task to run periodically.

    TASK_NAME is a unique name for this scheduled task.
    COMMAND is the command to run (e.g., 'deepwork sync').
    """
    try:
        _add_schedule(task_name, command, interval, path)
    except ScheduleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


def _add_schedule(task_name: str, command: str, interval: str, project_path: Path) -> None:
    """
    Add a scheduled task.

    Args:
        task_name: Name of the scheduled task
        command: Command to execute
        interval: Schedule interval
        project_path: Path to the project directory

    Raises:
        ScheduleError: If scheduling fails
    """
    console.print(f"\n[bold cyan]Scheduling DeepWork task: {task_name}[/bold cyan]\n")

    # Check if project has DeepWork installed (optional, just check if it's a git repo)
    if not is_git_repo(project_path):
        raise ScheduleError("Not a Git repository. DeepWork requires a Git repository.")

    deepwork_dir = project_path / ".deepwork"
    if not deepwork_dir.exists():
        console.print(
            "[yellow]Warning:[/yellow] DeepWork not installed in this project. "
            "The scheduled command may not work correctly."
        )

    # Detect system
    system_type = _detect_system()
    console.print(f"[yellow]→[/yellow] Detected system: {system_type}")

    if system_type == "unsupported":
        raise ScheduleError(
            "Unsupported system. DeepWork scheduling requires systemd (Linux) or launchd (macOS)."
        )

    # Install based on system type
    if system_type == "systemd":
        console.print("[yellow]→[/yellow] Installing systemd timer...")
        _install_systemd_timer(task_name, command, project_path, interval)
    elif system_type == "launchd":
        # Convert interval to seconds for launchd
        try:
            interval_seconds = int(interval)
        except ValueError as e:
            # Map common intervals to seconds
            interval_map = {
                "hourly": 3600,
                "daily": 86400,
                "weekly": 604800,
                "monthly": 2592000,  # 30 days
            }
            if interval.lower() not in interval_map:
                raise ScheduleError(
                    f"Invalid interval '{interval}'. "
                    f"Valid options are: {', '.join(interval_map.keys())}, "
                    "or a number of seconds."
                ) from e
            interval_seconds = interval_map[interval.lower()]

        console.print("[yellow]→[/yellow] Installing launchd agent...")
        _install_launchd_agent(task_name, command, project_path, interval_seconds)

    console.print()
    console.print(f"[bold green]✓ Task '{task_name}' scheduled successfully![/bold green]")
    console.print()


@schedule.command()
@click.argument("task_name")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def remove(task_name: str, path: Path) -> None:
    """
    Remove a scheduled task.

    TASK_NAME is the name of the task to unschedule.
    """
    try:
        _remove_schedule(task_name, path)
    except ScheduleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


def _remove_schedule(task_name: str, project_path: Path) -> None:
    """
    Remove a scheduled task.

    Args:
        task_name: Name of the scheduled task to unschedule
        project_path: Path to the project directory

    Raises:
        ScheduleError: If unscheduling fails
    """
    console.print(f"\n[bold cyan]Removing scheduled task: {task_name}[/bold cyan]\n")

    # Detect system
    system_type = _detect_system()
    console.print(f"[yellow]→[/yellow] Detected system: {system_type}")

    if system_type == "unsupported":
        raise ScheduleError(
            "Unsupported system. DeepWork scheduling requires systemd (Linux) or launchd (macOS)."
        )

    # Uninstall based on system type
    if system_type == "systemd":
        console.print("[yellow]→[/yellow] Removing systemd timer...")
        _uninstall_systemd_timer(task_name)
    elif system_type == "launchd":
        console.print("[yellow]→[/yellow] Removing launchd agent...")
        _uninstall_launchd_agent(task_name)

    console.print()
    console.print(f"[bold green]✓ Task '{task_name}' unscheduled successfully![/bold green]")
    console.print()


@schedule.command()
def list() -> None:
    """List all scheduled DeepWork tasks."""
    console.print("\n[bold cyan]Scheduled DeepWork Tasks[/bold cyan]\n")

    system_type = _detect_system()
    console.print(f"System: {system_type}\n")

    if system_type == "systemd":
        _list_systemd_timers()
    elif system_type == "launchd":
        _list_launchd_agents()
    else:
        console.print("[yellow]No scheduled tasks (unsupported system)[/yellow]")


def _list_systemd_timers() -> None:
    """List systemd timers for DeepWork tasks."""
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


def _list_launchd_agents() -> None:
    """List launchd agents for DeepWork tasks."""
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"

    if not launch_agents_dir.exists():
        console.print("[dim]No scheduled DeepWork tasks found[/dim]")
        return

    plist_files = list(launch_agents_dir.glob("com.deepwork.*.plist"))

    if plist_files:
        for plist_file in plist_files:
            task_name = plist_file.stem.replace("com.deepwork.", "")
            console.print(f"  [green]✓[/green] {task_name} ({plist_file.name})")
    else:
        console.print("[dim]No scheduled DeepWork tasks found[/dim]")
