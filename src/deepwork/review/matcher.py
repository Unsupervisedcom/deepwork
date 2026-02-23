"""Changed file detection and rule matching.

Detects changed files via git and matches them against ReviewRule glob
patterns, grouping results into ReviewTask objects according to the
rule's review strategy.
"""

import re
import subprocess
from pathlib import Path

from deepwork.review.config import ReviewRule, ReviewTask


class GitDiffError(Exception):
    """Exception raised for git diff operation errors."""

    pass


def get_changed_files(project_root: Path, base_ref: str | None = None) -> list[str]:
    """Get list of changed files relative to the repository root.

    Uses git diff to detect Added, Copied, Modified, and Renamed files.
    Combines unstaged and staged changes into a deduplicated list.

    Args:
        project_root: Path to the project (must be in a git repo).
        base_ref: Git ref to diff against. If None, auto-detects
            merge-base with main/master branch. Falls back to HEAD.

    Returns:
        Sorted list of changed file paths relative to repo root.

    Raises:
        GitDiffError: If git operations fail.
    """
    if base_ref is None:
        base_ref = _detect_base_ref(project_root)

    # Get the merge-base to avoid including changes from the target branch
    merge_base = _get_merge_base(project_root, base_ref)

    # Get changed files (unstaged + committed on branch)
    diff_files = _git_diff_name_only(project_root, merge_base)

    # Also get staged changes (not yet committed)
    staged_files = _git_diff_name_only(project_root, None, staged=True)

    return sorted(set(diff_files + staged_files))


