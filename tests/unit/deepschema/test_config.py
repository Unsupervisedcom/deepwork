"""Tests for DeepSchema configuration parsing.

Validates requirements: DW-REQ-011, DW-REQ-011.1, DW-REQ-011.2.
"""

from pathlib import Path

import pytest

from deepwork.deepschema.config import DeepSchemaError, parse_deepschema_file


def _write_schema(path: Path, filename: str, content: str) -> Path:
    filepath = path / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


class TestParseDeepschemaFile:
    def test_parses_named_schema(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.1.2, DW-REQ-011.2.1).
        filepath = _write_schema(
            tmp_path,
            "deepschema.yml",
            """
summary: "Job definitions"
instructions: "Keep them concise"
requirements:
  must-have-name: "MUST include a name field"
  should-be-short: "SHOULD keep summaries under 200 chars"
matchers:
  - "**/*.yml"
""",
        )
        schema = parse_deepschema_file(filepath, "named", "job_def")
        assert schema.name == "job_def"
        assert schema.schema_type == "named"
        assert schema.summary == "Job definitions"
        assert schema.instructions == "Keep them concise"
        assert len(schema.requirements) == 2
        assert schema.requirements["must-have-name"] == "MUST include a name field"
        assert schema.matchers == ["**/*.yml"]

    def test_parses_anonymous_schema(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.1.3, DW-REQ-011.2.1).
        filepath = _write_schema(
            tmp_path,
            ".deepschema.config.json.yml",
            """
requirements:
  valid-json: "MUST be valid JSON"
json_schema_path: "config.schema.json"
""",
        )
        schema = parse_deepschema_file(filepath, "anonymous", "config.json")
        assert schema.name == "config.json"
        assert schema.schema_type == "anonymous"
        assert schema.json_schema_path == "config.schema.json"
        assert schema.requirements["valid-json"] == "MUST be valid JSON"

    def test_parses_empty_file(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.2).
        filepath = _write_schema(tmp_path, "deepschema.yml", "")
        schema = parse_deepschema_file(filepath, "named", "empty")
        assert schema.name == "empty"
        assert schema.requirements == {}
        assert schema.matchers == []

    def test_parses_verification_commands(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.7).
        filepath = _write_schema(
            tmp_path,
            "deepschema.yml",
            """
verification_bash_command:
  - "yamllint $1"
  - "python -m json.tool $1"
""",
        )
        schema = parse_deepschema_file(filepath, "named", "test")
        assert schema.verification_bash_command == ["yamllint $1", "python -m json.tool $1"]

    def test_parses_parent_schemas(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.8).
        filepath = _write_schema(
            tmp_path,
            "deepschema.yml",
            """
parent_deep_schemas:
  - base_config
  - yaml_file
requirements:
  child-req: "MUST have child requirement"
""",
        )
        schema = parse_deepschema_file(filepath, "named", "child")
        assert schema.parent_deep_schemas == ["base_config", "yaml_file"]

    def test_parses_examples_and_references(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.1).
        filepath = _write_schema(
            tmp_path,
            "deepschema.yml",
            """
examples:
  - path: "examples/good.yml"
    description: "A well-formed config"
references:
  - path: "https://example.com/docs"
    description: "Official documentation"
""",
        )
        schema = parse_deepschema_file(filepath, "named", "test")
        assert len(schema.examples) == 1
        assert schema.examples[0]["path"] == "examples/good.yml"
        assert len(schema.references) == 1
        assert schema.references[0]["path"] == "https://example.com/docs"

    def test_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.3).
        filepath = _write_schema(tmp_path, "deepschema.yml", "[not a dict]")
        with pytest.raises(DeepSchemaError):
            parse_deepschema_file(filepath, "named", "test")

    def test_rejects_unknown_keys(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.3).
        filepath = _write_schema(
            tmp_path,
            "deepschema.yml",
            """
unknown_key: "value"
""",
        )
        with pytest.raises(DeepSchemaError, match="Schema validation failed"):
            parse_deepschema_file(filepath, "named", "test")

    def test_missing_file(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.3).
        with pytest.raises(DeepSchemaError, match="File not found"):
            parse_deepschema_file(tmp_path / "nonexistent.yml", "named", "test")
