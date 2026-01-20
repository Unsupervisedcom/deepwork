"""Tests for DTD schema validation."""

import pytest

from deepwork.schemas.dtd_schema import DTD_FRONTMATTER_SCHEMA, QUALITY_CRITERION_SCHEMA
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


class TestDTDFrontmatterSchema:
    """Tests for DTD frontmatter schema."""

    def test_valid_minimal_dtd(self) -> None:
        """Test valid minimal DTD frontmatter."""
        data = {
            "name": "Test DTD",
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        # Should not raise
        validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_valid_full_dtd(self) -> None:
        """Test valid DTD with all optional fields."""
        data = {
            "name": "Full DTD",
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
        validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_missing_name(self) -> None:
        """Test DTD missing name."""
        data = {
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError, match="name"):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_missing_description(self) -> None:
        """Test DTD missing description."""
        data = {
            "name": "Test DTD",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError, match="description"):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_missing_quality_criteria(self) -> None:
        """Test DTD missing quality criteria."""
        data = {
            "name": "Test DTD",
            "description": "A test document type",
        }
        with pytest.raises(ValidationError, match="quality_criteria"):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_empty_quality_criteria(self) -> None:
        """Test DTD with empty quality criteria array."""
        data = {
            "name": "Test DTD",
            "description": "A test document type",
            "quality_criteria": [],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_invalid_path_patterns(self) -> None:
        """Test DTD with invalid path patterns type."""
        data = {
            "name": "Test DTD",
            "description": "A test document type",
            "path_patterns": "reports/*.md",  # Should be array
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)

    def test_additional_properties_not_allowed(self) -> None:
        """Test DTD with additional properties."""
        data = {
            "name": "Test DTD",
            "description": "A test document type",
            "quality_criteria": [{"name": "Test", "description": "Test criterion"}],
            "extra_field": "not allowed",
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, DTD_FRONTMATTER_SCHEMA)
