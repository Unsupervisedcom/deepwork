"""Tests for DeepSchema file matching."""

from pathlib import Path

from deepwork.deepschema.config import DeepSchema
from deepwork.deepschema.matcher import get_applicable_schemas, get_schemas_for_file_fast


def _named_schema(
    name: str,
    matchers: list[str],
    source_path: Path | None = None,
) -> DeepSchema:
    return DeepSchema(
        name=name,
        schema_type="named",
        source_path=source_path or Path(f"/fake/.deepwork/schemas/{name}/deepschema.yml"),
        matchers=matchers,
        requirements={"test": "MUST pass"},
    )


def _anonymous_schema(
    target_filename: str,
    directory: Path,
) -> DeepSchema:
    return DeepSchema(
        name=target_filename,
        schema_type="anonymous",
        source_path=directory / f".deepschema.{target_filename}.yml",
        requirements={"test": "MUST pass"},
    )


class TestGetApplicableSchemas:
    def test_matches_named_schema_by_glob(self, tmp_path: Path) -> None:
        schema = _named_schema("py_files", ["**/*.py"])
        result = get_applicable_schemas("src/app.py", [schema], tmp_path)
        assert len(result) == 1
        assert result[0].name == "py_files"

    def test_no_match_for_wrong_extension(self, tmp_path: Path) -> None:
        schema = _named_schema("py_files", ["**/*.py"])
        result = get_applicable_schemas("src/app.js", [schema], tmp_path)
        assert len(result) == 0

    def test_matches_anonymous_schema(self, tmp_path: Path) -> None:
        schema = _anonymous_schema("config.json", tmp_path / "src")
        result = get_applicable_schemas("src/config.json", [schema], tmp_path)
        assert len(result) == 1

    def test_anonymous_no_match_different_dir(self, tmp_path: Path) -> None:
        schema = _anonymous_schema("config.json", tmp_path / "src")
        result = get_applicable_schemas("other/config.json", [schema], tmp_path)
        assert len(result) == 0

    def test_multiple_schemas_match(self, tmp_path: Path) -> None:
        named = _named_schema("all_yml", ["**/*.yml"])
        anon = _anonymous_schema("config.yml", tmp_path / "src")
        result = get_applicable_schemas("src/config.yml", [named, anon], tmp_path)
        assert len(result) == 2

    def test_named_schema_specific_dir_pattern(self, tmp_path: Path) -> None:
        schema = _named_schema("src_only", ["src/**/*.py"])
        assert get_applicable_schemas("src/main.py", [schema], tmp_path)
        assert not get_applicable_schemas("tests/main.py", [schema], tmp_path)


class TestAnonymousSchemaOutsideProject:
    """Tests for _anonymous_schema_matches when target is outside project_root (lines 122-123)."""

    def test_returns_false_when_target_outside_project(self, tmp_path: Path) -> None:
        """Anonymous schema whose target resolves outside project_root returns False."""
        from deepwork.deepschema.matcher import _anonymous_schema_matches

        # Schema in /outside/ directory, target would be /outside/config.json
        schema = DeepSchema(
            name="config.json",
            schema_type="anonymous",
            source_path=Path("/outside/.deepschema.config.json.yml"),
            requirements={"test": "MUST pass"},
        )
        # filepath is relative to tmp_path, but target resolves to /outside/config.json
        result = _anonymous_schema_matches("config.json", schema, tmp_path)
        assert result is False


class TestGetSchemasForFileFast:
    def test_finds_named_schema(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "py_files"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "matchers:\n  - '**/*.py'\nrequirements:\n  r1: 'MUST exist'\n",
            encoding="utf-8",
        )
        result = get_schemas_for_file_fast("src/app.py", tmp_path)
        assert len(result) == 1
        assert result[0].name == "py_files"

    def test_finds_anonymous_schema(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / ".deepschema.app.py.yml").write_text(
            "requirements:\n  r1: 'MUST exist'\n",
            encoding="utf-8",
        )
        result = get_schemas_for_file_fast("src/app.py", tmp_path)
        assert len(result) == 1
        assert result[0].name == "app.py"

    def test_returns_empty_when_no_schemas(self, tmp_path: Path) -> None:
        result = get_schemas_for_file_fast("src/app.py", tmp_path)
        assert result == []

    def test_skips_named_schema_with_parse_error(self, tmp_path: Path) -> None:
        """Named schema with parse error is skipped, not crash (lines 74-75)."""
        schema_dir = tmp_path / ".deepwork" / "schemas" / "broken"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text("[invalid yaml]", encoding="utf-8")

        # Should not raise — the broken schema is silently skipped
        result = get_schemas_for_file_fast("src/app.py", tmp_path)
        # No broken schemas in result
        assert all(s.name != "broken" for s in result)

    def test_skips_anonymous_schema_with_parse_error(self, tmp_path: Path) -> None:
        """Anonymous schema with parse error is skipped, not crash (lines 88-89)."""
        src = tmp_path / "src"
        src.mkdir()
        (src / ".deepschema.app.py.yml").write_text("[invalid yaml]", encoding="utf-8")

        # Should not raise — the broken anonymous schema is silently skipped
        result = get_schemas_for_file_fast("src/app.py", tmp_path)
        assert result == []
