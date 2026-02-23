"""Tests for YAML utilities."""

from pathlib import Path

import pytest

from deepwork.utils.yaml_utils import YAMLError, load_yaml, save_yaml, validate_yaml_structure


class TestLoadYAML:
    """Tests for load_yaml function."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.7.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loads_valid_yaml(self, temp_dir: Path) -> None:
        """Test that load_yaml loads valid YAML."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("""
name: test_job
version: "1.0.0"
description: "A test job"
""")

        result = load_yaml(yaml_file)

        assert result is not None
        assert result["name"] == "test_job"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test job"

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.7.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loads_nested_yaml(self, temp_dir: Path) -> None:
        """Test that load_yaml loads nested YAML structures."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("""
job:
  name: test_job
  steps:
    - id: step1
      name: "Step 1"
    - id: step2
      name: "Step 2"
""")

        result = load_yaml(yaml_file)

        assert result is not None
        assert "job" in result
        assert result["job"]["name"] == "test_job"
        assert len(result["job"]["steps"]) == 2

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_none_for_missing_file(self, temp_dir: Path) -> None:
        """Test that load_yaml returns None for missing file."""
        yaml_file = temp_dir / "nonexistent.yml"

        result = load_yaml(yaml_file)

        assert result is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.7.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_empty_dict_for_empty_file(self, temp_dir: Path) -> None:
        """Test that load_yaml returns empty dict for empty file."""
        yaml_file = temp_dir / "empty.yml"
        yaml_file.write_text("")

        result = load_yaml(yaml_file)

        assert result == {}

    def test_raises_for_invalid_yaml(self, temp_dir: Path) -> None:
        """Test that load_yaml raises YAMLError for invalid YAML."""
        yaml_file = temp_dir / "invalid.yml"
        yaml_file.write_text("""
invalid:
  - item1
  - item2
    - nested:  # Invalid indentation
""")

        with pytest.raises(YAMLError, match="Failed to parse YAML file"):
            load_yaml(yaml_file)

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_non_dict_yaml(self, temp_dir: Path) -> None:
        """Test that load_yaml raises YAMLError for non-dictionary YAML."""
        yaml_file = temp_dir / "list.yml"
        yaml_file.write_text("""
- item1
- item2
- item3
""")

        with pytest.raises(YAMLError, match="must contain a dictionary"):
            load_yaml(yaml_file)

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that load_yaml accepts string paths."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("name: test")

        result = load_yaml(str(yaml_file))

        assert result is not None
        assert result["name"] == "test"


class TestSaveYAML:
    """Tests for save_yaml function."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.8.1, DW-REQ-010.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_saves_simple_dict(self, temp_dir: Path) -> None:
        """Test that save_yaml saves simple dictionary."""
        yaml_file = temp_dir / "test.yml"
        data = {
            "name": "test_job",
            "version": "1.0.0",
            "description": "A test job",
        }

        save_yaml(yaml_file, data)

        assert yaml_file.exists()
        content = yaml_file.read_text()
        assert "name: test_job" in content
        # PyYAML may or may not quote version strings
        assert "version: " in content and "1.0.0" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_saves_nested_dict(self, temp_dir: Path) -> None:
        """Test that save_yaml saves nested dictionaries."""
        yaml_file = temp_dir / "test.yml"
        data = {
            "job": {
                "name": "test_job",
                "steps": [
                    {"id": "step1", "name": "Step 1"},
                    {"id": "step2", "name": "Step 2"},
                ],
            }
        }

        save_yaml(yaml_file, data)

        assert yaml_file.exists()
        # Load it back to verify structure
        loaded = load_yaml(yaml_file)
        assert loaded == data

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_parent_directories(self, temp_dir: Path) -> None:
        """Test that save_yaml creates parent directories."""
        yaml_file = temp_dir / "nested" / "path" / "test.yml"
        data = {"name": "test"}

        save_yaml(yaml_file, data)

        assert yaml_file.exists()
        assert yaml_file.parent.exists()

    def test_overwrites_existing_file(self, temp_dir: Path) -> None:
        """Test that save_yaml overwrites existing files."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("old: data")

        new_data = {"new": "data"}
        save_yaml(yaml_file, new_data)

        loaded = load_yaml(yaml_file)
        assert loaded == new_data
        assert "old" not in (loaded or {})

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.8.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_preserves_order(self, temp_dir: Path) -> None:
        """Test that save_yaml preserves dictionary order."""
        yaml_file = temp_dir / "test.yml"
        data = {
            "first": 1,
            "second": 2,
            "third": 3,
        }

        save_yaml(yaml_file, data)

        content = yaml_file.read_text()
        # Check that keys appear in order
        first_pos = content.find("first:")
        second_pos = content.find("second:")
        third_pos = content.find("third:")
        assert first_pos < second_pos < third_pos

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that save_yaml accepts string paths."""
        yaml_file = temp_dir / "test.yml"
        data = {"name": "test"}

        save_yaml(str(yaml_file), data)

        assert yaml_file.exists()


class TestValidateYAMLStructure:
    """Tests for validate_yaml_structure function."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.9.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_required_keys_present(self) -> None:
        """Test that validate_yaml_structure passes when keys present."""
        data = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "extra": "field",
        }

        # Should not raise
        validate_yaml_structure(data, ["name", "version", "description"])

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.9.1, DW-REQ-010.9.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_missing_keys(self) -> None:
        """Test that validate_yaml_structure raises for missing keys."""
        data = {
            "name": "test",
            "version": "1.0.0",
        }

        with pytest.raises(YAMLError, match="Missing required keys: description"):
            validate_yaml_structure(data, ["name", "version", "description"])

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-010.9.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_multiple_missing_keys(self) -> None:
        """Test that validate_yaml_structure reports multiple missing keys."""
        data = {"name": "test"}

        with pytest.raises(
            YAMLError, match="Missing required keys: version, description"
        ) as exc_info:
            validate_yaml_structure(data, ["name", "version", "description"])

        # Check that both missing keys are mentioned
        assert "version" in str(exc_info.value)
        assert "description" in str(exc_info.value)

    def test_raises_for_non_dict_data(self) -> None:
        """Test that validate_yaml_structure raises for non-dictionary data."""
        data = ["item1", "item2"]  # type: ignore

        with pytest.raises(YAMLError, match="Data must be a dictionary"):
            validate_yaml_structure(data, ["name"])  # type: ignore

    def test_accepts_empty_required_keys(self) -> None:
        """Test that validate_yaml_structure works with no required keys."""
        data = {"any": "data"}

        # Should not raise
        validate_yaml_structure(data, [])


class TestYAMLRoundTrip:
    """Integration tests for save and load operations."""

    def test_roundtrip_preserves_data(self, temp_dir: Path) -> None:
        """Test that save and load preserve data correctly."""
        yaml_file = temp_dir / "roundtrip.yml"
        original_data = {
            "name": "test_job",
            "version": "1.0.0",
            "description": "A test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "inputs": ["input1", "input2"],
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "outputs": ["output1"],
                },
            ],
        }

        save_yaml(yaml_file, original_data)
        loaded_data = load_yaml(yaml_file)

        assert loaded_data == original_data

    def test_roundtrip_with_unicode(self, temp_dir: Path) -> None:
        """Test that save and load handle unicode correctly."""
        yaml_file = temp_dir / "unicode.yml"
        original_data = {
            "name": "测试",
            "description": "Test with emoji 🚀",
            "special": "Ñoño",
        }

        save_yaml(yaml_file, original_data)
        loaded_data = load_yaml(yaml_file)

        assert loaded_data == original_data
