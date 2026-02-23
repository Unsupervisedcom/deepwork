# REQ-004: Rule Matching and Review Strategies

## Overview

After discovering review rules (REQ-002) and changed files (REQ-003), the system matches changed files against each rule's glob patterns, then groups the matched files according to the rule's review strategy. The result is a list of `ReviewTask` objects, each representing a discrete review to be performed by an agent. Glob patterns are always resolved relative to the directory containing the `.deepreview` file that defined the rule.

## Requirements

### REQ-004.1: Glob Pattern Matching

1. Include patterns MUST be matched against file paths that are relative to the rule's `source_dir`.
2. A changed file MUST first be checked to determine whether it resides under the rule's `source_dir`. If the changed file is not under `source_dir`, it MUST NOT match any patterns in that rule.
3. To test a match, the system MUST compute the changed file's path relative to `source_dir` and match it against the glob pattern.
4. The system MUST support `**` for recursive directory matching (e.g., `**/*.py` matches Python files at any depth).
5. The system MUST support `*` for single-component matching (e.g., `*.py` matches Python files in the current directory only).
6. A file MUST match a rule if it matches ANY of the `include` patterns AND does NOT match ANY of the `exclude` patterns.
7. If `exclude` is empty, only `include` patterns determine the match.

### REQ-004.2: Review Task Data Model

1. Each review task MUST be represented as a `ReviewTask` dataclass.
2. The `ReviewTask` MUST contain: `rule_name` (str), `files_to_review` (list[str] — paths relative to repo root), `instructions` (str), `agent_name` (str | None), `source_location` (str — formatted as `"path:line"`), `additional_files` (list[str] — unchanged matching files, relative to repo root), `all_changed_filenames` (list[str] | None).
3. `files_to_review` MUST always contain at least one file path.
4. `source_location` MUST be formatted as `"{relative_path}:{line_number}"` where the path is relative to the project root (e.g., `"src/.deepreview:5"`).

### REQ-004.3: Strategy — individual

1. When a rule's strategy is `"individual"`, the system MUST create one `ReviewTask` per matched changed file.
2. Each task's `files_to_review` MUST contain exactly one file path.
3. The task's `rule_name` MUST be the rule name.
4. The task's `instructions` MUST be the rule's resolved instruction text.

### REQ-004.4: Strategy — matches_together

1. When a rule's strategy is `"matches_together"`, the system MUST create a single `ReviewTask` containing all matched changed files.
2. The task's `files_to_review` MUST contain all matched changed files.
3. When the rule has `unchanged_matching_files: true`, the system MUST find all files under `source_dir` that match the `include` patterns (and do not match `exclude` patterns) but are NOT in the changed files list.
4. These unchanged matching files MUST be included in the task's `additional_files` list.
5. To discover unchanged matching files, the system MUST scan the filesystem using the rule's glob patterns relative to `source_dir`.

### REQ-004.5: Strategy — all_changed_files

1. When a rule's strategy is `"all_changed_files"`, the system MUST create a single `ReviewTask` only if at least one changed file matches the rule's patterns.
2. If triggered, the task's `files_to_review` MUST contain ALL changed files from the changeset (not just the matched ones).
3. This strategy acts as a "tripwire": the match patterns determine IF the review triggers, but the review itself covers the entire changeset.

### REQ-004.6: Additional Context — all_changed_filenames

1. When a rule has `all_changed_filenames: true`, every `ReviewTask` generated from that rule MUST include the full list of all changed filenames in `all_changed_filenames`.
2. This list MUST include ALL changed files in the changeset, regardless of whether they matched the rule's patterns.

### REQ-004.7: No-Match Behavior

1. If no changed files match a rule's patterns, the system MUST NOT create any `ReviewTask` for that rule.
2. If no rules produce any tasks, the overall result MUST be an empty list.

### REQ-004.8: Agent Resolution

1. When generating a `ReviewTask`, the system MUST accept a `platform` parameter (e.g., `"claude"`).
2. If the rule defines an `agent` mapping and the mapping contains a key matching the platform, the corresponding value MUST be set as the task's `agent_name`.
3. If the rule defines no `agent` mapping, or the mapping does not contain the target platform key, `agent_name` MUST be `None`.

### REQ-004.9: Orchestration

1. The system MUST provide a `match_files_to_rules(changed_files, rules, project_root, platform="claude")` function that processes all rules and returns a list of `ReviewTask` objects.
2. Each rule MUST be processed independently — a file can match multiple rules and appear in multiple tasks.
3. The function MUST process rules in the order they were discovered.
