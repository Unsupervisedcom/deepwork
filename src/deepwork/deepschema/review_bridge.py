"""Generate synthetic ReviewRule objects from DeepSchemas.

Bridges DeepSchemas into the existing DeepReview pipeline by producing
ReviewRule objects that flow through matching, instruction generation,
and formatting like regular .deepreview rules.
"""

from __future__ import annotations

from pathlib import Path

from deepwork.deepschema.config import DeepSchema
from deepwork.deepschema.discovery import anonymous_target_filename, discover_all_schemas
from deepwork.deepschema.resolver import resolve_all
from deepwork.review.config import ReferenceFile, ReviewRule


def generate_review_rules(
    project_root: Path,
) -> tuple[list[ReviewRule], list[str]]:
    """Discover all DeepSchemas and generate ReviewRules from them.

    Args:
        project_root: Project root for schema discovery.

    Returns:
        Tuple of (ReviewRule list, error messages).
    """
    schemas, discovery_errors = discover_all_schemas(project_root)
    errors = [f"{e.file_path}: {e.error}" for e in discovery_errors]

    resolved, resolve_errors = resolve_all(schemas)
    errors.extend(resolve_errors)

    rules: list[ReviewRule] = []
    for schema in resolved:
        rule = _schema_to_review_rule(schema, project_root)
        if rule is not None:
            refs, ref_errors = _collect_reference_files(schema)
            rule.reference_files = refs
            example_section = _build_examples_section(schema)
            if example_section:
                rule.instructions = rule.instructions.rstrip() + "\n\n" + example_section
            errors.extend(ref_errors)
            rules.append(rule)

    return rules, errors


def _schema_to_review_rule(
    schema: DeepSchema,
    project_root: Path,
) -> ReviewRule | None:
    """Convert a single DeepSchema into a ReviewRule.

    Returns None if the schema has no requirements and no matchers.
    """
    if not schema.requirements:
        return None

    if schema.schema_type == "named":
        return _named_schema_rule(schema, project_root)
    else:
        return _anonymous_schema_rule(schema, project_root)


def _named_schema_rule(
    schema: DeepSchema,
    project_root: Path,
) -> ReviewRule | None:
    """Build a ReviewRule from a named DeepSchema."""
    if not schema.matchers:
        return None

    instructions = _build_named_instructions(schema)

    return ReviewRule(
        name=f"{schema.name} DeepSchema Compliance",
        description=f"DeepSchema compliance review for {schema.name}",
        include_patterns=list(schema.matchers),
        exclude_patterns=[],
        strategy="individual",
        instructions=instructions,
        agent=None,
        all_changed_filenames=False,
        unchanged_matching_files=False,
        precomputed_info_bash_command=None,
        # Named schemas use project-root-relative matchers, so source_dir
        # must be the project root for the review matcher to resolve paths.
        source_dir=project_root,
        source_file=schema.source_path,
        source_line=0,
    )


def _anonymous_schema_rule(
    schema: DeepSchema,
    project_root: Path,
) -> ReviewRule | None:
    """Build a ReviewRule from an anonymous DeepSchema."""
    target_name = anonymous_target_filename(schema.source_path.name)
    target_path = schema.source_path.parent / target_name

    try:
        target_rel = str(target_path.relative_to(project_root))
    except ValueError:
        return None

    instructions = _build_anonymous_instructions(schema)

    return ReviewRule(
        name=f"{target_name} DeepSchema Compliance",
        description=f"DeepSchema compliance review for {target_name}",
        include_patterns=[target_rel],
        exclude_patterns=[],
        strategy="individual",
        instructions=instructions,
        agent=None,
        all_changed_filenames=False,
        unchanged_matching_files=False,
        precomputed_info_bash_command=None,
        source_dir=schema.source_path.parent,
        source_file=schema.source_path,
        source_line=0,
    )


