"""HTTP sidecar server for tool requirements enforcement.

Runs as a daemon thread alongside the MCP server, providing HTTP endpoints
that the PreToolUse hook calls to check/appeal tool requirements.

Uses stdlib http.server — no external dependencies.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import logging
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from deepwork.tool_requirements.cache import ToolRequirementsCache
from deepwork.tool_requirements.engine import ToolRequirementsEngine
from deepwork.tool_requirements.evaluator import HaikuSubprocessEvaluator

logger = logging.getLogger("deepwork.tool_requirements")


class _SidecarHandler(BaseHTTPRequestHandler):
    """HTTP request handler for sidecar endpoints."""

    engine: ToolRequirementsEngine  # Injected by start_sidecar via type()

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            self._respond(400, {"error": "Invalid JSON body"})
            return

        if self.path == "/check":
            self._handle_check(data)
        elif self.path == "/appeal":
            self._handle_appeal(data)
        else:
            self._respond(404, {"error": f"Unknown endpoint: {self.path}"})

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine in a new event loop, ensuring cleanup."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _handle_check(self, data: dict[str, Any]) -> None:
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        if not tool_name:
            self._respond(400, {"error": "Missing tool_name"})
            return

        try:
            result = self._run_async(self.engine.check(tool_name, tool_input))
        except Exception as e:
            logger.exception("Error checking tool requirements")
            self._respond(
                500,
                {
                    "decision": "deny",
                    "reason": f"Tool requirements evaluation error: {e}",
                },
            )
            return

        self._respond(
            200,
            {
                "decision": "allow" if result.allowed else "deny",
                "reason": result.reason,
                "failed_checks": result.failed_checks,
            },
        )

    def _handle_appeal(self, data: dict[str, Any]) -> None:
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        justifications = data.get("policy_justification", {})

        if not tool_name:
            self._respond(400, {"error": "Missing tool_name"})
            return
        if not justifications:
            self._respond(400, {"error": "Missing policy_justification"})
            return

        try:
            result = self._run_async(
                self.engine.appeal(tool_name, tool_input, justifications)
            )
        except Exception as e:
            logger.exception("Error processing appeal")
            self._respond(
                500,
                {
                    "passed": False,
                    "reason": f"Appeal evaluation error: {e}",
                },
            )
            return

        self._respond(
            200,
            {
                "passed": result.passed,
                "reason": result.reason,
                "no_exception_blocked": result.no_exception_blocked,
            },
        )

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        response = json.dumps(body).encode("utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr logging — use our logger instead."""
        logger.debug("Sidecar: %s", format % args)


class SidecarInfo:
    """Information about a running sidecar server."""

    def __init__(self, pid: int, port: int, port_file: Path) -> None:
        self.pid = pid
        self.port = port
        self.port_file = port_file


def start_sidecar(project_root: Path) -> SidecarInfo:
    """Start the sidecar HTTP server in a daemon thread.

    Writes a port file to .deepwork/tmp/tool_req_sidecar/<PID>.json
    so the hook can discover and connect.

    Args:
        project_root: Project root directory.

    Returns:
        SidecarInfo with pid, port, and port file path.
    """
    # Build the engine
    engine = ToolRequirementsEngine(
        project_root=project_root,
        evaluator=HaikuSubprocessEvaluator(),
        cache=ToolRequirementsCache(),
    )

    # Create handler class with engine reference
    handler_class = type(
        "_BoundSidecarHandler",
        (_SidecarHandler,),
        {"engine": engine},
    )

    # Bind to random port on localhost
    server = HTTPServer(("127.0.0.1", 0), handler_class)
    port = server.server_address[1]
    pid = os.getpid()

    # Write port file
    sidecar_dir = project_root / ".deepwork" / "tmp" / "tool_req_sidecar"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    port_file = sidecar_dir / f"{pid}.json"
    port_file.write_text(json.dumps({"pid": pid, "port": port}))

    logger.info("Tool requirements sidecar started on port %d (PID %d)", port, pid)

    # Start server in daemon thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Cleanup on exit
    def cleanup() -> None:
        server.shutdown()
        port_file.unlink(missing_ok=True)
        # Clean up any session mapping files that point to this PID
        for f in sidecar_dir.glob("session_*.json"):
            try:
                data = json.loads(f.read_text())
                if data.get("pid") == pid:
                    f.unlink(missing_ok=True)
            except (json.JSONDecodeError, OSError):
                pass

    atexit.register(cleanup)

    return SidecarInfo(pid=pid, port=port, port_file=port_file)


def _is_safe_session_id(session_id: str) -> bool:
    """Validate that session_id is safe for use in filenames."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", session_id))


def register_session(project_root: Path, session_id: str) -> None:
    """Register a session-to-sidecar mapping.

    Called when the MCP server receives its first tool call with a session_id.
    Creates a session_<SESSION_ID>.json file pointing to this PID's sidecar.

    Args:
        project_root: Project root directory.
        session_id: The Claude Code session ID.
    """
    if not _is_safe_session_id(session_id):
        return

    pid = os.getpid()
    sidecar_dir = project_root / ".deepwork" / "tmp" / "tool_req_sidecar"

    # Read our own port file
    port_file = sidecar_dir / f"{pid}.json"
    if not port_file.exists():
        return

    try:
        data = json.loads(port_file.read_text())
    except (json.JSONDecodeError, OSError):
        return

    # Write session mapping
    session_file = sidecar_dir / f"session_{session_id}.json"
    session_file.write_text(json.dumps({"pid": pid, "port": data["port"]}))


def discover_sidecar(project_root: Path, session_id: str) -> dict[str, Any] | None:
    """Discover the sidecar server for a given session.

    Looks for a session-specific mapping first, then falls back to
    scanning PID-keyed port files for live processes.

    Args:
        project_root: Project root directory.
        session_id: The Claude Code session ID.

    Returns:
        Dict with "port" and "pid" keys, or None if no sidecar found.
    """
    sidecar_dir = Path(project_root) / ".deepwork" / "tmp" / "tool_req_sidecar"
    if not sidecar_dir.is_dir():
        return None

    # Try session-specific mapping first
    if session_id and _is_safe_session_id(session_id):
        session_file = sidecar_dir / f"session_{session_id}.json"
        info = _read_and_validate_port_file(session_file)
        if info is not None:
            return info

    # Fall back to scanning PID files
    for port_file in sidecar_dir.glob("[0-9]*.json"):
        info = _read_and_validate_port_file(port_file)
        if info is not None:
            return info

    return None


def _read_and_validate_port_file(port_file: Path) -> dict[str, Any] | None:
    """Read a port file and check if the PID is alive."""
    if not port_file.exists():
        return None

    try:
        data = json.loads(port_file.read_text())
        pid = data.get("pid")
        port = data.get("port")
        if not pid or not port:
            return None

        # Check if PID is alive
        os.kill(pid, 0)
        return {"pid": pid, "port": port}
    except (json.JSONDecodeError, OSError):
        # PID is dead or file is corrupt — clean up
        port_file.unlink(missing_ok=True)
        return None
