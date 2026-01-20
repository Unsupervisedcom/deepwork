"""Doc spec parser for document type definitions."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.schemas.doc_spec_schema import DOC_SPEC_FRONTMATTER_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml_from_string


class DocSpecParseError(Exception):
    """Exception raised for doc spec parsing errors."""

    pass


@dataclass
class QualityCriterion:
    """Represents a single quality criterion for a document type."""

    name: str
    description: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityCriterion":
        """Create QualityCriterion from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
        )


@dataclass
class DocumentTypeDefinition:
    """Represents a complete document type definition (doc spec)."""

    # Required fields
    name: str
    description: str
    quality_criteria: list[QualityCriterion]

    # Optional fields
    path_patterns: list[str] = field(default_factory=list)
    target_audience: str | None = None
    frequency: str | None = None

    # The example document body (markdown content after frontmatter)
    example_document: str = ""

    # Source file path for reference
    source_file: Path | None = None

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], example_document: str = "", source_file: Path | None = None
    ) -> "DocumentTypeDefinition":
        """
        Create DocumentTypeDefinition from dictionary.

        Args:
            data: Parsed YAML frontmatter data
            example_document: The markdown body content (example document)
            source_file: Path to the source doc spec file

        Returns:
            DocumentTypeDefinition instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            quality_criteria=[QualityCriterion.from_dict(qc) for qc in data["quality_criteria"]],
            path_patterns=data.get("path_patterns", []),
            target_audience=data.get("target_audience"),
            frequency=data.get("frequency"),
            example_document=example_document,
            source_file=source_file,
        )


def _parse_frontmatter_markdown(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse frontmatter from markdown content.

    Expects format:
    ---
    key: value
    ---
    markdown body

    Args:
        content: Full file content

    Returns:
        Tuple of (frontmatter dict, body content)

    Raises:
        DocSpecParseError: If frontmatter is missing or invalid
    """
    # Match frontmatter pattern: starts with ---, ends with ---
    # The (.*?) captures frontmatter content, which may be empty
    pattern = r"^---[ \t]*\n(.*?)^---[ \t]*\n?(.*)"
    match = re.match(pattern, content.strip(), re.DOTALL | re.MULTILINE)

    if not match:
        raise DocSpecParseError(
            "Doc spec file must have YAML frontmatter (content between --- markers)"
        )

    frontmatter_yaml = match.group(1)
    body = match.group(2).strip() if match.group(2) else ""

    try:
        frontmatter = load_yaml_from_string(frontmatter_yaml)
    except YAMLError as e:
        raise DocSpecParseError(f"Failed to parse doc spec frontmatter: {e}") from e

    if frontmatter is None:
        raise DocSpecParseError("Doc spec frontmatter is empty")

    return frontmatter, body


def parse_doc_spec_file(filepath: Path | str) -> DocumentTypeDefinition:
    """
    Parse a doc spec file.

    Args:
        filepath: Path to the doc spec file (markdown with YAML frontmatter)

    Returns:
        Parsed DocumentTypeDefinition

    Raises:
        DocSpecParseError: If parsing fails or validation errors occur
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise DocSpecParseError(f"Doc spec file does not exist: {filepath}")

    if not filepath.is_file():
        raise DocSpecParseError(f"Doc spec path is not a file: {filepath}")

    # Read content
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        raise DocSpecParseError(f"Failed to read doc spec file: {e}") from e

    # Parse frontmatter and body
    frontmatter, body = _parse_frontmatter_markdown(content)

    # Validate against schema
    try:
        validate_against_schema(frontmatter, DOC_SPEC_FRONTMATTER_SCHEMA)
    except ValidationError as e:
        raise DocSpecParseError(f"Doc spec validation failed: {e}") from e

    # Create doc spec instance
    return DocumentTypeDefinition.from_dict(frontmatter, body, filepath)


def load_doc_specs_from_directory(
    doc_specs_dir: Path | str,
) -> dict[str, DocumentTypeDefinition]:
    """
    Load all doc spec files from a directory.

    Args:
        doc_specs_dir: Path to the doc_specs directory

    Returns:
        Dictionary mapping doc spec filename (without extension) to DocumentTypeDefinition

    Raises:
        DocSpecParseError: If any doc spec file fails to parse
    """
    doc_specs_dir = Path(doc_specs_dir)

    if not doc_specs_dir.exists():
        return {}

    if not doc_specs_dir.is_dir():
        raise DocSpecParseError(f"Doc specs path is not a directory: {doc_specs_dir}")

    doc_specs: dict[str, DocumentTypeDefinition] = {}

    for doc_spec_file in doc_specs_dir.glob("*.md"):
        # Use stem (filename without extension) as key
        doc_spec_key = doc_spec_file.stem

        try:
            doc_spec = parse_doc_spec_file(doc_spec_file)
            doc_specs[doc_spec_key] = doc_spec
        except DocSpecParseError:
            # Re-raise with context about which file failed
            raise

    return doc_specs
