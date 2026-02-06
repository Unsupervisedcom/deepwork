"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via ClaudeCLI) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiofiles

from deepwork.mcp.claude_cli import ClaudeCLI
from deepwork.mcp.schemas import (
    QualityCriteriaResult,
    QualityGateResult,
    ReviewResult,
)

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

# Section headers for inputs/outputs
SECTION_SEPARATOR = "=" * 20


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

    def _build_instructions(
        self,
        quality_criteria: dict[str, str],
        notes: str | None = None,
    ) -> str:
        """Build the system instructions for the review agent.

        Args:
            quality_criteria: Map of criterion name to criterion question
            notes: Optional notes from the agent about work done

        Returns:
            System instructions string
        """
        criteria_list = "\n".join(
            f"- **{name}**: {question}" for name, question in quality_criteria.items()
        )

        notes_section = ""
        if notes:
            notes_section = f"""

## Author Notes

The author provided the following notes about the work done:

{notes}"""

        return f"""\
You are an editor responsible for reviewing the files listed as outputs.
Your job is to evaluate whether outputs meet the specified criteria below.
You have also been provided any relevant inputs that were used by the process that generated the outputs.

## Criteria to Evaluate

{criteria_list}
{notes_section}

## Response Format

You must respond with JSON in this exact structure:
```json
{{
  "passed": true/false,
  "feedback": "Brief overall summary of evaluation",
  "criteria_results": [
    {{
      "criterion": "The criterion name",
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

    @staticmethod
    def _flatten_output_paths(outputs: dict[str, str | list[str]]) -> list[str]:
        """Flatten a structured outputs dict into a list of file paths.

        Args:
            outputs: Map of output names to file path(s)

        Returns:
            Flat list of all file paths
        """
        paths: list[str] = []
        for value in outputs.values():
            if isinstance(value, list):
                paths.extend(value)
            else:
                paths.append(value)
        return paths

    async def _read_file_sections(
        self,
        file_paths: dict[str, str | list[str]],
        project_root: Path,
    ) -> list[str]:
        """Read files and return formatted sections for each.

        Args:
            file_paths: Map of names to file path(s)
            project_root: Project root path for reading files

        Returns:
            List of formatted file sections
        """
        sections: list[str] = []
        all_paths = self._flatten_output_paths(file_paths)

        for file_path in all_paths:
            full_path = project_root / file_path
            header = f"{FILE_SEPARATOR} {file_path} {FILE_SEPARATOR}"

            if full_path.exists():
                try:
                    async with aiofiles.open(full_path, encoding="utf-8") as f:
                        content = await f.read()
                    sections.append(f"{header}\n{content}")
                except (UnicodeDecodeError, ValueError):
                    abs_path = full_path.resolve()
                    sections.append(
                        f"{header}\n[Binary file — not included in review. "
                        f"Read from: {abs_path}]"
                    )
                except Exception as e:
                    sections.append(f"{header}\n[Error reading file: {e}]")
            else:
                sections.append(f"{header}\n[File not found]")

        return sections

    async def _build_payload(
        self,
        outputs: dict[str, str | list[str]],
        project_root: Path,
        inputs: dict[str, str | list[str]] | None = None,
    ) -> str:
        """Build the user prompt payload with file contents.

        Organizes content into clearly separated INPUTS and OUTPUTS sections.

        Args:
            outputs: Map of output names to file path(s)
            project_root: Project root path for reading files
            inputs: Optional map of input names to file path(s) from prior steps

        Returns:
            Formatted payload with file contents in sections
        """
        parts: list[str] = []

        # Build inputs section if provided
        if inputs:
            input_sections = await self._read_file_sections(inputs, project_root)
            if input_sections:
                parts.append(f"{SECTION_SEPARATOR} BEGIN INPUTS {SECTION_SEPARATOR}")
                parts.extend(input_sections)
                parts.append(f"{SECTION_SEPARATOR} END INPUTS {SECTION_SEPARATOR}")

        # Build outputs section
        output_sections = await self._read_file_sections(outputs, project_root)
        if output_sections:
            parts.append(f"{SECTION_SEPARATOR} BEGIN OUTPUTS {SECTION_SEPARATOR}")
            parts.extend(output_sections)
            parts.append(f"{SECTION_SEPARATOR} END OUTPUTS {SECTION_SEPARATOR}")

        if not parts:
            return "[No files provided]"

        return "\n\n".join(parts)

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
        quality_criteria: dict[str, str],
        outputs: dict[str, str | list[str]],
        project_root: Path,
        inputs: dict[str, str | list[str]] | None = None,
        notes: str | None = None,
    ) -> QualityGateResult:
        """Evaluate step outputs against quality criteria.

        Args:
            quality_criteria: Map of criterion name to criterion question
            outputs: Map of output names to file path(s)
            project_root: Project root path
            inputs: Optional map of input names to file path(s) from prior steps
            notes: Optional notes from the agent about work done

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

        instructions = self._build_instructions(quality_criteria, notes=notes)
        payload = await self._build_payload(outputs, project_root, inputs=inputs)

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

    async def evaluate_reviews(
        self,
        reviews: list[dict[str, Any]],
        outputs: dict[str, str | list[str]],
        output_specs: dict[str, str],
        project_root: Path,
        inputs: dict[str, str | list[str]] | None = None,
        notes: str | None = None,
    ) -> list[ReviewResult]:
        """Evaluate all reviews for a step, running them in parallel.

        Args:
            reviews: List of review dicts with run_each and quality_criteria
            outputs: Map of output names to file path(s)
            output_specs: Map of output names to their type ("file" or "files")
            project_root: Project root path
            inputs: Optional map of input names to file path(s) from prior steps
            notes: Optional notes from the agent about work done

        Returns:
            List of ReviewResult for any failed reviews (empty if all pass)
        """
        if not reviews:
            return []

        tasks: list[tuple[str, str | None, dict[str, str], dict[str, str | list[str]]]] = []

        for review in reviews:
            run_each = review["run_each"]
            quality_criteria = review["quality_criteria"]

            if run_each == "step":
                # Review all outputs together
                tasks.append((run_each, None, quality_criteria, outputs))
            elif run_each in outputs:
                output_type = output_specs.get(run_each, "file")
                output_value = outputs[run_each]

                if output_type == "files" and isinstance(output_value, list):
                    # Run once per file
                    for file_path in output_value:
                        tasks.append((
                            run_each,
                            file_path,
                            quality_criteria,
                            {run_each: file_path},
                        ))
                else:
                    # Single file - run once
                    tasks.append((
                        run_each,
                        output_value if isinstance(output_value, str) else None,
                        quality_criteria,
                        {run_each: output_value},
                    ))

        async def run_review(
            run_each: str,
            target_file: str | None,
            criteria: dict[str, str],
            review_outputs: dict[str, str | list[str]],
        ) -> ReviewResult:
            result = await self.evaluate(
                quality_criteria=criteria,
                outputs=review_outputs,
                project_root=project_root,
                inputs=inputs,
                notes=notes,
            )
            return ReviewResult(
                review_run_each=run_each,
                target_file=target_file,
                passed=result.passed,
                feedback=result.feedback,
                criteria_results=result.criteria_results,
            )

        results = await asyncio.gather(
            *(run_review(*task) for task in tasks)
        )

        return [r for r in results if not r.passed]


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
        quality_criteria: dict[str, str],
        outputs: dict[str, str | list[str]],
        project_root: Path,
        inputs: dict[str, str | list[str]] | None = None,
        notes: str | None = None,
    ) -> QualityGateResult:
        """Mock evaluation - records call and returns configured result."""
        self.evaluations.append(
            {
                "quality_criteria": quality_criteria,
                "outputs": outputs,
                "inputs": inputs,
                "notes": notes,
            }
        )

        criteria_results = [
            QualityCriteriaResult(
                criterion=name,
                passed=self.should_pass,
                feedback=None if self.should_pass else self.feedback,
            )
            for name in quality_criteria
        ]

        return QualityGateResult(
            passed=self.should_pass,
            feedback=self.feedback,
            criteria_results=criteria_results,
        )
