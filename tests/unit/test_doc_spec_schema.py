"""Tests for doc spec schema validation."""

import pytest

from deepwork.schemas.doc_spec_schema import DOC_SPEC_FRONTMATTER_SCHEMA, QUALITY_CRITERION_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestQualityCriterionSchema:
    """Tests for quality criterion schema."""

    def test_valid_criterion(self) -> None:
        """Test valid quality criterion."""
        data = {"name": "Completeness", "description": "Must be complete"}
        # Should not raise
        validate_against_schema(data, QUALITY_CRITERION_SCHEMA)

    def test_missing_name(self) -> None:
        """Test criterion missing name."""
        data = {"description": "Must be complete"}
        with pytest.raises(ValidationError, match="name"):
            validate_against_schema(data, QUALITY_CRITERION_SCHEMA)

    def test_missing_description(self) -> None:
        """Test criterion missing description."""
        data = {"name": "Completeness"}
        with pytest.raises(ValidationError, match="description"):
            validate_against_schema(data, QUALITY_CRITERION_SCHEMA)

    def test_empty_name(self) -> None:
        """Test criterion with empty name."""
        data = {"name": "", "description": "Must be complete"}
        with pytest.raises(ValidationError):
            validate_against_schema(data, QUALITY_CRITERION_SCHEMA)

    def test_empty_description(self) -> None:
        """Test criterion with empty description."""
        data = {"name": "Completeness", "description": ""}
        with pytest.raises(ValidationError):
            validate_against_schema(data, QUALITY_CRITERION_SCHEMA)


class TestDocSpecFrontmatterSchema:
    """Tests for doc spec frontmatter schema."""

    def test_valid_minimal_doc_spec(self) -> None:
        """Test valid minimal doc spec frontmatter."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        # Should not raise
        validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_valid_full_doc_spec(self) -> None:
        """Test valid doc spec with all optional fields."""
        data = {
            "name": "Full Doc Spec",
            "description": "A complete document type",
            "path_patterns": ["reports/*.md", "docs/*.md"],
            "target_audience": "Engineering team",
            "frequency": "Weekly",
            "quality_criteria": [
                {"name": "Summary", "description": "Include summary"},
                {"name": "Data", "description": "Include data"},
            ],
        }
        # Should not raise
        validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_missing_name(self) -> None:
        """Test doc spec missing name."""
        data = {
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError, match="name"):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_missing_description(self) -> None:
        """Test doc spec missing description."""
        data = {
            "name": "Test Doc Spec",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError, match="description"):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_missing_quality_criteria(self) -> None:
        """Test doc spec missing quality criteria."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document type",
        }
        with pytest.raises(ValidationError, match="quality_criteria"):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_empty_quality_criteria(self) -> None:
        """Test doc spec with empty quality criteria array."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document type",
            "quality_criteria": [],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_invalid_path_patterns(self) -> None:
        """Test doc spec with invalid path patterns type."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document type",
            "path_patterns": "reports/*.md",  # Should be array
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)

    def test_additional_properties_not_allowed(self) -> None:
        """Test doc spec with additional properties."""
        data = {
            "name": "Test Doc Spec",
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
            "extra_field": "not allowed",
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DOC_SPEC_FRONTMATTER_SCHEMA)
