"""Tests for DTD parser."""

from pathlib import Path

import pytest

from deepwork.core.dtd_parser import (
    DocumentTypeDefinition,
    DTDParseError,
    QualityCriterion,
    load_dtds_from_directory,
    parse_dtd_file,
)


class TestQualityCriterion:
    """Tests for QualityCriterion dataclass."""

    def test_from_dict(self) -> None:
        """Test creating QualityCriterion from dictionary."""
        data = {"name": "Completeness", "description": "Must be complete"}
        criterion = QualityCriterion.from_dict(data)

        assert criterion.name == "Completeness"
        assert criterion.description == "Must be complete"


class TestDocumentTypeDefinition:
    """Tests for DocumentTypeDefinition dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating DTD from minimal dictionary."""
        data = {
            "name": "Test DTD",
            "description": "A test document",
            "quality_criteria": [{"name": "Test", "description": "Test desc"}],
        }
        dtd = DocumentTypeDefinition.from_dict(data)

        assert dtd.name == "Test DTD"
        assert dtd.description == "A test document"
        assert len(dtd.quality_criteria) == 1
        assert dtd.quality_criteria[0].name == "Test"
        assert dtd.path_patterns == []
        assert dtd.target_audience is None
        assert dtd.frequency is None
        assert dtd.example_document == ""

    def test_from_dict_full(self) -> None:
        """Test creating DTD from full dictionary."""
        data = {
            "name": "Full DTD",
            "description": "A complete document",
            "path_patterns": ["reports/*.md"],
            "target_audience": "Team",
            "frequency": "Weekly",
            "quality_criteria": [
                {"name": "Summary", "description": "Include summary"},
                {"name": "Data", "description": "Include data"},
            ],
        }
        dtd = DocumentTypeDefinition.from_dict(
            data, example_document="# Example", source_file=Path("/test/dtd.md")
        )

        assert dtd.name == "Full DTD"
        assert dtd.path_patterns == ["reports/*.md"]
        assert dtd.target_audience == "Team"
        assert dtd.frequency == "Weekly"
        assert len(dtd.quality_criteria) == 2
        assert dtd.example_document == "# Example"
        assert dtd.source_file == Path("/test/dtd.md")


class TestParseDTDFile:
    """Tests for parse_dtd_file function."""

    def test_parses_valid_dtd(self, fixtures_dir: Path) -> None:
        """Test parsing valid DTD file."""
        dtd_file = fixtures_dir / "dtds" / "valid_report.md"
        dtd = parse_dtd_file(dtd_file)

        assert dtd.name == "Monthly Report"
        assert dtd.description == "A monthly summary report"
        assert dtd.path_patterns == ["reports/*.md"]
        assert dtd.target_audience == "Team leads"
        assert dtd.frequency == "Monthly"
        assert len(dtd.quality_criteria) == 2
        assert dtd.quality_criteria[0].name == "Summary"
        assert "Executive Summary" in dtd.example_document
        assert dtd.source_file == dtd_file

    def test_parses_minimal_dtd(self, fixtures_dir: Path) -> None:
        """Test parsing minimal DTD file."""
        dtd_file = fixtures_dir / "dtds" / "minimal_dtd.md"
        dtd = parse_dtd_file(dtd_file)

        assert dtd.name == "Minimal DTD"
        assert dtd.description == "A minimal document type definition"
        assert dtd.path_patterns == []
        assert dtd.target_audience is None
        assert dtd.frequency is None
        assert len(dtd.quality_criteria) == 1

    def test_raises_for_missing_file(self, temp_dir: Path) -> None:
        """Test parsing fails for missing file."""
        nonexistent = temp_dir / "nonexistent.md"

        with pytest.raises(DTDParseError, match="does not exist"):
            parse_dtd_file(nonexistent)

    def test_raises_for_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for directory path."""
        with pytest.raises(DTDParseError, match="not a file"):
            parse_dtd_file(temp_dir)

    def test_raises_for_missing_frontmatter(self, temp_dir: Path) -> None:
        """Test parsing fails for missing frontmatter."""
        dtd_file = temp_dir / "no_frontmatter.md"
        dtd_file.write_text("# Just a document\nNo frontmatter here.")

        with pytest.raises(DTDParseError, match="frontmatter"):
            parse_dtd_file(dtd_file)

    def test_raises_for_invalid_yaml(self, temp_dir: Path) -> None:
        """Test parsing fails for invalid YAML frontmatter."""
        dtd_file = temp_dir / "invalid_yaml.md"
        dtd_file.write_text("---\ninvalid: [yaml: content\n---\n# Doc")

        with pytest.raises(DTDParseError, match="Failed to parse"):
            parse_dtd_file(dtd_file)

    def test_raises_for_empty_frontmatter(self, temp_dir: Path) -> None:
        """Test parsing fails for empty frontmatter."""
        dtd_file = temp_dir / "empty_frontmatter.md"
        dtd_file.write_text("---\n---\n# Doc")

        with pytest.raises(DTDParseError, match="empty"):
            parse_dtd_file(dtd_file)

    def test_raises_for_missing_required_fields(self, temp_dir: Path) -> None:
        """Test parsing fails for missing required fields."""
        dtd_file = temp_dir / "missing_fields.md"
        dtd_file.write_text(
            """---
name: "Test"
---
# Doc"""
        )

        with pytest.raises(DTDParseError, match="validation failed"):
            parse_dtd_file(dtd_file)


class TestLoadDTDsFromDirectory:
    """Tests for load_dtds_from_directory function."""

    def test_loads_all_dtds(self, fixtures_dir: Path) -> None:
        """Test loading all DTDs from directory."""
        dtds_dir = fixtures_dir / "dtds"
        dtds = load_dtds_from_directory(dtds_dir)

        assert "valid_report" in dtds
        assert "minimal_dtd" in dtds
        assert dtds["valid_report"].name == "Monthly Report"
        assert dtds["minimal_dtd"].name == "Minimal DTD"

    def test_returns_empty_for_missing_directory(self, temp_dir: Path) -> None:
        """Test returns empty dict for missing directory."""
        nonexistent = temp_dir / "nonexistent"
        dtds = load_dtds_from_directory(nonexistent)

        assert dtds == {}

    def test_raises_for_file_path(self, temp_dir: Path) -> None:
        """Test raises for file path instead of directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(DTDParseError, match="not a directory"):
            load_dtds_from_directory(file_path)

    def test_returns_empty_for_empty_directory(self, temp_dir: Path) -> None:
        """Test returns empty dict for empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        dtds = load_dtds_from_directory(empty_dir)

        assert dtds == {}

    def test_ignores_non_md_files(self, temp_dir: Path) -> None:
        """Test ignores non-markdown files."""
        dtds_dir = temp_dir / "dtds"
        dtds_dir.mkdir()

        # Create a valid DTD
        (dtds_dir / "valid.md").write_text(
            """---
name: "Valid"
description: "Valid DTD"
quality_criteria:
  - name: Test
    description: Test
---
# Doc"""
        )

        # Create non-markdown file
        (dtds_dir / "readme.txt").write_text("Not a DTD")

        dtds = load_dtds_from_directory(dtds_dir)

        assert len(dtds) == 1
        assert "valid" in dtds
