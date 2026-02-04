"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via subprocess) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

import asyncio
import json
import shlex
from pathlib import Path
from typing import Any

import aiofiles
import jsonschema

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
    """

    def __init__(
        self,
        command: str = "claude -p --output-format json",
        timeout: int = 120,
    ):
        """Initialize quality gate.

        Args:
            command: Base command to invoke review agent (system prompt added via -s flag)
            timeout: Timeout in seconds for review agent
        """
        self.command = command
        self.timeout = timeout

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

    def _parse_response(
        self, response_text: str, validate_schema: bool = True
    ) -> QualityGateResult:
        """Parse the review agent's response.

        Args:
            response_text: Raw response from review agent
            validate_schema: Whether to validate against JSON schema (default True)

        Returns:
            Parsed QualityGateResult

        Raises:
            QualityGateError: If response cannot be parsed or fails schema validation
        """
        # Try to extract JSON from the response
        try:
            # Look for JSON in code blocks
            if "```json" in response_text:
                start = response_text.index("```json") + 7
                end = response_text.index("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.index("```") + 3
                end = response_text.index("```", start)
                json_text = response_text[start:end].strip()
            else:
                # Assume entire response is JSON
                json_text = response_text.strip()

            data = json.loads(json_text)

            # Validate against JSON schema if enabled
            if validate_schema:
                try:
                    jsonschema.validate(data, QUALITY_GATE_RESPONSE_SCHEMA)
                except jsonschema.ValidationError as ve:
                    raise QualityGateError(
                        f"Quality gate response failed schema validation: {ve.message}\n"
                        f"Path: {list(ve.absolute_path)}\n"
                        f"Response was: {json_text[:500]}..."
                    ) from ve

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

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise QualityGateError(
                f"Failed to parse review agent response: {e}\n"
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

        # Build command with system prompt flag
        # Parse the base command properly to handle quoted arguments
        base_cmd = shlex.split(self.command)
        # Add system prompt via -s flag
        full_cmd = base_cmd + ["-s", instructions]

        try:
            # Run review agent with system prompt and payload using async subprocess
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
            raise QualityGateError(f"Review agent command not found: {base_cmd[0]}") from e


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
