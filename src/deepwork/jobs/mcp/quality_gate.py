"""Quality gate for evaluating step outputs.

The quality gate invokes a review agent (via ClaudeCLI) to evaluate
step outputs against quality criteria.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiofiles

from deepwork.jobs.mcp.claude_cli import ClaudeCLI
from deepwork.jobs.mcp.schemas import (
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
    and returns structured feedback. Can also build review instructions
    files for agent self-review when no external runner is configured.
    """

    # Default maximum number of files to include inline in the review payload.
    # Beyond this threshold, only file paths are listed.
    DEFAULT_MAX_INLINE_FILES = 5

    def __init__(
        self,
        cli: ClaudeCLI | None = None,
        max_inline_files: int | None = None,
    ):
        """Initialize quality gate.

        Args:
            cli: ClaudeCLI instance. If None, evaluate() cannot be called
                but instruction-building methods still work.
            max_inline_files: Maximum number of files to embed inline in
                review payloads. Beyond this, only file paths are listed.
                Defaults to DEFAULT_MAX_INLINE_FILES (5).
        """
        self._cli = cli
        self.max_inline_files = (
            max_inline_files if max_inline_files is not None else self.DEFAULT_MAX_INLINE_FILES
        )

    def _build_instructions(
        self,
        quality_criteria: dict[str, str],
        notes: str | None = None,
        additional_review_guidance: str | None = None,
    ) -> str:
        """Build the system instructions for the review agent.

        Args:
            quality_criteria: Map of criterion name to criterion question
            notes: Optional notes from the agent about work done
            additional_review_guidance: Optional guidance about what context to look at

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

        guidance_section = ""
        if additional_review_guidance:
            guidance_section = f"""

## Additional Context

{additional_review_guidance}"""

        return f"""\
You are an editor responsible for reviewing the files listed as outputs.
Your job is to evaluate whether outputs meet the specified criteria below.

## Criteria to Evaluate

