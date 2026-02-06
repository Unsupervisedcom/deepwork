"""Tests for expert schema validation."""

import pytest

from deepwork.schemas.expert_schema import (
    EXPERT_SCHEMA,
    LEARNING_FRONTMATTER_SCHEMA,
    TOPIC_FRONTMATTER_SCHEMA,
)
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestExpertSchema:
    """Tests for expert.yml schema validation."""

    def test_valid_minimal_expert(self) -> None:
        """Test valid minimal expert definition."""
        data = {
            "discovery_description": "Test expert for unit testing",
            "full_expertise": "You are an expert on testing.",
        }
        # Should not raise
        validate_against_schema(data, EXPERT_SCHEMA)

    def test_valid_multiline_expert(self) -> None:
        """Test valid expert with multiline content."""
        data = {
            "discovery_description": "Test expert for unit testing\nwith multiple lines",
            "full_expertise": "# Test Expert\n\nYou are an expert on testing.\n\n## Topics\n\n- Testing basics\n- Advanced testing",
        }
        # Should not raise
        validate_against_schema(data, EXPERT_SCHEMA)

    def test_missing_discovery_description(self) -> None:
        """Test that missing discovery_description fails validation."""
        data = {
            "full_expertise": "You are an expert on testing.",
        }
        with pytest.raises(ValidationError, match="discovery_description"):
            validate_against_schema(data, EXPERT_SCHEMA)

    def test_missing_full_expertise(self) -> None:
        """Test that missing full_expertise fails validation."""
        data = {
            "discovery_description": "Test expert",
        }
        with pytest.raises(ValidationError, match="full_expertise"):
            validate_against_schema(data, EXPERT_SCHEMA)

    def test_empty_discovery_description(self) -> None:
        """Test that empty discovery_description fails validation."""
        data = {
            "discovery_description": "",
            "full_expertise": "You are an expert on testing.",
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, EXPERT_SCHEMA)

    def test_empty_full_expertise(self) -> None:
        """Test that empty full_expertise fails validation."""
        data = {
            "discovery_description": "Test expert",
            "full_expertise": "",
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, EXPERT_SCHEMA)

    def test_additional_properties_not_allowed(self) -> None:
        """Test that additional properties are not allowed."""
        data = {
            "discovery_description": "Test expert",
            "full_expertise": "You are an expert on testing.",
            "extra_field": "not allowed",
        }
        with pytest.raises(ValidationError, match="extra_field"):
            validate_against_schema(data, EXPERT_SCHEMA)


class TestTopicFrontmatterSchema:
    """Tests for topic frontmatter schema validation."""

    def test_valid_minimal_topic(self) -> None:
        """Test valid minimal topic with just name."""
        data = {"name": "Test Topic"}
        # Should not raise
        validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_valid_full_topic(self) -> None:
        """Test valid topic with all fields."""
        data = {
            "name": "Test Topic",
            "keywords": ["testing", "unit test", "pytest"],
            "last_updated": "2025-01-30",
        }
        # Should not raise
        validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_missing_name(self) -> None:
        """Test that missing name fails validation."""
        data = {
            "keywords": ["testing"],
        }
        with pytest.raises(ValidationError, match="name"):
            validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_empty_name(self) -> None:
        """Test that empty name fails validation."""
        data = {"name": ""}
        with pytest.raises(ValidationError):
            validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_invalid_date_format(self) -> None:
        """Test that invalid date format fails validation."""
        data = {
            "name": "Test Topic",
            "last_updated": "January 30, 2025",
        }
        with pytest.raises(ValidationError, match="last_updated"):
            validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_valid_date_format(self) -> None:
        """Test that valid YYYY-MM-DD date format passes."""
        data = {
            "name": "Test Topic",
            "last_updated": "2025-01-30",
        }
        # Should not raise
        validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_empty_keywords_list(self) -> None:
        """Test that empty keywords list is allowed."""
        data = {
            "name": "Test Topic",
            "keywords": [],
        }
        # Should not raise
        validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)

    def test_additional_properties_not_allowed(self) -> None:
        """Test that additional properties are not allowed."""
        data = {
            "name": "Test Topic",
            "extra": "not allowed",
        }
        with pytest.raises(ValidationError, match="extra"):
            validate_against_schema(data, TOPIC_FRONTMATTER_SCHEMA)


class TestLearningFrontmatterSchema:
    """Tests for learning frontmatter schema validation."""

    def test_valid_minimal_learning(self) -> None:
        """Test valid minimal learning with just name."""
        data = {"name": "Test Learning"}
        # Should not raise
        validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_valid_full_learning(self) -> None:
        """Test valid learning with all fields."""
        data = {
            "name": "Test Learning",
            "last_updated": "2025-01-30",
            "summarized_result": "Discovered that X causes Y under Z conditions.",
        }
        # Should not raise
        validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_missing_name(self) -> None:
        """Test that missing name fails validation."""
        data = {
            "summarized_result": "Some finding",
        }
        with pytest.raises(ValidationError, match="name"):
            validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_empty_name(self) -> None:
        """Test that empty name fails validation."""
        data = {"name": ""}
        with pytest.raises(ValidationError):
            validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_empty_summarized_result(self) -> None:
        """Test that empty summarized_result fails validation."""
        data = {
            "name": "Test Learning",
            "summarized_result": "",
        }
        with pytest.raises(ValidationError):
            validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_invalid_date_format(self) -> None:
        """Test that invalid date format fails validation."""
        data = {
            "name": "Test Learning",
            "last_updated": "30-01-2025",
        }
        with pytest.raises(ValidationError, match="last_updated"):
            validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_multiline_summarized_result(self) -> None:
        """Test that multiline summarized_result is allowed."""
        data = {
            "name": "Test Learning",
            "summarized_result": "First line\nSecond line\nThird line",
        }
        # Should not raise
        validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)

    def test_additional_properties_not_allowed(self) -> None:
        """Test that additional properties are not allowed."""
        data = {
            "name": "Test Learning",
            "extra": "not allowed",
        }
        with pytest.raises(ValidationError, match="extra"):
            validate_against_schema(data, LEARNING_FRONTMATTER_SCHEMA)
