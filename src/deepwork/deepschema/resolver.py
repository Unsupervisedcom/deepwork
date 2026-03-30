"""Parent schema inheritance resolution for DeepSchemas.

Resolves the parent_deep_schemas chain, merging requirements and
validation commands from parent schemas into children.
"""

from __future__ import annotations

from deepwork.deepschema.config import DeepSchema, DeepSchemaError


def resolve_inheritance(
    schema: DeepSchema,
    named_schemas: dict[str, DeepSchema],
    _visited: set[str] | None = None,
) -> DeepSchema:
    """Resolve parent_deep_schemas inheritance for a single schema.

    Merges parent requirements into the child. Child keys override parent
    on conflict. json_schema_path is inherited if not set on child.
    verification_bash_command is appended (parent commands run first).

    Args:
        schema: The schema to resolve.
        named_schemas: All named schemas keyed by name, for parent lookups.
        _visited: Internal set for circular reference detection.

    Returns:
        A new DeepSchema with inherited fields merged in.

    Raises:
        DeepSchemaError: On circular references or missing parent schemas.
    """
    if not schema.parent_deep_schemas:
        return schema

    if _visited is None:
        _visited = set()

    if schema.name in _visited:
        raise DeepSchemaError(
            f"Circular parent reference detected: '{schema.name}' is in its own inheritance chain"
        )
    _visited.add(schema.name)

    # Collect merged fields from all parents (in order)
    merged_requirements: dict[str, str] = {}
    merged_verification_cmds: list[str] = []
    inherited_json_schema_path: str | None = None

    for parent_name in schema.parent_deep_schemas:
        parent = named_schemas.get(parent_name)
        if parent is None:
            raise DeepSchemaError(
                f"Schema '{schema.name}' references unknown parent '{parent_name}'"
            )

        # Resolve the parent recursively first
        resolved_parent = resolve_inheritance(parent, named_schemas, _visited.copy())

        # Merge requirements (parent first, child overrides)
        merged_requirements.update(resolved_parent.requirements)

        # Append verification commands (parent first)
        merged_verification_cmds.extend(resolved_parent.verification_bash_command)

        # Inherit json_schema_path from first parent that has one
        if inherited_json_schema_path is None and resolved_parent.json_schema_path:
            inherited_json_schema_path = resolved_parent.json_schema_path

    # Child requirements override parent on key conflict
    merged_requirements.update(schema.requirements)

    # Child verification commands come after parent
    merged_verification_cmds.extend(schema.verification_bash_command)

    return DeepSchema(
        name=schema.name,
        schema_type=schema.schema_type,
        source_path=schema.source_path,
        requirements=merged_requirements,
        parent_deep_schemas=schema.parent_deep_schemas,
        json_schema_path=schema.json_schema_path or inherited_json_schema_path,
        verification_bash_command=merged_verification_cmds,
        summary=schema.summary,
        instructions=schema.instructions,
        examples=schema.examples,
        references=schema.references,
        matchers=schema.matchers,
    )


def resolve_all(
    schemas: list[DeepSchema],
) -> tuple[list[DeepSchema], list[str]]:
    """Resolve inheritance for all schemas.

    Args:
        schemas: All discovered schemas.

    Returns:
        Tuple of (resolved schemas, list of error messages).
    """
    named_lookup = {s.name: s for s in schemas if s.schema_type == "named"}
    resolved: list[DeepSchema] = []
    errors: list[str] = []

    for schema in schemas:
        try:
            resolved.append(resolve_inheritance(schema, named_lookup))
        except DeepSchemaError as e:
            errors.append(str(e))

    return resolved, errors