{criteria_list}
{notes_section}
{guidance_section}

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
- Apply criteria pragmatically. If a criterion is not applicable to this step's purpose, pass it.
- Only mark a criterion as passed if it is clearly met or if it is not applicable.
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
                        f"{header}\n[Binary file — not included in review. Read from: {abs_path}]"
                    )
                except Exception as e:
                    sections.append(f"{header}\n[Error reading file: {e}]")
            else:
                sections.append(f"{header}\n[File not found]")

        return sections

    # =========================================================================
    # WARNING: REVIEW PERFORMANCE IS SENSITIVE TO PAYLOAD SIZE
    #
    # The payload builder below sends file contents to the review agent (Claude
    # CLI subprocess or self-review file). Reviews can get REALLY SLOW if the
    # content gets too big:
    #
    # - Each file's full content is read and embedded in the prompt
    # - The review agent must process ALL of this content to evaluate criteria
    # - Large payloads (25+ files, or files with 500+ lines each) can cause
    #   the review to approach or exceed its timeout
    # - Per-file reviews (run_each: <output_name> with type: files) multiply
    #   the problem — each file gets its own review subprocess
    #
    # To mitigate this, when more than self.max_inline_files files are
    # present, the payload switches to a path-listing mode that only shows
    # file paths instead of dumping all contents inline. The reviewer can
    # then use its own tools to read specific files as needed.
    #
    # max_inline_files is configurable per instance:
    #   - external_runner="claude": 5 (embed small sets, list large ones)
    #   - external_runner=None (self-review): 0 (always list paths)
    #
    # If you're changing the payload builder, keep payload size in mind.
    # =========================================================================

    @staticmethod
    def _build_path_listing(file_paths: dict[str, str | list[str]]) -> list[str]:
        """Build a path-only listing for large file sets.

        Args:
            file_paths: Map of names to file path(s)

        Returns:
            List of formatted path entries
        """
        lines: list[str] = []
        for name, value in file_paths.items():
            if isinstance(value, list):
                for path in value:
                    lines.append(f"- {path}  (output: {name})")
            else:
                lines.append(f"- {value}  (output: {name})")
        return lines

    async def _build_payload(
        self,
        outputs: dict[str, str | list[str]],
        project_root: Path,
        notes: str | None = None,
    ) -> str:
        """Build the user prompt payload with output file contents.

        When the total number of files exceeds MAX_INLINE_FILES, the payload
        lists file paths instead of embedding full contents to avoid slow reviews.

        Args:
            outputs: Map of output names to file path(s)
            project_root: Project root path for reading files
            notes: Optional notes from the agent about work done

        Returns:
            Formatted payload with output file contents or path listing
        """
        parts: list[str] = []
        total_files = len(self._flatten_output_paths(outputs))

        if total_files > self.max_inline_files:
            # Too many files — list paths only so the reviewer reads selectively
            path_lines = self._build_path_listing(outputs)
            parts.append(f"{SECTION_SEPARATOR} BEGIN OUTPUTS {SECTION_SEPARATOR}")
            parts.append(
                f"[{total_files} files — too many to include inline. "
                f"Paths listed below. Read files as needed to evaluate criteria.]"
            )
            parts.extend(path_lines)
            parts.append(f"{SECTION_SEPARATOR} END OUTPUTS {SECTION_SEPARATOR}")
        else:
            # Build outputs section with full content
            output_sections = await self._read_file_sections(outputs, project_root)
            if output_sections:
                parts.append(f"{SECTION_SEPARATOR} BEGIN OUTPUTS {SECTION_SEPARATOR}")
                parts.extend(output_sections)
                parts.append(f"{SECTION_SEPARATOR} END OUTPUTS {SECTION_SEPARATOR}")

        if notes:
            parts.append(f"{SECTION_SEPARATOR} AUTHOR NOTES {SECTION_SEPARATOR}")
            parts.append(notes)
            parts.append(f"{SECTION_SEPARATOR} END AUTHOR NOTES {SECTION_SEPARATOR}")

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
                f"Failed to interpret quality gate result: {e}\nData was: {data}"
            ) from e

    async def build_review_instructions_file(
        self,
        reviews: list[dict[str, Any]],
        outputs: dict[str, str | list[str]],
        output_specs: dict[str, str],
        project_root: Path,
        notes: str | None = None,
    ) -> str:
        """Build complete review instructions content for writing to a file.

        Used in self-review mode (no external runner) to generate a file that
        a subagent can read and follow to evaluate quality criteria.

        Args:
            reviews: List of review dicts with run_each, quality_criteria,
                and optional additional_review_guidance
            outputs: Map of output names to file path(s)
            output_specs: Map of output names to their type ("file" or "files")
            project_root: Project root path
            notes: Optional notes from the agent about work done

        Returns:
            Complete review instructions as a string
        """
        parts: list[str] = []

        parts.append("# Quality Review Instructions")
        parts.append("")
        parts.append(
            "You are an editor responsible for reviewing the outputs of a workflow step. "
            "Your job is to evaluate whether the outputs meet the specified quality criteria."
        )
        parts.append("")

        # Build outputs listing (uses self.max_inline_files to decide inline vs path-only)
        # Notes are handled separately below in the "Author Notes" section,
        # so we don't pass them to _build_payload here.
        payload = await self._build_payload(outputs, project_root)
        parts.append(payload)
        parts.append("")

        # Build review sections
        for i, review in enumerate(reviews, 1):
            run_each = review["run_each"]
            quality_criteria = review["quality_criteria"]
            guidance = review.get("additional_review_guidance")

            if len(reviews) > 1:
                scope = "all outputs together" if run_each == "step" else f"output '{run_each}'"
                parts.append(f"## Review {i} (scope: {scope})")
            else:
                parts.append("## Criteria to Evaluate")
            parts.append("")

            criteria_list = "\n".join(
                f"- **{name}**: {question}" for name, question in quality_criteria.items()
            )
            parts.append(criteria_list)
            parts.append("")

            if run_each != "step" and run_each in outputs:
                output_type = output_specs.get(run_each, "file")
                output_value = outputs[run_each]
                if output_type == "files" and isinstance(output_value, list):
                    parts.append(
                        f"Evaluate the above criteria for **each file** in output '{run_each}':"
                    )
                    for fp in output_value:
                        parts.append(f"- {fp}")
                    parts.append("")

            if guidance:
                parts.append("### Additional Context")
                parts.append("")
                parts.append(guidance)
                parts.append("")

        if notes:
            parts.append("## Author Notes")
            parts.append("")
            parts.append(notes)
            parts.append("")

        parts.append("## Guidelines")
        parts.append("")
        parts.append("- Be strict but fair")
        parts.append(
            "- Apply criteria pragmatically. If a criterion is not applicable "
            "to this step's purpose, pass it."
        )
        parts.append("- Only mark a criterion as passed if it is clearly met or not applicable.")
        parts.append("- Provide specific, actionable feedback for failed criteria.")
        parts.append(
            "- The overall review should PASS only if ALL criteria across all reviews pass."
        )
        parts.append("")
        parts.append("## Your Task")
        parts.append("")
        parts.append("1. Read each output file listed above")
        parts.append("2. Evaluate every criterion in every review section")
        parts.append("3. For each criterion, report **PASS** or **FAIL** with specific feedback")
        parts.append("4. At the end, clearly state the overall result: **PASSED** or **FAILED**")
        parts.append(
            "5. If any criteria failed, provide clear actionable feedback on what needs to change"
        )

        return "\n".join(parts)

    @staticmethod
    def compute_timeout(file_count: int) -> int:
        """Compute dynamic timeout based on number of files.

        Base timeout is 240 seconds (4 minutes). For every file beyond
        the first 5, add 30 seconds. Examples:
          - 3 files  -> 240s
          - 5 files  -> 240s
          - 10 files -> 240 + 30*5 = 390s (6.5 min)
          - 20 files -> 240 + 30*15 = 690s (11.5 min)

        Args:
            file_count: Total number of files being reviewed

        Returns:
            Timeout in seconds
        """
        return 240 + 30 * max(0, file_count - 5)

    async def evaluate(
        self,
        quality_criteria: dict[str, str],
        outputs: dict[str, str | list[str]],
        project_root: Path,
        notes: str | None = None,
        additional_review_guidance: str | None = None,
    ) -> QualityGateResult:
        """Evaluate step outputs against quality criteria.

        Args:
            quality_criteria: Map of criterion name to criterion question
            outputs: Map of output names to file path(s)
            project_root: Project root path
            notes: Optional notes from the agent about work done
            additional_review_guidance: Optional guidance for the reviewer

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

        if self._cli is None:
            raise QualityGateError(
                "Cannot evaluate quality gate without a CLI runner. "
                "Use build_review_instructions_file() for self-review mode."
            )

        instructions = self._build_instructions(
            quality_criteria,
            notes=notes,
            additional_review_guidance=additional_review_guidance,
        )
        payload = await self._build_payload(outputs, project_root, notes=notes)

        # Dynamic timeout: more files = more time for the reviewer
        file_count = len(self._flatten_output_paths(outputs))
        timeout = self.compute_timeout(file_count)

        from deepwork.jobs.mcp.claude_cli import ClaudeCLIError

        try:
            data = await self._cli.run(
                prompt=payload,
                system_prompt=instructions,
                json_schema=QUALITY_GATE_RESPONSE_SCHEMA,
                cwd=project_root,
                timeout=timeout,
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
        notes: str | None = None,
    ) -> list[ReviewResult]:
        """Evaluate all reviews for a step, running them in parallel.

        Args:
            reviews: List of review dicts with run_each, quality_criteria,
                and optional additional_review_guidance
            outputs: Map of output names to file path(s)
            output_specs: Map of output names to their type ("file" or "files")
            project_root: Project root path
            notes: Optional notes from the agent about work done

        Returns:
            List of ReviewResult for any failed reviews (empty if all pass)
        """
        if not reviews:
            return []

        # Each task is (run_each, target_file, criteria, review_outputs, guidance)
        tasks: list[
            tuple[str, str | None, dict[str, str], dict[str, str | list[str]], str | None]
        ] = []

        for review in reviews:
            run_each = review["run_each"]
            quality_criteria = review["quality_criteria"]
            guidance = review.get("additional_review_guidance")

            if run_each == "step":
                # Review all outputs together
                tasks.append((run_each, None, quality_criteria, outputs, guidance))
            elif run_each in outputs:
                output_type = output_specs.get(run_each, "file")
                output_value = outputs[run_each]

                if output_type == "files" and isinstance(output_value, list):
                    # Run once per file
                    for file_path in output_value:
                        tasks.append(
                            (
                                run_each,
                                file_path,
                                quality_criteria,
                                {run_each: file_path},
                                guidance,
                            )
                        )
                else:
                    # Single file - run once
                    tasks.append(
                        (
                            run_each,
                            output_value if isinstance(output_value, str) else None,
                            quality_criteria,
                            {run_each: output_value},
                            guidance,
                        )
                    )

        async def run_review(
            run_each: str,
            target_file: str | None,
            criteria: dict[str, str],
            review_outputs: dict[str, str | list[str]],
            guidance: str | None,
        ) -> ReviewResult:
            result = await self.evaluate(
                quality_criteria=criteria,
                outputs=review_outputs,
                project_root=project_root,
                notes=notes,
                additional_review_guidance=guidance,
            )
            return ReviewResult(
                review_run_each=run_each,
                target_file=target_file,
                passed=result.passed,
                feedback=result.feedback,
                criteria_results=result.criteria_results,
            )

        results = await asyncio.gather(*(run_review(*task) for task in tasks))

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
        notes: str | None = None,
        additional_review_guidance: str | None = None,
    ) -> QualityGateResult:
        """Mock evaluation - records call and returns configured result."""
        self.evaluations.append(
            {
                "quality_criteria": quality_criteria,
                "outputs": outputs,
                "notes": notes,
                "additional_review_guidance": additional_review_guidance,
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
