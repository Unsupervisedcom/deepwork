# REVIEW-REQ-003: Changed File Detection

## Overview

DeepWork Reviews needs to determine which files have changed in order to match them against review rules. Changed files are detected using git, comparing the current state against a base reference (typically the main branch or a specific commit). The detection uses `subprocess` to invoke git directly, since GitPython is a dev-only dependency.

## Requirements

### REVIEW-REQ-003.1: Changed File Retrieval

1. The system MUST provide a `get_changed_files(project_root, base_ref)` function that returns a list of changed file paths relative to the repository root.
2. The function MUST use `subprocess.run()` to invoke `git diff --name-only` with appropriate flags.
3. The function MUST use `--diff-filter=ACMR` to include only Added, Copied, Modified, and Renamed files (excluding Deleted files, since deleted files cannot be reviewed).
4. The function MUST combine committed changes on the branch (since diverging from the base ref), unstaged modifications to tracked files, staged-but-not-committed changes, and untracked files (files not yet added to git) that are not excluded by `.gitignore` into a single deduplicated list. It uses `git ls-files --others --exclude-standard` for untracked file detection.
5. The function MUST operate entirely on local git state. It MUST NOT fetch from or communicate with any remote repository.
6. Changed file paths MUST be returned relative to the git repository root.
7. The returned list MUST be sorted alphabetically.
8. The function MUST raise an error if the `git` command fails (e.g., not a git repository, invalid base ref).

### REVIEW-REQ-003.2: Base Reference

1. The `base_ref` parameter MUST default to `None`.
2. When `base_ref` is `None`, the system MUST auto-detect the merge base by finding the common ancestor between HEAD and the main branch.
3. The system MUST detect the base branch by first querying `git symbolic-ref refs/remotes/origin/HEAD` to discover the remote's default branch. This avoids hardcoding branch names and works for any default branch (main, master, develop, trunk, etc.). If the symbolic ref is not set, the system MUST fall back to checking well-known refs in order: `origin/main`, `origin/master`, `main`, `master`. Remote tracking refs are preferred over local branches because local branches can become stale when the user does not check them out and pull.
4. If none of the candidate refs exist, the system MUST fall back to `HEAD` (uncommitted changes only).
5. Known limitation: the base ref detection always resolves to the repository's default branch. It does not handle stacked PRs (branches based on other feature branches rather than the default branch).
6. When `base_ref` is provided explicitly (e.g., `"main"`, `"HEAD"`, a commit SHA), the system MUST use it directly as the comparison target.
7. The system MUST use `git merge-base` to find the common ancestor when comparing against a branch name, to avoid including changes from the target branch itself.

### REVIEW-REQ-003.3: Working Directory

1. All git commands MUST be executed with `cwd` set to `project_root`.
2. The function MUST NOT change the process working directory.

### REVIEW-REQ-003.4: Error Handling

1. If the project is not a git repository, the function MUST raise an error with a descriptive message.
2. If the specified `base_ref` does not exist, the function MUST raise an error with a descriptive message.
3. Git subprocess errors MUST be caught and re-raised with the stderr output included in the error message.
