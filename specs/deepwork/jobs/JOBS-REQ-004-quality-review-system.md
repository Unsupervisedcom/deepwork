# JOBS-REQ-004: Quality Review System

## Overview

The quality review system evaluates step outputs against defined quality criteria. It operates in two modes: external runner mode (Claude CLI subprocess) and self-review mode (instructions file for agent subagent). Reviews can be scoped to the entire step or to individual output files. The system manages payload construction, timeout computation, and result parsing.

## Requirements

### JOBS-REQ-004.1: QualityGate Initialization

1. The `QualityGate` MUST accept an optional `cli` parameter (`ClaudeCLI` or `None`).
2. The `QualityGate` MUST accept an optional `max_inline_files` parameter (integer).
3. When `max_inline_files` is not provided, it MUST default to `DEFAULT_MAX_INLINE_FILES` (5).
4. When `max_inline_files` is explicitly set, the provided value MUST be used.
5. A `QualityGate` with `cli=None` MUST still support `build_review_instructions_file()` for self-review mode.
6. A `QualityGate` with `cli=None` MUST raise `QualityGateError` if `evaluate()` is called directly.

### JOBS-REQ-004.2: Review Modes

#### External Runner Mode (CLI Subprocess)

1. In external runner mode, the quality gate MUST invoke the ClaudeCLI subprocess to evaluate criteria.
2. The ClaudeCLI MUST receive a system prompt containing the quality criteria, optional author notes, and optional additional review guidance.
3. The ClaudeCLI MUST receive a user prompt (payload) containing output file contents or path listings.
4. The ClaudeCLI MUST be invoked with a JSON schema enforcing the response structure.
5. The JSON schema MUST require `passed` (boolean) and `feedback` (string) fields, with an optional `criteria_results` array.
6. Each criteria result MUST require `criterion` (string) and `passed` (boolean), with optional `feedback` (string or null).

#### Self-Review Mode (Instructions File)

7. In self-review mode, the system MUST generate a review instructions file.
8. The review instructions file MUST be written to `.deepwork/tmp/quality_review_{session_id}_{step_id}.md`.
9. The instructions file MUST contain: a header, output listing/content, criteria sections, author notes (if any), guidelines, and a task checklist.
10. The `finished_step` response in self-review mode MUST return `status: "needs_work"` with instructions for spawning a subagent.
11. The subagent instructions MUST direct the agent to: (a) read the review file, (b) evaluate criteria, (c) fix issues, (d) repeat until passing, (e) call `finished_step` again with `quality_review_override_reason`.

### JOBS-REQ-004.3: Payload Construction

1. When the total number of output files is less than or equal to `max_inline_files`, the payload MUST include full file contents inline.
2. When the total number of output files exceeds `max_inline_files`, the payload MUST switch to path-listing mode showing only file paths.
3. In path-listing mode, each path entry MUST include the file path and its output name.
4. In path-listing mode, the payload MUST include a notice about the total file count and instruct the reviewer to read files as needed.
5. File content sections MUST be delimited by a separator line of 20 dashes, the filename, and 20 dashes.
6. Output sections MUST be delimited by `====================` BEGIN/END OUTPUTS markers.
7. If author notes are provided, they MUST be included in a separate AUTHOR NOTES section.
8. If no files are provided and no notes exist, the payload MUST return `"[No files provided]"`.

### JOBS-REQ-004.4: File Reading

1. The system MUST read files in an async-friendly way (such as `aiofiles`)
2. For files that exist and are valid UTF-8, the system MUST include the full text content. [TODO: review this]
3. For files that exist but cannot be decoded as UTF-8 (binary files), the system MUST include a placeholder message: `"[Binary file - not included in review. Read from: {absolute_path}]"`.
4. For files that do not exist, the system MUST include a `"[File not found]"` placeholder.
5. For files that encounter other read errors, the system MUST include an `"[Error reading file: {error}]"` placeholder.

### JOBS-REQ-004.5: Review Instruction Building (Self-Review)

1. The `build_review_instructions_file()` method MUST produce a complete markdown document.
2. When there are multiple reviews, each review section MUST be numbered and include its scope (e.g., "all outputs together" or "output 'name'").
3. When there is a single review, the section MUST be titled "Criteria to Evaluate" without numbering.
4. For per-file reviews (`run_each` != "step") with `type: files` outputs, the instructions MUST list each individual file to evaluate.
5. Additional review guidance MUST be included under an "Additional Context" subsection if present.
6. The guidelines section MUST instruct the reviewer to be strict but fair, apply criteria pragmatically, and provide actionable feedback.
7. The task section MUST list 5 steps: read files, evaluate criteria, report PASS/FAIL, state overall result, provide feedback for failures.

### JOBS-REQ-004.6: Review Evaluation (External Runner)

1. When `quality_criteria` is empty, `evaluate()` MUST return an auto-pass result with `passed=True` and feedback `"No quality criteria defined - auto-passing"`.
2. When `_cli` is `None`, `evaluate()` MUST raise `QualityGateError`.
3. The system MUST use a dynamic timeout based on file count (see JOBS-REQ-004.8).
4. ClaudeCLI errors MUST be caught and re-raised as `QualityGateError`.

### JOBS-REQ-004.7: Multi-Review Evaluation

1. `evaluate_reviews()` MUST process all reviews for a step.
2. When the `reviews` list is empty, `evaluate_reviews()` MUST return an empty list (no failures).
3. For reviews with `run_each: "step"`, a single evaluation task MUST be created covering all outputs.
4. For reviews with `run_each` matching an output name where the output type is `"files"`, a separate evaluation task MUST be created for each individual file in the list.
5. For reviews with `run_each` matching an output name where the output type is `"file"`, a single evaluation task MUST be created for that file.
6. All evaluation tasks MUST be executed concurrently using `asyncio.gather`.
7. `evaluate_reviews()` MUST return only the failed reviews (where `passed=False`).
8. The `additional_review_guidance` from each review MUST be passed through to the underlying `evaluate()` call.

### JOBS-REQ-004.8: Timeout Computation

1. The base timeout MUST be 240 seconds (4 minutes).
2. For file counts of 5 or fewer, the timeout MUST be 240 seconds.
3. For file counts beyond 5, the timeout MUST increase by 30 seconds per additional file.

### JOBS-REQ-004.9: Result Parsing

1. The `_parse_result()` method MUST extract `passed`, `feedback`, and `criteria_results` from the structured output.
2. If `passed` is missing, it MUST default to `False`.
3. If `feedback` is missing, it MUST default to `"No feedback provided"`.
4. If `criteria_results` is missing, it MUST default to an empty list.
5. If the data cannot be interpreted, a `QualityGateError` MUST be raised.

### JOBS-REQ-004.10: Review Instructions Sections

1. The instructions MUST include a system prompt instructing the reviewer role.
2. The criteria list MUST be formatted as markdown bold name/question pairs.
3. The notes section (if present) MUST appear under "Author Notes" heading.
4. The guidance section (if present) MUST appear under "Additional Context" heading.
5. The instructions MUST state that the overall result should pass only if ALL criteria pass.
6. The instructions MUST state that criteria not applicable to the step's purpose should be passed.
