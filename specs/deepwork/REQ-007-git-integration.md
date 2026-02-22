# REQ-007: Git Integration

## Overview

DeepWork provides Git utility functions for repository operations including branch management, status checking, and repository introspection. These utilities support the workflow's Git-native architecture where work products are versioned on dedicated branches. The git module uses GitPython for repository operations.

## Requirements

### REQ-007.1: Repository Detection

1. `is_git_repo(path)` MUST return `True` if the given path is inside a Git repository.
2. `is_git_repo(path)` MUST return `False` if the given path is not inside a Git repository.
3. `is_git_repo()` MUST search parent directories for the Git repository root.

### REQ-007.2: Repository Access

1. `get_repo(path)` MUST return a GitPython `Repo` object for the given path.
2. `get_repo(path)` MUST search parent directories for the Git repository root.
3. `get_repo(path)` MUST raise `GitError` if the path is not inside a Git repository.
4. `get_repo_root(path)` MUST return the `Path` to the repository root (working tree directory).
5. `get_repo_root(path)` MUST raise `GitError` if the path is not inside a Git repository.

### REQ-007.3: Branch Operations

1. `get_current_branch(path)` MUST return the name of the currently checked-out branch.
2. `get_current_branch(path)` MUST raise `GitError` if HEAD is detached (not on any branch).
3. `get_current_branch(path)` MUST raise `GitError` if the path is not inside a Git repository.
4. `branch_exists(path, name)` MUST return `True` if a branch with the given name exists in the repository.
5. `branch_exists(path, name)` MUST return `False` if no branch with the given name exists.
6. `create_branch(path, name)` MUST create a new branch with the given name.
7. `create_branch(path, name)` MUST raise `GitError` if a branch with that name already exists.
8. `create_branch(path, name, checkout=True)` MUST check out the newly created branch after creation.
9. `create_branch(path, name, checkout=False)` (the default) MUST NOT check out the new branch.
10. `create_branch()` MUST raise `GitError` if the branch creation fails for any other reason.

### REQ-007.4: Repository Status

1. `has_uncommitted_changes(path)` MUST return `True` if the repository has staged changes, unstaged changes, or untracked files.
2. `has_uncommitted_changes(path)` MUST return `False` if the working tree is clean with no untracked files.
3. `get_untracked_files(path)` MUST return a list of untracked file paths in the repository.
4. `get_untracked_files(path)` MUST return an empty list if there are no untracked files.

### REQ-007.5: Error Handling

1. All Git utility functions MUST raise `GitError` (not raw GitPython exceptions) for Git-related failures.
2. `GitError` MUST include a descriptive message about the failure.
