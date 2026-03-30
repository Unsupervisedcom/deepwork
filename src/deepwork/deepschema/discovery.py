"""Discovery of DeepSchema definitions in the project tree.

Named schemas are discovered from multiple sources in priority order:

1. ``<project_root>/.deepwork/schemas`` – project-local named schemas
2. ``<package>/standard_schemas``       – built-in standard schemas shipped with DeepWork
3. ``DEEPWORK_ADDITIONAL_SCHEMAS_FOLDERS`` env var – colon-delimited list of extra directories

Each additional directory is scanned for subdirectories containing ``deepschema.yml``.
If the same schema name appears in multiple sources, the first one wins (project-local
overrides standard, standard overrides env var extras).

Anonymous schemas (``.deepschema.<filename>.yml``) are found by walking the project tree.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from deepwork.deepschema.config import DeepSchema, DeepSchemaError, parse_deepschema_file

# Directories to skip during anonymous schema discovery
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

_SKIP_SUFFIXES = (".egg-info",)

NAMED_SCHEMAS_DIR = ".deepwork/schemas"
ANONYMOUS_PREFIX = ".deepschema."
ANONYMOUS_SUFFIX = ".yml"

# Environment variable for additional schema folders (colon-delimited)
ENV_ADDITIONAL_SCHEMAS_FOLDERS = "DEEPWORK_ADDITIONAL_SCHEMAS_FOLDERS"

# Location of built-in standard schemas inside the package
_STANDARD_SCHEMAS_DIR = Path(__file__).parent.parent / "standard_schemas"


@dataclass
class DiscoveryError:
    """An error encountered while loading a DeepSchema file."""

    file_path: Path
    error: str


def get_named_schema_folders(project_root: Path) -> list[Path]:
    """Return the ordered list of directories to scan for named schemas.

    Priority order (first match wins on name conflict):
    1. <project_root>/.deepwork/schemas – project-local
    2. <package>/standard_schemas – built-in
    3. DEEPWORK_ADDITIONAL_SCHEMAS_FOLDERS – env var extras
    """
    folders: list[Path] = [
        project_root / NAMED_SCHEMAS_DIR,
        _STANDARD_SCHEMAS_DIR,
    ]

    extra = os.environ.get(ENV_ADDITIONAL_SCHEMAS_FOLDERS, "")
    if extra:
        for entry in extra.split(":"):
            entry = entry.strip()
            if entry:
                folders.append(Path(entry))

    return folders


def find_named_schemas(project_root: Path) -> list[Path]:
    """Find all named DeepSchema manifest files across all schema folders.

    Scans each folder from get_named_schema_folders(). If the same schema
    name (directory name) appears in multiple folders, the first one wins.

    Args:
        project_root: Root directory of the project.

    Returns:
        List of deepschema.yml paths, deduplicated by schema name.
    """
    seen_names: set[str] = set()
    results: list[Path] = []

    for folder in get_named_schema_folders(project_root):
        if not folder.is_dir():
            continue
        try:
            for entry in sorted(folder.iterdir()):
                if entry.is_dir() and entry.name not in seen_names:
                    manifest = entry / "deepschema.yml"
                    if manifest.is_file():
                        results.append(manifest)
                        seen_names.add(entry.name)
        except PermissionError:
            continue

    return results


def find_anonymous_schemas(project_root: Path) -> list[Path]:
    """Find all anonymous DeepSchema files in the project tree.

    Walks the project looking for files matching .deepschema.<filename>.yml.

    Args:
        project_root: Root directory to search.

    Returns:
        List of anonymous schema file paths, sorted alphabetically.
    """
    results: list[Path] = []
    _walk_for_anonymous(project_root, results)
    results.sort(key=str)
    return results


def _walk_for_anonymous(root: Path, results: list[Path]) -> None:
    """Walk directory tree looking for .deepschema.*.yml files."""
    try:
        entries = sorted(root.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if entry.is_file() and _is_anonymous_schema(entry.name):
            results.append(entry)
        elif (
            entry.is_dir()
            and entry.name not in _SKIP_DIRS
            and not entry.name.endswith(_SKIP_SUFFIXES)
        ):
            _walk_for_anonymous(entry, results)


def _is_anonymous_schema(filename: str) -> bool:
    """Check if a filename matches the .deepschema.<name>.yml pattern."""
    return (
        filename.startswith(ANONYMOUS_PREFIX)
        and filename.endswith(ANONYMOUS_SUFFIX)
        and len(filename) > len(ANONYMOUS_PREFIX) + len(ANONYMOUS_SUFFIX)
    )


def anonymous_target_filename(schema_filename: str) -> str:
    """Extract the target filename from an anonymous schema filename.

    ".deepschema.foo.py.yml" -> "foo.py"
    """
    return schema_filename[len(ANONYMOUS_PREFIX) : -len(ANONYMOUS_SUFFIX)]


def discover_all_schemas(
    project_root: Path,
) -> tuple[list[DeepSchema], list[DiscoveryError]]:
    """Discover all DeepSchemas (named and anonymous) in the project.

    Named schemas are loaded from all configured folders (project-local,
    standard, and env var). Anonymous schemas are found by walking the
    project tree.

    Args:
        project_root: Root directory to search.

    Returns:
        Tuple of (successfully parsed schemas, list of errors).
    """
    schemas: list[DeepSchema] = []
    errors: list[DiscoveryError] = []

    # Named schemas (from all sources, deduplicated)
    for manifest_path in find_named_schemas(project_root):
        name = manifest_path.parent.name
        try:
            schema = parse_deepschema_file(manifest_path, "named", name)
            schemas.append(schema)
        except DeepSchemaError as e:
            errors.append(DiscoveryError(file_path=manifest_path, error=str(e)))

    # Anonymous schemas
    for schema_path in find_anonymous_schemas(project_root):
        target = anonymous_target_filename(schema_path.name)
        try:
            schema = parse_deepschema_file(schema_path, "anonymous", target)
            schemas.append(schema)
        except DeepSchemaError as e:
            errors.append(DiscoveryError(file_path=schema_path, error=str(e)))

    return schemas, errors
