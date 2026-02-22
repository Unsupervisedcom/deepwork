"""Claude Code CLI subprocess wrapper.

Runs Claude Code CLI as a subprocess with structured JSON output.
Always uses --json-schema for structured output conformance.

See doc/reference/calling_claude_in_print_mode.md for details on
proper CLI invocation with structured output.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


class ClaudeCLIError(Exception):
    """Exception raised for Claude CLI subprocess errors."""

    pass


class ClaudeCLI:
    """Runs Claude Code CLI as a subprocess with structured JSON output.

    Always requires a JSON schema - the structured output is returned
    as a parsed dict from the CLI's `structured_output` field.

    See doc/reference/calling_claude_in_print_mode.md for details on
    proper CLI invocation with structured output.
    """

    def __init__(
        self,
        timeout: int = 120,
        *,
        _test_command: list[str] | None = None,
    ):
        """Initialize Claude CLI wrapper.

        Args:
            timeout: Timeout in seconds for the subprocess
            _test_command: Internal testing only - override the subprocess command.
                          When set, skips adding --json-schema flag (test mock handles it).
        """
        self.timeout = timeout
        self._test_command = _test_command

    def _build_command(
        self,
        system_prompt: str,
        json_schema: dict[str, Any],
    ) -> list[str]:
        """Build the CLI command with proper flag ordering.

        Flags must come BEFORE `-p --` because:
        - `-p` expects a prompt argument immediately after
        - `--` marks the end of flags, everything after is the prompt
        - When piping via stdin, we use `-p --` to read from stdin

        Args:
            system_prompt: System prompt for the CLI
            json_schema: JSON schema for structured output

        Returns:
            Command list ready for subprocess execution
        """
        if self._test_command:
            return self._test_command + ["--system-prompt", system_prompt]

        schema_json = json.dumps(json_schema)
        return [
            "claude",
            "--print",
            "--output-format",
            "json",
            "--system-prompt",
            system_prompt,
            "--json-schema",
            schema_json,
            "-p",
            "--",
        ]

    def _parse_wrapper(self, response_text: str) -> dict[str, Any]:
        """Parse the Claude CLI JSON wrapper and extract structured_output.

        When using --print --output-format json --json-schema, Claude CLI returns
        a wrapper object with the structured output in the 'structured_output' field.

        Args:
            response_text: Raw JSON response from Claude CLI

        Returns:
            The parsed structured_output dict

        Raises:
            ClaudeCLIError: If response cannot be parsed
        """
        try:
            wrapper = json.loads(response_text.strip())

            if wrapper.get("is_error"):
                raise ClaudeCLIError(
                    f"Claude CLI returned error: {wrapper.get('result', 'Unknown error')}"
                )

            data: dict[str, Any] = wrapper.get("structured_output")
            if data is None:
                raise ClaudeCLIError(
                    "Claude CLI response missing 'structured_output' field. "
                    f"Response was: {response_text[:500]}..."
                )

            return data

        except json.JSONDecodeError as e:
            raise ClaudeCLIError(
                f"Failed to parse Claude CLI response as JSON: {e}\n"
                f"Response was: {response_text[:500]}..."
            ) from e

    async def run(
        self,
        prompt: str,
        system_prompt: str,
        json_schema: dict[str, Any],
        cwd: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Run Claude CLI and return the structured output.

        Args:
            prompt: The user prompt (piped via stdin)
            system_prompt: System instructions for the CLI
            json_schema: JSON schema enforcing structured output conformance
            cwd: Working directory for the subprocess
            timeout: Override instance timeout for this call (seconds).
                     If None, uses the instance default.

        Returns:
            The parsed structured_output dict from Claude CLI

        Raises:
            ClaudeCLIError: If the subprocess fails or output cannot be parsed
        """
        effective_timeout = timeout if timeout is not None else self.timeout
        cmd = self._build_command(system_prompt, json_schema)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=prompt.encode()),
                    timeout=effective_timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                raise ClaudeCLIError(
                    f"Claude CLI timed out after {effective_timeout} seconds"
                ) from None

            if process.returncode != 0:
                raise ClaudeCLIError(
                    f"Claude CLI failed with exit code {process.returncode}:\n"
                    f"stderr: {stderr.decode()}"
                )

            return self._parse_wrapper(stdout.decode())

        except FileNotFoundError as e:
            raise ClaudeCLIError("Claude CLI command not found: claude") from e
