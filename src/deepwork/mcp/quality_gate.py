"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via subprocess) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import aiofiles

from deepwork.mcp.schemas import QualityCriteriaResult, QualityGateResult

# JSON Schema for quality gate response validation
QUALITY_GATE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["passed", "feedback"],
    "properties": {
        "passed": {"type": "boolean"},
        "feedback": {"type": "string"},
        "criteria_results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["criterion", "passed"],
                "properties": {
                    "criterion": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "feedback": {"type": ["string", "null"]},
                },
            },
        },
    },
}

# File separator format: 20 dashes, filename, 20 dashes
FILE_SEPARATOR = "-" * 20


class QualityGateError(Exception):
    """Exception raised for quality gate errors."""

    pass


class QualityGate:
    """Evaluates step outputs against quality criteria.

    Uses a subprocess to invoke a review agent (e.g., Claude CLI) that
    evaluates outputs and returns structured feedback.

    See doc/reference/calling_claude_in_print_mode.md for details on
    proper CLI invocation with structured output.
    """

    def __init__(
        self,
        timeout: int = 120,
        *,
        _test_command: list[str] | None = None,
    ):
        """Initialize quality gate.

        Args:
            timeout: Timeout in seconds for review agent
            _test_command: Internal testing only - override the subprocess command.
                          When set, skips adding --json-schema flag (test mock handles it).
        """
        self.timeout = timeout
        self._test_command = _test_command

    def _build_instructions(self, quality_criteria: list[str]) -> str:
        """Build the system instructions for the review agent.

        Args:
            quality_criteria: List of quality criteria to evaluate

        Returns:
            System instructions string
        """
        criteria_list = "\n".join(f"- {c}" for c in quality_criteria)

        return f"""You are a quality gate reviewer. Your job is to evaluate whether outputs meet the specified quality criteria.

## Quality Criteria to Evaluate

{criteria_list}

## Response Format

You must respond with JSON in this exact structure:
```json
{{
  "passed": true/false,
  "feedback": "Brief overall summary of evaluation",
  "criteria_results": [
    {{
      "criterion": "The criterion text",
      "passed": true/false,
      "feedback": "Specific feedback for this criterion (null if passed)"
    }}
  ]
}}
```

## Guidelines

- Be strict but fair
- Only mark a criterion as passed if it is clearly met
- Provide specific, actionable feedback for failed criteria
- The overall "passed" should be true only if ALL criteria pass"""

    async def _build_payload(
        self,
        outputs: list[str],
        project_root: Path,
    ) -> str:
        """Build the user prompt payload with file contents.

        Args:
            outputs: List of output file paths
            project_root: Project root path for reading files

        Returns:
            Formatted payload with file contents
        """
        output_sections: list[str] = []

        for output_path in outputs:
            full_path = project_root / output_path
            header = f"{FILE_SEPARATOR} {output_path} {FILE_SEPARATOR}"

            if full_path.exists():
                try:
                    async with aiofiles.open(full_path, encoding="utf-8") as f:
                        content = await f.read()
                    output_sections.append(f"{header}\n{content}")
                except Exception as e:
                    output_sections.append(f"{header}\n[Error reading file: {e}]")
            else:
                output_sections.append(f"{header}\n[File not found]")

        if not output_sections:
            return "[No output files provided]"

        return "\n\n".join(output_sections)

    def _parse_response(self, response_text: str) -> QualityGateResult:
        """Parse the review agent's response.

        When using --print --output-format json --json-schema, Claude CLI returns
        a wrapper object with the structured output in the 'structured_output' field.

        Args:
            response_text: Raw response from review agent (JSON wrapper)

        Returns:
            Parsed QualityGateResult

        Raises:
            QualityGateError: If response cannot be parsed
        """
        try:
            wrapper = json.loads(response_text.strip())

            # Check for errors in the wrapper
            if wrapper.get("is_error"):
                raise QualityGateError(
                    f"Review agent returned error: {wrapper.get('result', 'Unknown error')}"
                )

            # Extract structured_output - this is where --json-schema puts the result
            data = wrapper.get("structured_output")
            if data is None:
                raise QualityGateError(
                    "Review agent response missing 'structured_output' field. "
                    f"Response was: {response_text[:500]}..."
                )

            # Parse criteria results
            criteria_results = [
                QualityCriteriaResult(
                    criterion=cr.get("criterion", ""),
                    passed=cr.get("passed", False),
                    feedback=cr.get("feedback"),
                )
                for cr in data.get("criteria_results", [])
            ]

            return QualityGateResult(
                passed=data.get("passed", False),
                feedback=data.get("feedback", "No feedback provided"),
                criteria_results=criteria_results,
            )

        except json.JSONDecodeError as e:
            raise QualityGateError(
                f"Failed to parse review agent response as JSON: {e}\n"
                f"Response was: {response_text[:500]}..."
            ) from e
        except (ValueError, KeyError) as e:
            raise QualityGateError(
                f"Failed to extract quality gate result: {e}\n"
                f"Response was: {response_text[:500]}..."
            ) from e

    async def evaluate(
        self,
        quality_criteria: list[str],
        outputs: list[str],
        project_root: Path,
    ) -> QualityGateResult:
        """Evaluate step outputs against quality criteria.

        Args:
            quality_criteria: List of quality criteria to evaluate
            outputs: List of output file paths
            project_root: Project root path

        Returns:
            QualityGateResult with pass/fail and feedback

        Raises:
            QualityGateError: If evaluation fails
        """
        if not quality_criteria:
            # No criteria = auto-pass
            return QualityGateResult(
                passed=True,
                feedback="No quality criteria defined - auto-passing",
                criteria_results=[],
            )

        # Build system instructions and payload separately
        instructions = self._build_instructions(quality_criteria)
        payload = await self._build_payload(outputs, project_root)

        # Build command with proper flag ordering for Claude CLI
        # See doc/reference/calling_claude_in_print_mode.md for details
        #
        # Key insight: flags must come BEFORE `-p --` because:
        # - `-p` expects a prompt argument immediately after
        # - `--` marks the end of flags, everything after is the prompt
        # - When piping via stdin, we use `-p --` to read from stdin
        if self._test_command:
            # Testing mode: use provided command, add system prompt only
            full_cmd = self._test_command + ["--system-prompt", instructions]
        else:
            # Production mode: use Claude CLI with proper flags
            schema_json = json.dumps(QUALITY_GATE_RESPONSE_SCHEMA)
            full_cmd = [
                "claude",
                "--print",  # Non-interactive mode
                "--output-format",
                "json",  # JSON output wrapper
                "--system-prompt",
                instructions,
                "--json-schema",
                schema_json,  # Structured output - result in 'structured_output' field
                "-p",
                "--",  # Read prompt from stdin
            ]

        try:
            # Run review agent with payload piped via stdin
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=payload.encode()),
                    timeout=self.timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                raise QualityGateError(
                    f"Review agent timed out after {self.timeout} seconds"
                ) from None

            if process.returncode != 0:
                raise QualityGateError(
                    f"Review agent failed with exit code {process.returncode}:\n"
                    f"stderr: {stderr.decode()}"
                )

            return self._parse_response(stdout.decode())

        except FileNotFoundError as e:
            raise QualityGateError("Review agent command not found: claude") from e


class MockQualityGate(QualityGate):
    """Mock quality gate for testing.

    Always passes unless configured otherwise.
    """

    def __init__(self, should_pass: bool = True, feedback: str = "Mock evaluation"):
        """Initialize mock quality gate.

        Args:
            should_pass: Whether evaluations should pass
            feedback: Feedback message to return
        """
        super().__init__()
        self.should_pass = should_pass
        self.feedback = feedback
        self.evaluations: list[dict[str, Any]] = []

    async def evaluate(
        self,
        quality_criteria: list[str],
        outputs: list[str],
        project_root: Path,
    ) -> QualityGateResult:
        """Mock evaluation - records call and returns configured result."""
        self.evaluations.append(
            {
                "quality_criteria": quality_criteria,
                "outputs": outputs,
            }
        )

        criteria_results = [
            QualityCriteriaResult(
                criterion=c,
                passed=self.should_pass,
                feedback=None if self.should_pass else self.feedback,
            )
            for c in quality_criteria
        ]

        return QualityGateResult(
            passed=self.should_pass,
            feedback=self.feedback,
            criteria_results=criteria_results,
        )
