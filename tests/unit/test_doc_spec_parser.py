"""Tests for doc spec parser."""

from pathlib import Path

import pytest

from deepwork.core.doc_spec_parser import (
    DocSpecParseError,
    DocumentTypeDefinition,
    QualityCriterion,
    load_doc_specs_from_directory,
    parse_doc_spec_file,
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
        """Test creating doc spec from minimal dictionary."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document",
            "quality_criteria": [{"name": "Test", "description": "Test desc"}],
        }
        doc_spec = DocumentTypeDefinition.from_dict(data)

        assert doc_spec.name == "Test Doc Spec"
        assert doc_spec.description == "A test document"
        assert len(doc_spec.quality_criteria) == 1
        assert doc_spec.quality_criteria[0].name == "Test"
        assert doc_spec.path_patterns == []
        assert doc_spec.target_audience is None
        assert doc_spec.frequency is None
        assert doc_spec.example_document == ""

    def test_from_dict_full(self) -> None:
        """Test creating doc spec from full dictionary."""
        data = {
            "name": "Full Doc Spec",
            "description": "A complete document",
            "path_patterns": ["reports/*.md"],
            "target_audience": "Team",
            "frequency": "Weekly",
            "quality_criteria": [
                {"name": "Summary", "description": "Include summary"},
                {"name": "Data", "description": "Include data"},
            ],
        }
        doc_spec = DocumentTypeDefinition.from_dict(
            data, example_document="# Example", source_file=Path("/test/doc_spec.md")
        )

        assert doc_spec.name == "Full Doc Spec"
        assert doc_spec.path_patterns == ["reports/*.md"]
        assert doc_spec.target_audience == "Team"
        assert doc_spec.frequency == "Weekly"
        assert len(doc_spec.quality_criteria) == 2
        assert doc_spec.example_document == "# Example"
        assert doc_spec.source_file == Path("/test/doc_spec.md")


class TestParseDocSpecFile:
    """Tests for parse_doc_spec_file function."""

    def test_parses_valid_doc_spec(self, fixtures_dir: Path) -> None:
        """Test parsing valid doc spec file."""
        doc_spec_file = fixtures_dir / "doc_specs" / "valid_report.md"
        doc_spec = parse_doc_spec_file(doc_spec_file)

        assert doc_spec.name == "Monthly Report"
        assert doc_spec.description == "A monthly summary report"
        assert doc_spec.path_patterns == ["reports/*.md"]
        assert doc_spec.target_audience == "Team leads"
        assert doc_spec.frequency == "Monthly"
        assert len(doc_spec.quality_criteria) == 2
        assert doc_spec.quality_criteria[0].name == "Summary"
        assert "Executive Summary" in doc_spec.example_document
        assert doc_spec.source_file == doc_spec_file

    def test_parses_minimal_doc_spec(self, fixtures_dir: Path) -> None:
        """Test parsing minimal doc spec file."""
        doc_spec_file = fixtures_dir / "doc_specs" / "minimal_doc_spec.md"
        doc_spec = parse_doc_spec_file(doc_spec_file)

        assert doc_spec.name == "Minimal Doc Spec"
        assert doc_spec.description == "A minimal document type definition"
        assert doc_spec.path_patterns == []
        assert doc_spec.target_audience is None
        assert doc_spec.frequency is None
        assert len(doc_spec.quality_criteria) == 1

    def test_raises_for_missing_file(self, temp_dir: Path) -> None:
        """Test parsing fails for missing file."""
        nonexistent = temp_dir / "nonexistent.md"

        with pytest.raises(DocSpecParseError, match="does not exist"):
            parse_doc_spec_file(nonexistent)

    def test_raises_for_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for directory path."""
        with pytest.raises(DocSpecParseError, match="not a file"):
            parse_doc_spec_file(temp_dir)

    def test_raises_for_missing_frontmatter(self, temp_dir: Path) -> None:
        """Test parsing fails for missing frontmatter."""
        doc_spec_file = temp_dir / "no_frontmatter.md"
        doc_spec_file.write_text("# Just a document\nNo frontmatter here.")

        with pytest.raises(DocSpecParseError, match="frontmatter"):
            parse_doc_spec_file(doc_spec_file)

    def test_raises_for_invalid_yaml(self, temp_dir: Path) -> None:
        """Test parsing fails for invalid YAML frontmatter."""
        doc_spec_file = temp_dir / "invalid_yaml.md"
        doc_spec_file.write_text("---\ninvalid: [yaml: content\n---\n# Doc")

        with pytest.raises(DocSpecParseError, match="Failed to parse"):
            parse_doc_spec_file(doc_spec_file)

    def test_raises_for_empty_frontmatter(self, temp_dir: Path) -> None:
        """Test parsing fails for empty frontmatter."""
        doc_spec_file = temp_dir / "empty_frontmatter.md"
        doc_spec_file.write_text("---\n---\n# Doc")

        with pytest.raises(DocSpecParseError, match="empty"):
            parse_doc_spec_file(doc_spec_file)

    def test_raises_for_missing_required_fields(self, temp_dir: Path) -> None:
        """Test parsing fails for missing required fields."""
        doc_spec_file = temp_dir / "missing_fields.md"
        doc_spec_file.write_text(
            """---
name: "Test"
---
# Doc"""
        )

        with pytest.raises(DocSpecParseError, match="validation failed"):
            parse_doc_spec_file(doc_spec_file)


class TestLoadDocSpecsFromDirectory:
    """Tests for load_doc_specs_from_directory function."""

    def test_loads_all_doc_specs(self, fixtures_dir: Path) -> None:
        """Test loading all doc specs from directory."""
        doc_specs_dir = fixtures_dir / "doc_specs"
        doc_specs = load_doc_specs_from_directory(doc_specs_dir)

        assert "valid_report" in doc_specs
        assert "minimal_doc_spec" in doc_specs
        assert doc_specs["valid_report"].name == "Monthly Report"
        assert doc_specs["minimal_doc_spec"].name == "Minimal Doc Spec"

    def test_returns_empty_for_missing_directory(self, temp_dir: Path) -> None:
        """Test returns empty dict for missing directory."""
        nonexistent = temp_dir / "nonexistent"
        doc_specs = load_doc_specs_from_directory(nonexistent)

        assert doc_specs == {}

    def test_raises_for_file_path(self, temp_dir: Path) -> None:
        """Test raises for file path instead of directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(DocSpecParseError, match="not a directory"):
            load_doc_specs_from_directory(file_path)

    def test_returns_empty_for_empty_directory(self, temp_dir: Path) -> None:
        """Test returns empty dict for empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        doc_specs = load_doc_specs_from_directory(empty_dir)

        assert doc_specs == {}

    def test_ignores_non_md_files(self, temp_dir: Path) -> None:
        """Test ignores non-markdown files."""
        doc_specs_dir = temp_dir / "doc_specs"
        doc_specs_dir.mkdir()

        # Create a valid doc spec
        (doc_specs_dir / "valid.md").write_text(
            """---
name: "Valid"
description: "Valid doc spec"
quality_criteria:
  - name: Test
    description: Test
---
# Doc"""
        )

        # Create non-markdown file
        (doc_specs_dir / "readme.txt").write_text("Not a doc spec")

        doc_specs = load_doc_specs_from_directory(doc_specs_dir)

        assert len(doc_specs) == 1
        assert "valid" in doc_specs
