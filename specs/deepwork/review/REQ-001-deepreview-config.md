# REQ-001: DeepWork Reviews Configuration Format

## Overview

DeepWork Reviews uses `.deepreview` YAML configuration files to define review rules for automated code review. Each file contains one or more named rules that specify file matching patterns and review behavior. The configuration format is validated against a JSON Schema bundled with the DeepWork package. Rules support inline or file-referenced instructions, optional agent personas, and additional context flags.

## Requirements

### REQ-001.1: Configuration File Format

1. A `.deepreview` file MUST be a valid YAML document.
2. The top-level structure MUST be a mapping of rule names to rule objects.
3. Rule names MUST match the pattern `^[a-zA-Z0-9_-]+$`.
4. Each rule object MUST contain exactly three required keys: `description`, `match`, and `review`.
5. Rule objects MUST NOT contain additional properties beyond `description`, `match`, and `review`.

### REQ-001.2: Match Section

1. The `match` section MUST be an object.
2. The `match` section MUST contain an `include` key with a non-empty array of glob pattern strings.
3. The `match` section MAY contain an `exclude` key with an array of glob pattern strings.
4. The `match` section MUST NOT contain additional properties beyond `include` and `exclude`.
5. Glob patterns MUST support standard glob syntax including `**` for recursive directory matching and `*` for filename matching.

### REQ-001.3: Review Section

1. The `review` section MUST be an object.
2. The `review` section MUST contain a `strategy` key with one of: `"individual"`, `"matches_together"`, or `"all_changed_files"`.
3. The `review` section MUST contain an `instructions` key.
4. The `review` section MAY contain an `agent` key.
5. The `review` section MAY contain an `additional_context` key.
6. The `review` section MUST NOT contain additional properties beyond `strategy`, `instructions`, `agent`, and `additional_context`.

### REQ-001.4: Instructions

1. The `instructions` field MUST be one of two forms: an inline string, or an object with a `file` key.
2. When `instructions` is a string, the string MUST be used directly as the review instruction text.
3. When `instructions` is an object, it MUST contain a `file` key whose value is a path to a markdown file.
4. The `file` path MUST be resolved relative to the directory containing the `.deepreview` file.
5. The system MUST raise an error if a referenced instructions file does not exist.
6. The instructions object MUST NOT contain additional properties beyond `file`.

### REQ-001.5: Agent Configuration

1. The `agent` field, when present, MUST be an object mapping CLI provider names to agent persona strings.
2. Provider names MUST match the pattern `^[a-zA-Z0-9_-]+$`.
3. Agent persona values MUST be strings (e.g., `"security-expert"`, `"devops-engineer"`).
4. The system MUST select the agent persona matching the target platform (e.g., the `claude` key when generating instructions for Claude Code).
5. When no matching agent key exists for the target platform, the system MUST use the default agent (no persona).

### REQ-001.6: Additional Context

1. The `additional_context` field, when present, MUST be an object.
2. The `additional_context` object MAY contain `all_changed_filenames` (boolean).
3. The `additional_context` object MAY contain `unchanged_matching_files` (boolean).
4. The `additional_context` object MUST NOT contain additional properties beyond these two.
5. When `all_changed_filenames` is `true`, the system MUST include a list of all files changed in the changeset (not just matched files) as context in the review instructions.
6. When `unchanged_matching_files` is `true`, the system MUST include the full contents of files that match the `include` patterns but were NOT modified in this changeset.

### REQ-001.7: Schema Validation

1. The JSON Schema for `.deepreview` files MUST be bundled with the DeepWork package at `src/deepwork/schemas/deepreview_schema.json`.
2. The schema MUST be loaded at module import time and stored as a module-level constant.
3. Every `.deepreview` file MUST be validated against the schema before parsing into data models.
4. The system MUST raise an error with a descriptive message if schema validation fails, including the validation path and error details.
5. Schema validation MUST use the `jsonschema` library (same as job definition validation, see REQ-002.2).

### REQ-001.8: Data Model

1. Each parsed rule MUST be represented as a `ReviewRule` dataclass.
2. The `ReviewRule` MUST contain: `name` (str), `description` (str), `include_patterns` (list[str]), `exclude_patterns` (list[str]), `strategy` (str), `instructions` (str — resolved text), `agent` (dict[str, str] | None), `all_changed_filenames` (bool), `unchanged_matching_files` (bool), `source_dir` (Path), `source_file` (Path), `source_line` (int).
3. The `source_dir` field MUST be set to the directory containing the `.deepreview` file (used for resolving relative glob patterns and file references).
4. The `source_file` field MUST be set to the path of the `.deepreview` file the rule was parsed from.
5. The `source_line` field MUST be set to the 1-based line number where the rule name appears in the `.deepreview` file.
6. When `exclude` is not specified in the YAML, `exclude_patterns` MUST default to an empty list.
7. When `additional_context` is not specified, both `all_changed_filenames` and `unchanged_matching_files` MUST default to `False`.
8. When `agent` is not specified, it MUST default to `None`.
