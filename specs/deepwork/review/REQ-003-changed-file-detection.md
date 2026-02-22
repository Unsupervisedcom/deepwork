# REQ-003: Changed File Detection

## Overview

DeepWork Reviews needs to determine which files have changed in order to match them against review rules. Changed files are detected using git, comparing the current state against a base reference (typically the main branch or a specific commit). The detection uses `subprocess` to invoke git directly, since GitPython is a dev-only dependency.

## Requirements

### REQ-003.1: Changed File Retrieval

1. The system MUST provide a `get_changed_files(project_root, base_ref)` function that returns a list of changed file paths relative to the repository root.
2. The function MUST use `subprocess.run()` to invoke `git diff --name-only` with appropriate flags.
3. The function MUST use `--diff-filter=ACMR` to include only Added, Copied, Modified, and Renamed files (excluding Deleted files, since deleted files cannot be reviewed).
4. The function MUST combine both unstaged changes and staged changes into a single deduplicated list.
5. Changed file paths MUST be returned relative to the git repository root.
6. The returned list MUST be sorted alphabetically.
7. The function MUST raise an error if the `git` command fails (e.g., not a git repository, invalid base ref).

### REQ-003.2: Base Reference

1. The `base_ref` parameter MUST default to `None`.
2. When `base_ref` is `None`, the system MUST auto-detect the merge base by finding the common ancestor between HEAD and the main branch.
3. The system MUST detect the main branch by checking for `main` first, then `master`, using `git rev-parse --verify`.
4. If neither `main` nor `master` exists, the system MUST fall back to `HEAD` (uncommitted changes only).
5. When `base_ref` is provided explicitly (e.g., `"main"`, `"HEAD"`, a commit SHA), the system MUST use it directly as the comparison target.
6. The system MUST use `git merge-base` to find the common ancestor when comparing against a branch name, to avoid including changes from the target branch itself.

### REQ-003.3: Working Directory

1. All git commands MUST be executed with `cwd` set to `project_root`.
2. The function MUST NOT change the process working directory.

### REQ-003.4: Error Handling

1. If the project is not a git repository, the function MUST raise an error with a descriptive message.
2. If the specified `base_ref` does not exist, the function MUST raise an error with a descriptive message.
3. Git subprocess errors MUST be caught and re-raised with the stderr output included in the error message.
