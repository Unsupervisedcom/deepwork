"""Document Type Definition (DTD) parser."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.schemas.dtd_schema import DTD_FRONTMATTER_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml_from_string


class DTDParseError(Exception):
    """Exception raised for DTD parsing errors."""

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
    """Represents a complete Document Type Definition."""

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
            source_file: Path to the source DTD file

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
        DTDParseError: If frontmatter is missing or invalid
    """
    # Match frontmatter pattern: starts with ---, ends with ---
    # The (.*?) captures frontmatter content, which may be empty
    pattern = r"^---[ \t]*\n(.*?)^---[ \t]*\n?(.*)"
    match = re.match(pattern, content.strip(), re.DOTALL | re.MULTILINE)

    if not match:
        raise DTDParseError("DTD file must have YAML frontmatter (content between --- markers)")

    frontmatter_yaml = match.group(1)
    body = match.group(2).strip() if match.group(2) else ""

    try:
        frontmatter = load_yaml_from_string(frontmatter_yaml)
    except YAMLError as e:
        raise DTDParseError(f"Failed to parse DTD frontmatter: {e}") from e

    if frontmatter is None:
        raise DTDParseError("DTD frontmatter is empty")

    return frontmatter, body


def parse_dtd_file(filepath: Path | str) -> DocumentTypeDefinition:
    """
    Parse a DTD file.

    Args:
        filepath: Path to the DTD file (markdown with YAML frontmatter)

    Returns:
        Parsed DocumentTypeDefinition

    Raises:
        DTDParseError: If parsing fails or validation errors occur
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise DTDParseError(f"DTD file does not exist: {filepath}")

    if not filepath.is_file():
        raise DTDParseError(f"DTD path is not a file: {filepath}")

    # Read content
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        raise DTDParseError(f"Failed to read DTD file: {e}") from e

    # Parse frontmatter and body
    frontmatter, body = _parse_frontmatter_markdown(content)

    # Validate against schema
    try:
        validate_against_schema(frontmatter, DTD_FRONTMATTER_SCHEMA)
    except ValidationError as e:
        raise DTDParseError(f"DTD validation failed: {e}") from e

    # Create DTD instance
    return DocumentTypeDefinition.from_dict(frontmatter, body, filepath)


def load_dtds_from_directory(dtds_dir: Path | str) -> dict[str, DocumentTypeDefinition]:
    """
    Load all DTD files from a directory.

    Args:
        dtds_dir: Path to the DTDs directory

    Returns:
        Dictionary mapping DTD filename (without extension) to DocumentTypeDefinition

    Raises:
        DTDParseError: If any DTD file fails to parse
    """
    dtds_dir = Path(dtds_dir)

    if not dtds_dir.exists():
        return {}

    if not dtds_dir.is_dir():
        raise DTDParseError(f"DTDs path is not a directory: {dtds_dir}")

    dtds: dict[str, DocumentTypeDefinition] = {}

    for dtd_file in dtds_dir.glob("*.md"):
        # Use stem (filename without extension) as key
        dtd_key = dtd_file.stem

        try:
            dtd = parse_dtd_file(dtd_file)
            dtds[dtd_key] = dtd
        except DTDParseError:
            # Re-raise with context about which file failed
            raise

    return dtds
