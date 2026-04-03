"""Quality gate using DeepWork Reviews infrastructure.

Replaces the bespoke quality gate with dynamic ReviewRule objects built from
step output reviews and process requirements. These are merged with
.deepreview rules and processed through the standard review pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path

from deepwork.deepschema.review_bridge import generate_review_rules as gen_schema_rules
from deepwork.jobs.mcp.schemas import ArgumentValue
from deepwork.jobs.parser import (
    JobDefinition,
    ReviewBlock,
    Workflow,
    WorkflowStep,
)
from deepwork.review.config import ReviewRule, ReviewTask
from deepwork.review.discovery import load_all_rules
from deepwork.review.formatter import format_for_claude
from deepwork.review.instructions import (
    write_instruction_files,
)
from deepwork.review.matcher import match_files_to_rules
from deepwork.utils.validation import ValidationError, validate_against_schema

logger = logging.getLogger("deepwork.jobs.mcp.quality_gate")


class QualityGateError(Exception):
    """Exception raised for quality gate errors."""

    pass


def validate_json_schemas(
    outputs: dict[str, ArgumentValue],
    step: WorkflowStep,
    job: JobDefinition,
    project_root: Path,
) -> list[str]:
    """Validate file_path outputs against their step_argument json_schema.

    Returns list of error messages (empty if all pass).
    """
    errors: list[str] = []
    for output_name, value in outputs.items():
        arg = job.get_argument(output_name)
        if not arg or not arg.json_schema or arg.type != "file_path":
            continue

        paths = [value] if isinstance(value, str) else value
        for path in paths:
            full_path = project_root / path
            if not full_path.exists():
                continue
            try:
                import yaml

                content = full_path.read_text(encoding="utf-8")
                parsed = yaml.safe_load(content)
            except Exception as e:
                errors.append(f"Output '{output_name}' file '{path}': failed to parse: {e}")
                continue

            try:
                validate_against_schema(parsed, arg.json_schema)
            except ValidationError as e:
                errors.append(
                    f"Output '{output_name}' file '{path}': JSON schema validation failed: {e}"
                )

    return errors


def _collect_output_file_paths(
    outputs: dict[str, ArgumentValue],
    job: JobDefinition,
) -> list[str]:
    """Collect all file paths from file_path type outputs."""
    paths: list[str] = []
    for output_name, value in outputs.items():
        arg = job.get_argument(output_name)
        if arg and arg.type == "file_path":
            if isinstance(value, list):
                paths.extend(value)
            else:
                paths.append(value)
    return paths


def _build_input_context(
    step: WorkflowStep,
    job: JobDefinition,
    input_values: dict[str, ArgumentValue],
) -> str:
    """Build a context string describing the step's inputs and their values."""
    if not step.inputs:
        return ""

    parts: list[str] = []
    parts.append("## Step Inputs\n")

    for input_name, _input_ref in step.inputs.items():
        arg = job.get_argument(input_name)
        if not arg:
            continue

        value = input_values.get(input_name)
        if value is None:
            parts.append(f"- **{input_name}** ({arg.type}): {arg.description} — *not available*")
            continue

        if arg.type == "file_path":
            # For file_path, show the path as a reference
            if isinstance(value, list):
                paths_str = ", ".join(f"@{p}" for p in value)
                parts.append(f"- **{input_name}** (file_path): {paths_str}")
            else:
                parts.append(f"- **{input_name}** (file_path): @{value}")
        else:
            # For string, include content inline
            parts.append(f"- **{input_name}** (string): {value}")

    parts.append("")
    return "\n".join(parts)