def _detect_base_ref(project_root: Path) -> str:
    """Auto-detect the base branch to diff against.

    Queries ``git symbolic-ref refs/remotes/origin/HEAD`` to discover the
    remote's default branch. This works regardless of whether the default
    branch is called main, master, develop, trunk, etc.

    Falls back to a hardcoded list (origin/main, origin/master, then local
    main/master) when the symbolic ref is not set, and finally to HEAD.

    Known limitation: this always resolves to the repository's default
    branch. It does not handle the case where the current branch is based
    on another feature branch (i.e. stacked PRs / PRs off other PRs).
    That would require querying the hosting platform (e.g. GitHub) for the
    PR's base ref.

    Args:
        project_root: Path to the project root.

    Returns:
        Git ref string to use as base ref.
    """
    # Try the remote HEAD symbolic ref first — this is the most reliable
    # way to find the default branch without hardcoding names.
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        # Returns e.g. "refs/remotes/origin/main" — strip to "origin/main"
        full_ref = result.stdout.strip()
        short_ref = full_ref.removeprefix("refs/remotes/")
        # Verify the ref actually resolves to a commit
        subprocess.run(
            ["git", "rev-parse", "--verify", short_ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return short_ref
    except subprocess.CalledProcessError:
        pass

    # Fallback: try well-known branch names
    for ref in ("origin/main", "origin/master", "main", "master"):
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", ref],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return ref
        except subprocess.CalledProcessError:
            continue
    return "HEAD"


def _get_merge_base(project_root: Path, ref: str) -> str:
    """Get the merge-base between HEAD and the given ref.

    If ref is HEAD, returns HEAD directly.

    Args:
        project_root: Path to the project root.
        ref: Git ref to find merge-base with.

    Returns:
        The merge-base commit SHA, or the ref itself for HEAD.

    Raises:
        GitDiffError: If the git command fails.
    """
    if ref == "HEAD":
        return "HEAD"

    try:
        result = subprocess.run(
            ["git", "merge-base", "HEAD", ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitDiffError(f"Failed to find merge-base with '{ref}': {e.stderr.strip()}") from e


def _git_diff_name_only(project_root: Path, ref: str | None, *, staged: bool = False) -> list[str]:
    """Run git diff --name-only and return the list of files.

    Args:
        project_root: Path to the project root.
        ref: Git ref to diff against. If None and staged=True, diffs staged changes.
        staged: If True, include --cached flag for staged changes.

    Returns:
        List of changed file paths.

    Raises:
        GitDiffError: If the git command fails.
    """
    cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR"]
    if staged:
        cmd.append("--cached")
    if ref is not None:
        cmd.append(ref)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError as e:
        raise GitDiffError(f"git diff failed: {e.stderr.strip()}") from e


def match_files_to_rules(
    changed_files: list[str],
    rules: list[ReviewRule],
    project_root: Path,
    platform: str = "claude",
) -> list[ReviewTask]:
    """Match changed files against rules and produce ReviewTask objects.

    Each rule is processed independently. A file can match multiple rules
    and appear in multiple tasks.

    Args:
        changed_files: List of changed file paths relative to repo root.
        rules: List of ReviewRule objects to match against.
        project_root: Absolute path to the project root.
        platform: Target platform for agent resolution (e.g., "claude").

    Returns:
        List of ReviewTask objects.
    """
    tasks: list[ReviewTask] = []

    for rule in rules:
        matched = match_rule(changed_files, rule, project_root)
        if not matched:
            continue

        agent_name = _resolve_agent(rule, platform)
        all_filenames = changed_files if rule.all_changed_filenames else None
        source_location = format_source_location(rule, project_root)

        if rule.strategy == "individual":
            for filepath in matched:
                tasks.append(
                    ReviewTask(
                        rule_name=rule.name,
                        files_to_review=[filepath],
                        instructions=rule.instructions,
                        agent_name=agent_name,
                        source_location=source_location,
                        all_changed_filenames=all_filenames,
                    )
                )

        elif rule.strategy == "matches_together":
            additional = []
            if rule.unchanged_matching_files:
                additional = _find_unchanged_matching_files(changed_files, rule, project_root)
            tasks.append(
                ReviewTask(
                    rule_name=rule.name,
                    files_to_review=matched,
                    instructions=rule.instructions,
                    agent_name=agent_name,
                    source_location=source_location,
                    additional_files=additional,
                    all_changed_filenames=all_filenames,
                )
            )

        elif rule.strategy == "all_changed_files":
            tasks.append(
                ReviewTask(
                    rule_name=rule.name,
                    files_to_review=list(changed_files),
                    instructions=rule.instructions,
                    agent_name=agent_name,
                    source_location=source_location,
                    all_changed_filenames=all_filenames,
                )
            )

    return tasks


def match_rule(changed_files: list[str], rule: ReviewRule, project_root: Path) -> list[str]:
    """Find changed files that match a rule's include/exclude patterns.

    Patterns are resolved relative to the rule's source_dir.

    Args:
        changed_files: List of changed file paths relative to repo root.
        rule: The ReviewRule to match against.
        project_root: Absolute path to the project root.

    Returns:
        List of matched file paths (relative to repo root).
    """
    matched: list[str] = []
    source_dir = rule.source_dir

    # Compute source_dir relative to project_root for path comparison
    try:
        source_rel = source_dir.relative_to(project_root)
    except ValueError:
        # source_dir is not under project_root — skip this rule
        return []

    for filepath in changed_files:
        # Check if file is under the rule's source directory
        rel_to_source = _relative_to_dir(filepath, str(source_rel))
        if rel_to_source is None:
            continue

        # Check include patterns
        if not any(_glob_match(rel_to_source, pattern) for pattern in rule.include_patterns):
            continue

        # Check exclude patterns
        if any(_glob_match(rel_to_source, pattern) for pattern in rule.exclude_patterns):
            continue

        matched.append(filepath)

    return matched


def _relative_to_dir(filepath: str, dir_path: str) -> str | None:
    """Compute a filepath relative to a directory.

    Both paths should be relative to the same root. If the file is not
    under the directory, returns None.

    Args:
        filepath: File path (relative to some root).
        dir_path: Directory path (relative to the same root).

    Returns:
        The filepath relative to dir_path, or None if not under it.
    """
    if dir_path == "" or dir_path == ".":
        return filepath

    prefix = dir_path.rstrip("/") + "/"
    if filepath.startswith(prefix):
        return filepath[len(prefix) :]

    return None


def _glob_match(filepath: str, pattern: str) -> bool:
    """Match a file path against a glob pattern.

    Uses glob semantics: ``*`` matches within a single path component
    (does not cross ``/``), and ``**`` matches zero or more path components.

    Args:
        filepath: File path to check (relative to rule source dir).
        pattern: Glob pattern to match against.

    Returns:
        True if the filepath matches the pattern.
    """
    regex = _glob_to_regex(pattern)
    return bool(re.match(regex, filepath))


def _glob_to_regex(pattern: str) -> str:
    """Convert a glob pattern to an anchored regex.

    - ``**`` matches zero or more path components (including separators).
    - ``*`` matches any characters except ``/``.
    - ``?`` matches any single character except ``/``.
    - All other characters are escaped.

    Args:
        pattern: Glob pattern string.

    Returns:
        Regex pattern string anchored with ``^...$``.
    """
    parts: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        if i + 1 < n and pattern[i : i + 2] == "**":
            # ** followed by / matches zero or more directories
            if i + 2 < n and pattern[i + 2] == "/":
                parts.append("(?:.+/)?")
                i += 3
            else:
                # ** at end matches everything remaining
                parts.append(".*")
                i += 2
        elif pattern[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(pattern[i]))
            i += 1
    return "^" + "".join(parts) + "$"


def _resolve_agent(rule: ReviewRule, platform: str) -> str | None:
    """Resolve the agent persona for the target platform.

    Args:
        rule: The ReviewRule to check.
        platform: Target platform (e.g., "claude").

    Returns:
        Agent persona name, or None if not specified.
    """
    if rule.agent is None:
        return None
    return rule.agent.get(platform)


def format_source_location(rule: ReviewRule, project_root: Path) -> str:
    """Format the source location of a rule as 'relative/path:line'.

    Args:
        rule: The ReviewRule with source_file and source_line.
        project_root: Project root for computing relative paths.

    Returns:
        Source location string (e.g., "src/.deepreview:5").
    """
    try:
        rel_path = rule.source_file.relative_to(project_root)
    except ValueError:
        rel_path = rule.source_file
    return f"{rel_path}:{rule.source_line}"


def _find_unchanged_matching_files(
    changed_files: list[str],
    rule: ReviewRule,
    project_root: Path,
) -> list[str]:
    """Find files that match the rule's patterns but were not changed.

    Scans the filesystem under the rule's source_dir for files matching
    the include patterns (minus exclude patterns), then removes any that
    appear in the changed files list.

    Args:
        changed_files: List of changed file paths relative to repo root.
        rule: The ReviewRule with include/exclude patterns.
        project_root: Absolute path to the project root.

    Returns:
        List of unchanged matching file paths (relative to repo root).
    """
    source_dir = rule.source_dir
    changed_set = set(changed_files)
    unchanged: list[str] = []

    try:
        source_rel = source_dir.relative_to(project_root)
    except ValueError:
        return []

    # Walk the source directory for matching files.
    # We intentionally follow symlinks here so that symlinked source trees
    # are included in the unchanged-file search.
    for include_pattern in rule.include_patterns:
        for match_path in source_dir.glob(include_pattern):
            if not match_path.is_file():
                continue

            # Get path relative to project root
            try:
                rel_path = str(match_path.relative_to(project_root))
            except ValueError:
                continue

            # Skip if it's a changed file
            if rel_path in changed_set:
                continue

            # Get path relative to source dir for exclude check
            rel_to_source = _relative_to_dir(rel_path, str(source_rel))
            if rel_to_source is None:
                continue

            # Check exclude patterns
            if any(_glob_match(rel_to_source, pattern) for pattern in rule.exclude_patterns):
                continue

            unchanged.append(rel_path)

    return sorted(set(unchanged))
