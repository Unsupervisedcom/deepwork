"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via subprocess) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from deepwork.mcp.schemas import QualityCriteriaResult, QualityGateResult


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
            command: Command to invoke review agent (receives prompt via stdin)
            timeout: Timeout in seconds for review agent
        """
        self.command = command
        self.timeout = timeout

    def _build_review_prompt(
        self,
        step_instructions: str,
        quality_criteria: list[str],
        outputs: list[str],
        project_root: Path,
    ) -> str:
        """Build the prompt for the review agent.

        Args:
            step_instructions: The step's instruction content
            quality_criteria: List of quality criteria to evaluate
            outputs: List of output file paths
            project_root: Project root path for reading files

        Returns:
            Formatted review prompt
        """
        # Read output file contents
        output_contents: list[str] = []
        for output_path in outputs:
            full_path = project_root / output_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    output_contents.append(f"### {output_path}\n```\n{content}\n```")
                except Exception as e:
                    output_contents.append(f"### {output_path}\nError reading file: {e}")
            else:
                output_contents.append(f"### {output_path}\nFile not found")

        outputs_text = "\n\n".join(output_contents) if output_contents else "No outputs provided"

        criteria_list = "\n".join(f"- {c}" for c in quality_criteria)

        return f"""You are a quality gate reviewer for a workflow step. Evaluate the outputs against the quality criteria.

## Step Instructions

{step_instructions}

## Quality Criteria

{criteria_list}

## Outputs to Review

{outputs_text}

## Your Task

Evaluate each output against the quality criteria. For each criterion, determine if it passes or fails.

Return your evaluation as JSON with this exact structure:
```json
{{
  "passed": true/false,
  "feedback": "Brief overall summary",
  "criteria_results": [
    {{
      "criterion": "The criterion text",
      "passed": true/false,
      "feedback": "Specific feedback for this criterion (null if passed)"
    }}
  ]
}}
```

Be strict but fair. Only mark as passed if the criterion is clearly met.
"""

    def _parse_response(self, response_text: str) -> QualityGateResult:
        """Parse the review agent's response.

        Args:
            response_text: Raw response from review agent

        Returns:
            Parsed QualityGateResult

        Raises:
            QualityGateError: If response cannot be parsed
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

    def evaluate(
        self,
        step_instructions: str,
        quality_criteria: list[str],
        outputs: list[str],
        project_root: Path,
    ) -> QualityGateResult:
        """Evaluate step outputs against quality criteria.

        Args:
            step_instructions: The step's instruction content
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

        prompt = self._build_review_prompt(
            step_instructions=step_instructions,
            quality_criteria=quality_criteria,
            outputs=outputs,
            project_root=project_root,
        )

        try:
            # Run review agent
            result = subprocess.run(
                self.command.split(),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(project_root),
            )

            if result.returncode != 0:
                raise QualityGateError(
                    f"Review agent failed with exit code {result.returncode}:\n"
                    f"stderr: {result.stderr}"
                )

            return self._parse_response(result.stdout)

        except subprocess.TimeoutExpired as e:
            raise QualityGateError(
                f"Review agent timed out after {self.timeout} seconds"
            ) from e
        except FileNotFoundError as e:
            raise QualityGateError(
                f"Review agent command not found: {self.command.split()[0]}"
            ) from e


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
        self.evaluations: list[dict] = []

    def evaluate(
        self,
        step_instructions: str,
        quality_criteria: list[str],
        outputs: list[str],
        project_root: Path,
    ) -> QualityGateResult:
        """Mock evaluation - records call and returns configured result."""
        self.evaluations.append({
            "step_instructions": step_instructions,
            "quality_criteria": quality_criteria,
            "outputs": outputs,
        })

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