def build_dynamic_review_rules(
    step: WorkflowStep,
    job: JobDefinition,
    workflow: Workflow,
    outputs: dict[str, ArgumentValue],
    input_values: dict[str, ArgumentValue],
    work_summary: str | None,
    project_root: Path,
) -> list[ReviewRule]:
    """Build dynamic ReviewRule objects from step output reviews.

    For each output with a review block (on the output ref or inherited from
    the step_argument), creates a ReviewRule with the output files as match
    targets.
    """
    rules: list[ReviewRule] = []
    input_context = _build_input_context(step, job, input_values)
    common_info = workflow.common_job_info or ""

    # Build preamble with common info and inputs
    preamble_parts: list[str] = []
    if common_info:
        preamble_parts.append(f"## Job Context\n\n{common_info}")
    if input_context:
        preamble_parts.append(input_context)
    preamble = "\n\n".join(preamble_parts)

    # Process each output
    for output_name, output_ref in step.outputs.items():
        arg = job.get_argument(output_name)
        if not arg:
            continue

        # Collect review blocks: output-level review + argument-level review
        review_blocks: list[ReviewBlock] = []
        if output_ref.review:
            review_blocks.append(output_ref.review)
        if arg.review:
            review_blocks.append(arg.review)

        if not review_blocks:
            continue

        # Get the output value
        value = outputs.get(output_name)
        if value is None:
            continue

        # Get file paths for file_path type
        if arg.type == "file_path":
            file_paths = [value] if isinstance(value, str) else list(value)
        else:
            # For string type, no file matching — create a synthetic task later
            file_paths = []

        for i, review_block in enumerate(review_blocks):
            # Build full instructions with preamble
            full_instructions = (
                f"{preamble}\n\n{review_block.instructions}"
                if preamble
                else review_block.instructions
            )

            suffix = "_arg" if i > 0 else ""
            rule_name = f"step_{step.name}_output_{output_name}{suffix}"

            if arg.type == "file_path" and file_paths:
                # Create exact-match patterns for the output files
                include_patterns = list(file_paths)

                rule = ReviewRule(
                    name=rule_name,
                    description=f"Review of output '{output_name}' from step '{step.name}'",
                    include_patterns=include_patterns,
                    exclude_patterns=[],
                    strategy=review_block.strategy,
                    instructions=full_instructions,
                    agent=review_block.agent,
                    all_changed_filenames=bool(
                        review_block.additional_context
                        and review_block.additional_context.get("all_changed_filenames")
                    ),
                    unchanged_matching_files=bool(
                        review_block.additional_context
                        and review_block.additional_context.get("unchanged_matching_files")
                    ),
                    precomputed_info_bash_command=None,
                    source_dir=project_root,
                    source_file=job.job_dir / "job.yml",
                    source_line=0,
                )
                rules.append(rule)

    # Process requirements review
    if step.process_requirements and work_summary is not None:
        attrs_list = "\n".join(
            f"- **{name}**: {statement}" for name, statement in step.process_requirements.items()
        )

        # Build context with all inputs and outputs
        output_context_parts: list[str] = []
        for output_name, value in outputs.items():
            arg = job.get_argument(output_name)
            if arg and arg.type == "file_path":
                if isinstance(value, list):
                    paths_str = ", ".join(f"@{p}" for p in value)
                    output_context_parts.append(f"- **{output_name}** (file_path): {paths_str}")
                else:
                    output_context_parts.append(f"- **{output_name}** (file_path): @{value}")
            elif arg and arg.type == "string":
                output_context_parts.append(f"- **{output_name}** (string): {value}")

        output_context = "\n".join(output_context_parts)

        pqa_instructions = f"""{preamble}

## Process Requirements Review

Please review for compliance with the following requirements. You MUST fail the review for any requirement using MUST/SHALL that is not met. You MUST fail the review for any SHOULD/RECOMMENDED requirement that appears easily achievable but was not followed. You SHOULD give feedback but not fail the review for any other applicable requirements. You can ignore requirements that are not applicable.

## Requirements

{attrs_list}

## Work Summary (work_summary)

{work_summary}

## Step Outputs

{output_context}

Evaluate whether the work described in the `work_summary` meets each requirement. If an output file helps verify a requirement, read it."""

        # Create a synthetic ReviewTask directly (not a ReviewRule since there are
        # no file patterns to match — this is about the process, not files)
        # We'll create a rule that matches all output files so it goes through
        # the pipeline
        output_paths = _collect_output_file_paths(outputs, job)
        if output_paths:
            pqa_rule = ReviewRule(
                name=f"step_{step.name}_process_quality",
                description=f"Process quality review for step '{step.name}'",
                include_patterns=output_paths,
                exclude_patterns=[],
                strategy="matches_together",
                instructions=pqa_instructions,
                agent=None,
                all_changed_filenames=False,
                unchanged_matching_files=False,
                precomputed_info_bash_command=None,
                source_dir=project_root,
                source_file=job.job_dir / "job.yml",
                source_line=0,
            )
            rules.append(pqa_rule)

    return rules


def run_quality_gate(
    step: WorkflowStep,
    job: JobDefinition,
    workflow: Workflow,
    outputs: dict[str, ArgumentValue],
    input_values: dict[str, ArgumentValue],
    work_summary: str | None,
    project_root: Path,
    platform: str = "claude",
) -> str | None:
    """Run the quality gate and return review instructions if reviews are needed.

    Returns:
        Review instructions string if there are reviews to run, None if all pass.
    """
    # 1. Validate json_schemas first
    schema_errors = validate_json_schemas(outputs, step, job, project_root)
    if schema_errors:
        error_text = "\n".join(f"- {e}" for e in schema_errors)
        return f"JSON schema validation failed:\n\n{error_text}\n\nFix these issues and call finished_step again."

    # 2. Build dynamic ReviewRules from step output reviews
    dynamic_rules = build_dynamic_review_rules(
        step=step,
        job=job,
        workflow=workflow,
        outputs=outputs,
        input_values=input_values,
        work_summary=work_summary,
        project_root=project_root,
    )

    # 3. Load .deepreview rules
    deepreview_rules, _errors = load_all_rules(project_root)

    # 3b. Load DeepSchema-generated review rules
    schema_rules, _schema_errors = gen_schema_rules(project_root)
    deepreview_rules.extend(schema_rules)

    # 4. Get the "changed files" list = output file paths
    output_files = _collect_output_file_paths(outputs, job)

    # 5. Match .deepreview rules against output files
    deepreview_tasks: list[ReviewTask] = []
    if deepreview_rules and output_files:
        deepreview_tasks = match_files_to_rules(
            output_files, deepreview_rules, project_root, platform
        )

    # 6. Match dynamic rules against output files
    dynamic_tasks: list[ReviewTask] = []
    if dynamic_rules and output_files:
        dynamic_tasks = match_files_to_rules(output_files, dynamic_rules, project_root, platform)

    # 7. Combine all tasks
    all_tasks = dynamic_tasks + deepreview_tasks

    if not all_tasks:
        return None

    # 8. Write instruction files (honors .passed markers)
    task_files = write_instruction_files(all_tasks, project_root)

    if not task_files:
        # All reviews already passed
        return None

    # 9. Format as review instructions
    review_output = format_for_claude(task_files, project_root)

    # 10. Build complete response with guidance
    guidance = _build_review_guidance(review_output)

    return guidance


def _build_review_guidance(review_output: str) -> str:
    """Build the complete review guidance including /review skill instructions."""
    return f"""Quality reviews are required before this step can advance.

{review_output}

## How to Run Reviews

For each review task listed above, launch it as a parallel Task agent. The task's prompt field points to an instruction file — read it and follow the review instructions.

## After Reviews

For any failing reviews, if you believe the issue is invalid, then you can call `mark_review_as_passed` on it. Otherwise, you should act on any feedback from the review to fix the issues. Once done, call `finished_step` again to see if you will pass now."""
