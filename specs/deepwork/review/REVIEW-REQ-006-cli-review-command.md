# REVIEW-REQ-006: CLI Review Command

## Overview

The `deepwork review` CLI command orchestrates the full DeepWork Reviews pipeline: discovering `.deepreview` config files, detecting changed files via git, matching them against rules, generating review instruction files, and outputting structured instructions for the target AI agent platform (currently Claude Code). The command is designed to be invoked via `!bash` syntax from a skill, with its stdout captured and used as agent instructions.

## Requirements

### REVIEW-REQ-006.1: Command Definition

1. The `review` command MUST be a Click command registered in the DeepWork CLI.
2. The command MUST be registered in `src/deepwork/cli/main.py` via `cli.add_command(review)`.
3. The command MUST accept a `--instructions-for` option with choices `["claude"]` (required).
4. The command MUST accept a `--base-ref` option (string, default: `None`) specifying the git ref to diff against.
5. The command MUST accept a `--path` option (default: `"."`, must exist, must be a directory) specifying the project root.
6. The command MUST accept a `--files` option that can be specified multiple times to provide explicit file paths to review.

### REVIEW-REQ-006.2: Pipeline Orchestration

1. The command MUST execute the following pipeline in order:
   a. Discover all `.deepreview` files under the project root (REVIEW-REQ-002).
   b. Determine changed files (see REVIEW-REQ-006.6).
   c. Match changed files against discovered rules and group by strategy (REVIEW-REQ-004).
   d. Generate review instruction files for each task (REVIEW-REQ-005).
   e. Format and output the results for the target platform.
2. If any step in the pipeline fails with an error, the command MUST print a user-friendly error message to stderr and exit with code 1.

### REVIEW-REQ-006.3: Output Format for Claude Code

1. When `--instructions-for claude` is specified, the command MUST output to stdout a structured text block that Claude Code can use to dispatch parallel review agents.
2. The output MUST begin with a line instructing the agent to invoke tasks in parallel.
3. For each review task, the output MUST include fields matching the Claude Code `Task` tool parameters:
   a. A `name` field formatted as `"{scope_prefix}{rule_name} review of {file_or_scope}"` — for `individual` strategy, `{file_or_scope}` is the single filename; for grouped strategies, it is a summary (e.g., `"3 files"`). When the rule comes from a `.deepreview` in a subdirectory, `{scope_prefix}` MUST be `"{parent_dir_name}/"` (e.g., `"my_job/"`); for root-level `.deepreview` files, `{scope_prefix}` MUST be empty.
   b. A `description` field with a short (3-5 word) summary for the task (e.g., `"Review {rule_name}"`). When the rule comes from a `.deepreview` in a subdirectory, the description MUST include the scope (e.g., `"Review my_job/{rule_name}"`).
   c. A `subagent_type` field set to the agent persona name (from the rule's `agent.claude` value) or `"general-purpose"` if no persona is specified.
   d. A `prompt` field referencing the instruction file path relative to the project root, prefixed with `@` (e.g., `@.deepwork/tmp/review_instructions/7142141.md`).
4. The instruction file paths MUST be relative to the project root.

### REVIEW-REQ-006.4: Empty Results

1. If no `.deepreview` files are found, the command MUST output a message indicating no review configuration was found.
2. If no changed files are detected, the command MUST output a message indicating no changes were found to review.
3. If changed files exist but no rules match, the command MUST output a message indicating no review rules matched the changed files.

### REVIEW-REQ-006.5: Error Handling

1. Configuration parse errors MUST be reported to stderr but MUST NOT prevent other `.deepreview` files from being processed (see REVIEW-REQ-002.3).
2. Git errors MUST be reported to stderr and the command MUST exit with code 1.
3. Instruction file write errors MUST be reported to stderr and the command MUST exit with code 1.

### REVIEW-REQ-006.6: Changed File Sources

The command supports three sources for the list of files to review, with the following priority:

1. **`--files` arguments** (highest priority): When one or more `--files` options are provided, the command MUST use those file paths directly and MUST NOT invoke git diff or read stdin.
2. **stdin** (second priority): When no `--files` are provided and stdin is not a TTY (i.e., input is piped), the command MUST read file paths from stdin (one per line, blank lines ignored). This allows chaining with other commands (e.g., `git diff --name-only HEAD~3 | deepwork review ...` or `find src -name '*.py' | deepwork review ...`).
3. **git diff** (default): When neither `--files` nor piped stdin is present, the command MUST fall back to detecting changed files via git diff (REVIEW-REQ-003).

In all cases:
4. The resulting file list MUST be sorted and deduplicated.
5. The `--base-ref` option only applies to the git diff source; it MUST be ignored when `--files` or stdin provides the file list.
