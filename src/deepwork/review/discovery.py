"""Discovery of .deepreview configuration files in the project tree.

Walks the project directory to find all .deepreview files and parses
them into ReviewRule objects.
"""

from dataclasses import dataclass
from pathlib import Path

from deepwork.review.config import ConfigError, ReviewRule, parse_deepreview_file

# Directories to skip during discovery
_SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".eggs",
}

# Suffix patterns that can't be matched via set membership
_SKIP_SUFFIXES = (".egg-info",)

DEEPREVIEW_FILENAME = ".deepreview"


@dataclass
class DiscoveryError:
    """An error encountered while loading a .deepreview file."""

    file_path: Path
    error: str


def find_deepreview_files(project_root: Path) -> list[Path]:
    """Find all .deepreview files in the project directory tree.

    Walks project_root and its subdirectories recursively, skipping
    common non-source directories (.git, node_modules, etc.).

    Args:
        project_root: Root directory to search.

    Returns:
        List of .deepreview file paths, sorted by depth (deepest first),
        then alphabetically within the same depth.
    """
    results: list[Path] = []

    for path in _walk_for_file(project_root, DEEPREVIEW_FILENAME):
        results.append(path)

    # Sort by depth (deepest first), then alphabetically
    root_depth = len(project_root.parts)
    results.sort(key=lambda p: (-len(p.parts) + root_depth, str(p)))

    return results


def _walk_for_file(root: Path, filename: str) -> list[Path]:
    """Walk directory tree looking for files with the given name.

    Skips directories in _SKIP_DIRS.

    Args:
        root: Root directory to walk.
        filename: Exact filename to look for.

    Returns:
        List of matching file paths.
    """
    results: list[Path] = []

    try:
        entries = sorted(root.iterdir())
    except PermissionError:
        return results

    for entry in entries:
        if entry.is_file() and entry.name == filename:
            results.append(entry)
        elif (
            entry.is_dir()
            and entry.name not in _SKIP_DIRS
            and not entry.name.endswith(_SKIP_SUFFIXES)
        ):
            results.extend(_walk_for_file(entry, filename))

    return results


def load_all_rules(
    project_root: Path,
) -> tuple[list[ReviewRule], list[DiscoveryError]]:
    """Discover all .deepreview files and parse them into rules.

    Args:
        project_root: Root directory to search.

    Returns:
        Tuple of (successfully parsed rules, list of errors).
    """
    files = find_deepreview_files(project_root)
    all_rules: list[ReviewRule] = []
    errors: list[DiscoveryError] = []

    for filepath in files:
        try:
            rules = parse_deepreview_file(filepath)
            all_rules.extend(rules)
        except ConfigError as e:
            errors.append(DiscoveryError(file_path=filepath, error=str(e)))

    return all_rules, errors
