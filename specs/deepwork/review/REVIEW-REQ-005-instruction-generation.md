# REVIEW-REQ-005: Review Instruction Generation

## Overview

For each `ReviewTask`, the system generates a self-contained markdown instruction file that provides a review agent with everything it needs: the review instructions, the files to examine, and any additional context. These files are written to `.deepwork/tmp/review_instructions/` and referenced by path in the final CLI output. The instruction files use `@path` syntax so that Claude Code automatically reads the referenced files when the prompt is loaded.

## Requirements

### REVIEW-REQ-005.1: Instruction File Content

1. Each instruction file MUST be a valid markdown document.
2. The file MUST begin with a heading identifying the review rule and scope (e.g., `# Review: python_file_best_practices — src/app.py`).
3. The file MUST contain a "Review Instructions" section with the rule's resolved instruction text.
4. The file MUST contain a "Files to Review" section listing the file paths to examine.
5. File paths in the "Files to Review" section MUST be relative to the repository root.
6. When the task has `additional_files` (unchanged matching files), the file MUST contain an "Unchanged Matching Files" section listing those file paths.
7. When the task has `all_changed_filenames`, the file MUST contain an "All Changed Files" section listing every changed filename for context.

### REVIEW-REQ-005.2: File Path Formatting

1. File paths in the "Files to Review" section MUST be prefixed with `@` to trigger Claude Code's file-reading behavior (e.g., `@src/app.py`).
2. File paths in the "Unchanged Matching Files" section MUST also be prefixed with `@`.
3. File paths in the "All Changed Files" section MUST NOT be prefixed with `@` (they are listed for informational context only, not for the agent to read in full).

### REVIEW-REQ-005.3: File Writing

1. Instruction files MUST be written to `.deepwork/tmp/review_instructions/` under the project root.
2. The directory MUST be created if it does not exist (with `parents=True, exist_ok=True`).
3. Each file MUST have a unique filename with a `.md` extension.
4. The filename MUST be a random numeric ID (e.g., `7142141.md`) to avoid collisions.
5. The system MUST use `fs.safe_write()` for writing instruction files.
6. The system MUST return a list of `(ReviewTask, Path)` tuples mapping each task to its generated instruction file path.

### REVIEW-REQ-005.4: Instruction Resolution

1. When the rule's instructions reference a file (`{file: "path"}`), the system MUST resolve the path relative to the rule's `source_dir` and read the file contents.
2. The resolved instruction text MUST be included verbatim in the instruction file.
3. If the referenced file cannot be read, the system MUST raise an error with the file path and reason.

### REVIEW-REQ-005.5: Cleanup

1. The system SHOULD clear the `.deepwork/tmp/review_instructions/` directory at the start of each `deepwork review` invocation to avoid stale instruction files from previous runs.

### REVIEW-REQ-005.6: Policy Traceability

1. Each instruction file MUST end with a traceability line linking back to the source `.deepreview` file and rule location.
2. The traceability line MUST be formatted as: `This review was requested by the policy at \`{source_location}\`.` where `source_location` is the relative file path and line number (e.g., `src/.deepreview:5`).
3. The traceability line MUST be preceded by a markdown horizontal rule (`---`).
4. When `source_location` is empty, the traceability section MUST be omitted.
