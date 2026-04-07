"""Tests for get_named_schemas MCP tool.

Validates requirements: DW-REQ-011.9.
"""

from pathlib import Path

import pytest

from deepwork.deepschema.config import DeepSchemaError, parse_deepschema_file
from deepwork.deepschema.discovery import find_named_schemas


@pytest.mark.usefixtures("without_standard_schemas")
class TestGetNamedSchemas:
    """Tests for the get_named_schemas tool logic."""

    def test_returns_empty_when_no_schemas(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.9.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        results = find_named_schemas(tmp_path)
        assert results == []

    def test_returns_named_schema_info(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.9.1, DW-REQ-011.9.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema_dir = tmp_path / ".deepwork" / "schemas" / "my_config"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "summary: 'Config files'\nmatchers:\n  - '**/*.cfg'\nrequirements:\n  r1: 'MUST exist'\n",
            encoding="utf-8",
        )

        manifests = find_named_schemas(tmp_path)
        assert len(manifests) == 1

        schema = parse_deepschema_file(manifests[0], "named", manifests[0].parent.name)
        assert schema.name == "my_config"
        assert schema.summary == "Config files"
        assert schema.matchers == ["**/*.cfg"]

    def test_multiple_schemas_returned(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.9.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        for name in ["alpha", "beta"]:
            d = tmp_path / ".deepwork" / "schemas" / name
            d.mkdir(parents=True)
            (d / "deepschema.yml").write_text(
                f"summary: '{name} schema'\nmatchers:\n  - '**/*.{name}'\n",
                encoding="utf-8",
            )

        manifests = find_named_schemas(tmp_path)
        assert len(manifests) == 2
        names = {m.parent.name for m in manifests}
        assert names == {"alpha", "beta"}

    def test_malformed_schema_raises_error(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.9.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema_dir = tmp_path / ".deepwork" / "schemas" / "bad"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "requirements: 'not a dict'\n",
            encoding="utf-8",
        )

        manifests = find_named_schemas(tmp_path)
        assert len(manifests) == 1

        with pytest.raises(DeepSchemaError):
            parse_deepschema_file(manifests[0], "named", "bad")

    def test_schema_without_summary_returns_none(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.2.2, DW-REQ-011.9.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema_dir = tmp_path / ".deepwork" / "schemas" / "minimal"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "matchers:\n  - '**/*.txt'\n",
            encoding="utf-8",
        )

        manifests = find_named_schemas(tmp_path)
        schema = parse_deepschema_file(manifests[0], "named", "minimal")
        assert schema.summary is None
        assert schema.matchers == ["**/*.txt"]
