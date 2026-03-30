"""Tests for DeepSchema discovery."""

from pathlib import Path
from unittest.mock import patch

from deepwork.deepschema.discovery import (
    ENV_ADDITIONAL_SCHEMAS_FOLDERS,
    anonymous_target_filename,
    discover_all_schemas,
    find_anonymous_schemas,
    find_named_schemas,
    get_named_schema_folders,
)


def _make_named_schema(project_root: Path, name: str, content: str = "") -> Path:
    schema_dir = project_root / ".deepwork" / "schemas" / name
    schema_dir.mkdir(parents=True, exist_ok=True)
    manifest = schema_dir / "deepschema.yml"
    manifest.write_text(content or f"summary: '{name} schema'\n", encoding="utf-8")
    return manifest


def _make_anonymous_schema(directory: Path, target_filename: str, content: str = "") -> Path:
    filepath = directory / f".deepschema.{target_filename}.yml"
    filepath.write_text(
        content or "requirements:\n  test-req: 'MUST exist'\n",
        encoding="utf-8",
    )
    return filepath


class TestFindNamedSchemas:
    def test_finds_schemas_in_deepwork_dir(self, tmp_path: Path) -> None:
        _make_named_schema(tmp_path, "job_def")
        _make_named_schema(tmp_path, "config")
        results = find_named_schemas(tmp_path)
        names = [p.parent.name for p in results]
        assert sorted(names) == ["config", "job_def"]

    def test_returns_empty_when_no_schemas_dir(self, tmp_path: Path) -> None:
        assert find_named_schemas(tmp_path) == []

    def test_skips_directories_without_manifest(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "incomplete"
        schema_dir.mkdir(parents=True)
        # No deepschema.yml inside
        assert find_named_schemas(tmp_path) == []


class TestFindAnonymousSchemas:
    def test_finds_anonymous_schemas(self, tmp_path: Path) -> None:
        _make_anonymous_schema(tmp_path, "config.json")
        subdir = tmp_path / "src"
        subdir.mkdir()
        _make_anonymous_schema(subdir, "app.py")
        results = find_anonymous_schemas(tmp_path)
        assert len(results) == 2

    def test_skips_git_directories(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        _make_anonymous_schema(git_dir, "config.json")
        assert find_anonymous_schemas(tmp_path) == []

    def test_returns_empty_when_none(self, tmp_path: Path) -> None:
        assert find_anonymous_schemas(tmp_path) == []


class TestAnonymousTargetFilename:
    def test_simple_filename(self) -> None:
        assert anonymous_target_filename(".deepschema.foo.py.yml") == "foo.py"

    def test_dotted_filename(self) -> None:
        assert anonymous_target_filename(".deepschema.config.json.yml") == "config.json"

    def test_long_extension(self) -> None:
        assert anonymous_target_filename(".deepschema.data.tar.gz.yml") == "data.tar.gz"


def _make_named_schema_in(folder: Path, name: str, content: str = "") -> Path:
    """Create a named schema in an arbitrary folder (not under .deepwork/schemas)."""
    schema_dir = folder / name
    schema_dir.mkdir(parents=True, exist_ok=True)
    manifest = schema_dir / "deepschema.yml"
    manifest.write_text(content or f"summary: '{name} schema'\n", encoding="utf-8")
    return manifest


class TestGetNamedSchemaFolders:
    def test_includes_project_local_and_standard(self, tmp_path: Path) -> None:
        folders = get_named_schema_folders(tmp_path)
        assert folders[0] == tmp_path / ".deepwork" / "schemas"
        # Second entry is the standard_schemas package dir
        assert folders[1].name == "standard_schemas"
        assert len(folders) == 2

    @patch.dict("os.environ", {ENV_ADDITIONAL_SCHEMAS_FOLDERS: "/extra/one:/extra/two"})
    def test_includes_env_var_folders(self, tmp_path: Path) -> None:
        folders = get_named_schema_folders(tmp_path)
        assert len(folders) == 4
        assert folders[2] == Path("/extra/one")
        assert folders[3] == Path("/extra/two")

    @patch.dict("os.environ", {ENV_ADDITIONAL_SCHEMAS_FOLDERS: ""})
    def test_empty_env_var_adds_nothing(self, tmp_path: Path) -> None:
        folders = get_named_schema_folders(tmp_path)
        assert len(folders) == 2


class TestFindNamedSchemasMultiSource:
    def test_finds_standard_schemas(self, tmp_path: Path) -> None:
        # Create a "standard" schema in a separate directory and patch it in
        standard_dir = tmp_path / "standard"
        _make_named_schema_in(standard_dir, "builtin_schema")

        with patch("deepwork.deepschema.discovery._STANDARD_SCHEMAS_DIR", standard_dir):
            results = find_named_schemas(tmp_path)
        names = [p.parent.name for p in results]
        assert "builtin_schema" in names

    def test_project_local_overrides_standard(self, tmp_path: Path) -> None:
        # Same name in both project-local and standard — project-local wins
        _make_named_schema(tmp_path, "shared_name", "summary: 'local'\n")

        standard_dir = tmp_path / "standard"
        _make_named_schema_in(standard_dir, "shared_name", "summary: 'standard'\n")

        with patch("deepwork.deepschema.discovery._STANDARD_SCHEMAS_DIR", standard_dir):
            results = find_named_schemas(tmp_path)
        # Only one result — the local one
        matching = [p for p in results if p.parent.name == "shared_name"]
        assert len(matching) == 1
        assert ".deepwork/schemas" in str(matching[0])

    @patch.dict("os.environ", clear=True)
    def test_env_var_schemas_discovered(self, tmp_path: Path) -> None:
        extra_dir = tmp_path / "extra_schemas"
        _make_named_schema_in(extra_dir, "env_schema")

        env_val = str(extra_dir)
        with (
            patch.dict("os.environ", {ENV_ADDITIONAL_SCHEMAS_FOLDERS: env_val}),
            patch("deepwork.deepschema.discovery._STANDARD_SCHEMAS_DIR", tmp_path / "empty"),
        ):
            results = find_named_schemas(tmp_path)
        names = [p.parent.name for p in results]
        assert "env_schema" in names

    @patch.dict("os.environ", clear=True)
    def test_project_local_overrides_env_var(self, tmp_path: Path) -> None:
        _make_named_schema(tmp_path, "overlap", "summary: 'local'\n")

        extra_dir = tmp_path / "extra"
        _make_named_schema_in(extra_dir, "overlap", "summary: 'extra'\n")

        env_val = str(extra_dir)
        with (
            patch.dict("os.environ", {ENV_ADDITIONAL_SCHEMAS_FOLDERS: env_val}),
            patch("deepwork.deepschema.discovery._STANDARD_SCHEMAS_DIR", tmp_path / "empty"),
        ):
            results = find_named_schemas(tmp_path)
        matching = [p for p in results if p.parent.name == "overlap"]
        assert len(matching) == 1
        assert ".deepwork/schemas" in str(matching[0])


class TestDiscoverAllSchemas:
    def test_discovers_both_types(self, tmp_path: Path) -> None:
        _make_named_schema(
            tmp_path,
            "yaml_config",
            "summary: 'YAML configs'\nmatchers:\n  - '**/*.yml'\n",
        )
        _make_anonymous_schema(tmp_path, "special.json")
        schemas, errors = discover_all_schemas(tmp_path)
        assert len(schemas) == 2
        assert len(errors) == 0
        types = {s.schema_type for s in schemas}
        assert types == {"named", "anonymous"}

    def test_collects_parse_errors(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "bad"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text("[invalid]", encoding="utf-8")
        schemas, errors = discover_all_schemas(tmp_path)
        assert len(schemas) == 0
        assert len(errors) == 1