def _build_named_instructions(schema: DeepSchema) -> str:
    """Build review instructions for a named DeepSchema."""
    parts: list[str] = []

    # Intro with summary and instructions
    parts.append(f"{{file_path}} is an instance of {schema.name}.")
    if schema.summary:
        parts.append(f"\n{schema.summary}")
    if schema.instructions:
        parts.append(f"\n\nInstructions for dealing with these files:\n{schema.instructions}")

    # Requirements body
    parts.append("\n\n")
    parts.append(_build_requirements_body(schema.requirements))

    return "".join(parts)


def _build_anonymous_instructions(schema: DeepSchema) -> str:
    """Build review instructions for an anonymous DeepSchema."""
    parts: list[str] = []
    parts.append("{file_path} has requirements that it must follow.")
    parts.append("\n\n")
    parts.append(_build_requirements_body(schema.requirements))
    return "".join(parts)


def _collect_reference_files(
    schema: DeepSchema,
) -> tuple[list[ReferenceFile], list[str]]:
    """Collect ReferenceFile entries from a schema's examples, references, and JSON schema.

    Paths are resolved relative to the schema's source directory
    (``schema.source_path.parent``), matching the convention used by
    existing schema YAML files (e.g. ``json_schema_path: "job.schema.json"``
    in a sibling directory).

    Missing files are skipped and an error string is appended to the
    returned error list so callers can surface it to the user.
    """
    schema_dir = schema.source_path.parent
    refs: list[ReferenceFile] = []
    errors: list[str] = []

    def _add(raw_path: str, description: str | None, source_field: str) -> None:
        # Skip URL-style references — these are informational pointers, not
        # local files to inline.
        if raw_path.startswith(("http://", "https://")):
            return
        resolved = (schema_dir / raw_path).resolve()
        if not resolved.exists():
            errors.append(
                f"{schema.source_path}: {source_field} entry '{raw_path}' not found "
                f"(resolved to {resolved})"
            )
            return
        refs.append(
            ReferenceFile(
                path=resolved,
                relative_label=raw_path,
                description=description,
            )
        )

    # For anonymous schemas, include the governed target file so the
    # reviewer can validate requirements against the actual file content
    # without needing a separate lookup.  (DW-REQ-011.11.7)
    if schema.schema_type == "anonymous":
        target_name = anonymous_target_filename(schema.source_path.name)
        target_path = (schema_dir / target_name).resolve()
        if target_path.exists():
            refs.append(
                ReferenceFile(
                    path=target_path,
                    relative_label=target_name,
                    description=f"Target file governed by this schema",
                )
            )

    # Note: schema.examples are intentionally NOT inlined — they are listed
    # in the instructions via _build_examples_section so reviewers know they
    # exist without bloating the prompt.
    for reference in schema.references:
        path = reference.get("path")
        if path:
            _add(path, reference.get("description"), "references")

    if schema.json_schema_path:
        _add(
            schema.json_schema_path,
            f"JSON Schema for {schema.name}",
            "json_schema_path",
        )

    return refs, errors


def _build_examples_section(schema: DeepSchema) -> str:
    """Build a text section listing the schema's example files by path + description.

    Examples are listed (not inlined) so the reviewer knows what reference
    material exists without bloating the prompt.
    """
    if not schema.examples:
        return ""

    lines = ["Example files available for reference (read on demand):"]
    for example in schema.examples:
        path = example.get("path")
        if not path:
            continue
        description = example.get("description") or ""
        if description:
            lines.append(f"- `{path}` — {description}")
        else:
            lines.append(f"- `{path}`")
    return "\n".join(lines)


def _build_requirements_body(requirements: dict[str, str]) -> str:
    """Build the RFC 2119 requirements review section."""
    req_lines = "\n".join(f"- **{name}**: {desc}" for name, desc in requirements.items())

    return f"""Please review for compliance with the following requirements. You must fail reviews over anything that is MUST. You must fail reviews over any SHOULD that seems like it could be easily followed but is not. You should give feedback but not fail over anything else applicable. You can ignore N/A requirements.

{req_lines}"""
