"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via ClaudeCLI) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiofiles

from deepwork.mcp.claude_cli import ClaudeCLI
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

    Uses ClaudeCLI to invoke a review agent that evaluates outputs
    and returns structured feedback.
    """

    def __init__(self, cli: ClaudeCLI | None = None):
        """Initialize quality gate.

        Args:
            cli: ClaudeCLI instance. If not provided, a default one is created.
        """
        self._cli = cli or ClaudeCLI()

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

    def _parse_result(self, data: dict[str, Any]) -> QualityGateResult:
        """Parse the structured output into a QualityGateResult.

        Args:
            data: The structured_output dict from ClaudeCLI

        Returns:
            Parsed QualityGateResult

        Raises:
            QualityGateError: If data cannot be interpreted
        """
        try:
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

        except (ValueError, KeyError) as e:
            raise QualityGateError(
                f"Failed to interpret quality gate result: {e}\n"
                f"Data was: {data}"
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

        instructions = self._build_instructions(quality_criteria)
        payload = await self._build_payload(outputs, project_root)

        from deepwork.mcp.claude_cli import ClaudeCLIError

        try:
            data = await self._cli.run(
                prompt=payload,
                system_prompt=instructions,
                json_schema=QUALITY_GATE_RESPONSE_SCHEMA,
                cwd=project_root,
            )
        except ClaudeCLIError as e:
            raise QualityGateError(str(e)) from e

        return self._parse_result(data)


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
