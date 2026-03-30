"""Schema-to-file matching for DeepSchemas.

Computes which DeepSchemas are applicable to a given file path, using
glob matchers for named schemas and naming conventions for anonymous schemas.
"""

from __future__ import annotations

from pathlib import Path

from deepwork.deepschema.config import DeepSchema
from deepwork.deepschema.discovery import (
    ANONYMOUS_PREFIX,
    ANONYMOUS_SUFFIX,
    anonymous_target_filename,
    find_named_schemas,
)
from deepwork.review.matcher import _glob_match


def get_applicable_schemas(
    filepath: str,
    schemas: list[DeepSchema],
    project_root: Path,
) -> list[DeepSchema]:
    """Find all DeepSchemas applicable to a given file path.

    Args:
        filepath: File path relative to project root.
        schemas: All discovered (and resolved) schemas.
        project_root: Project root for resolving paths.

    Returns:
        List of applicable DeepSchema objects.
    """
    applicable: list[DeepSchema] = []

    for schema in schemas:
        if schema.schema_type == "named":
            if _named_schema_matches(filepath, schema, project_root):
                applicable.append(schema)
        elif schema.schema_type == "anonymous":
            if _anonymous_schema_matches(filepath, schema, project_root):
                applicable.append(schema)

    return applicable


def get_schemas_for_file_fast(
    filepath: str,
    project_root: Path,
) -> list[DeepSchema]:
    """Fast path for hooks: find schemas applicable to a single file.

    Avoids full tree walk. Only scans .deepwork/schemas/ (bounded) and
    checks the file's parent directory for an anonymous schema (O(1) stat).

    Args:
        filepath: File path relative to project root.
        project_root: Project root for resolving paths.

    Returns:
        List of applicable DeepSchema objects (not inheritance-resolved).
    """
    from deepwork.deepschema.config import DeepSchemaError, parse_deepschema_file

    applicable: list[DeepSchema] = []

    # Check named schemas
    for manifest_path in find_named_schemas(project_root):
        name = manifest_path.parent.name
        try:
            schema = parse_deepschema_file(manifest_path, "named", name)
        except DeepSchemaError:
            continue
        if _named_schema_matches(filepath, schema, project_root):
            applicable.append(schema)

    # Check for anonymous schema in same directory
    abs_filepath = project_root / filepath
    parent_dir = abs_filepath.parent
    basename = abs_filepath.name
    anonymous_path = parent_dir / f"{ANONYMOUS_PREFIX}{basename}{ANONYMOUS_SUFFIX}"
    if anonymous_path.is_file():
        try:
            schema = parse_deepschema_file(anonymous_path, "anonymous", basename)
            applicable.append(schema)
        except DeepSchemaError:
            pass

    return applicable


def _named_schema_matches(
    filepath: str,
    schema: DeepSchema,
    project_root: Path,
) -> bool:
    """Check if a named schema's matchers match the given file path."""
    for pattern in schema.matchers:
        if _glob_match(filepath, pattern):
            return True
    return False


def _anonymous_schema_matches(
    filepath: str,
    schema: DeepSchema,
    project_root: Path,
) -> bool:
    """Check if an anonymous schema applies to the given file path.

    An anonymous schema at /dir/.deepschema.foo.py.yml applies to /dir/foo.py.
    """
    schema_dir = schema.source_path.parent
    target_name = anonymous_target_filename(schema.source_path.name)
    target_path = schema_dir / target_name

    # Compare relative to project root
    try:
        target_rel = str(target_path.relative_to(project_root))
    except ValueError:
        return False

    return filepath == target_rel
