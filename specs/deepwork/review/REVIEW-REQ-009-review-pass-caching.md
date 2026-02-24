# REVIEW-REQ-009: Review Pass Caching

## Overview

When a review passes, the reviewing agent marks it as passed via the `mark_review_as_passed` MCP tool. On subsequent runs of `get_review_instructions`, reviews whose trigger files haven't changed are automatically skipped. This avoids re-running reviews on unchanged code.

The mechanism relies on a deterministic `review_id` that encodes the rule name, file paths, and a content hash. When file contents change, the content hash changes, producing a new `review_id` that has no matching `.passed` marker — so the review runs again automatically.

## Requirements

### REVIEW-REQ-009.0: Pass Caching Guarantee

1. If a review passes and none of the files that triggered that review have changed, subsequent calls to `get_review_instructions` MUST NOT re-run that review.

### REVIEW-REQ-009.1: Review ID Computation

1. Each review task MUST be assigned a deterministic `review_id` of the form `{sanitized_rule_name}--{sanitized_file_paths}--{content_hash_12chars}`.
2. The rule name component MUST replace non-alphanumeric characters (except `-`, `_`, `.`) with `-`.
3. The file paths component MUST replace `/` with `-` in each path, join multiple paths with `_AND_`, and fall back to `{N}_files` when the joined paths exceed 100 characters.
4. The content hash MUST be the first 12 hex characters of the SHA-256 digest of the concatenated contents of all files to review, with files sorted alphabetically before concatenation.
5. Files that cannot be read MUST contribute the placeholder string `MISSING` instead of their contents.
6. The same inputs (rule name, file paths, file contents) MUST always produce the same `review_id`.

### REVIEW-REQ-009.2: `mark_review_as_passed` MCP Tool

1. The tool MUST be registered as `mark_review_as_passed` on the MCP server.
2. The tool MUST accept a required `review_id` parameter (string).
3. The tool MUST create an empty file at `.deepwork/tmp/review_instructions/{review_id}.passed`.
4. The tool MUST create the parent directory if it does not exist.
5. The tool MUST reject empty `review_id` values with an error message.
6. The tool MUST reject `review_id` values containing path traversal sequences (`..`) or absolute paths (starting with `/`).
7. The tool MUST return a confirmation message that includes the `review_id`.

### REVIEW-REQ-009.3: Instruction Generation Skips Passed Reviews

1. `write_instruction_files` MUST check for a `.passed` marker file before writing each instruction file.
2. If `{review_id}.passed` exists in the instructions directory, that task MUST be skipped (no instruction file written, not included in results).
3. If all tasks are skipped, the function MUST return an empty list.
4. Instruction files MUST be named `{review_id}.md` (not random IDs).

### REVIEW-REQ-009.4: Instruction Files Include "After Review" Section

1. Each generated instruction file MUST include an "After Review" section.
2. The "After Review" section MUST appear after the files-to-review section and before the traceability blurb (if present).
3. The section MUST include the exact `mark_review_as_passed` tool name and the exact `review_id` value for the task.

### REVIEW-REQ-009.5: Cleanup Preserves `.passed` Files

1. When `write_instruction_files` clears previous instruction files, it MUST delete only `.md` files, not `.passed` files.
2. `.passed` files MUST survive across multiple calls to `write_instruction_files`.

### REVIEW-REQ-009.6: `get_configured_reviews` Unaffected

1. The `get_configured_reviews` tool MUST NOT be affected by pass caching — it always returns all matching rules regardless of cached state.
