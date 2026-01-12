"""Filesystem utilities for safe file operations."""

import shutil
from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path to create

    Returns:
        Path object for the created/existing directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_write(path: Path | str, content: str) -> None:
    """
    Write content to file, creating parent directories if needed.

    Args:
        path: File path to write to
        content: Content to write

    Raises:
        OSError: If write operation fails
    """
    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    path_obj.write_text(content, encoding="utf-8")


def safe_read(path: Path | str) -> str | None:
    """
    Read content from file, return None if file doesn't exist.

    Args:
        path: File path to read from

    Returns:
        File content as string, or None if file doesn't exist

    Raises:
        OSError: If read operation fails for reasons other than file not existing
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return None
    return path_obj.read_text(encoding="utf-8")


def copy_dir(src: Path | str, dst: Path | str, ignore_patterns: list[str] | None = None) -> None:
    """
    Recursively copy directory, optionally ignoring patterns.

    Args:
        src: Source directory path
        dst: Destination directory path
        ignore_patterns: Optional list of glob patterns to ignore

    Raises:
        FileNotFoundError: If source directory doesn't exist
        OSError: If copy operation fails
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_path}")

    if not src_path.is_dir():
        raise NotADirectoryError(f"Source is not a directory: {src_path}")

    # Create ignore function if patterns provided
    ignore_func = None
    if ignore_patterns:

        def _ignore(directory: str, contents: list[str]) -> set[str]:
            ignored = set()
            dir_path = Path(directory)
            for item in contents:
                item_path = dir_path / item
                for pattern in ignore_patterns:
                    if item_path.match(pattern):
                        ignored.add(item)
                        break
            return ignored

        ignore_func = _ignore

    shutil.copytree(src_path, dst_path, ignore=ignore_func, dirs_exist_ok=True)


def find_files(directory: Path | str, pattern: str) -> list[Path]:
    """
    Find files matching glob pattern in directory.

    Args:
        directory: Directory to search in
        pattern: Glob pattern to match (e.g., "*.py", "**/*.md")

    Returns:
        List of matching file paths (sorted)

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {dir_path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    # Use rglob for ** patterns, otherwise use glob
    if "**" in pattern:
        matches = dir_path.glob(pattern)
    else:
        matches = dir_path.glob(pattern)

    # Return only files, not directories, sorted by path
    return sorted([p for p in matches if p.is_file()])
