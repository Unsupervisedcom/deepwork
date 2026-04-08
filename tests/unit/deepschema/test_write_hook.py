"""Tests for the DeepSchema write hook.

Validates requirements: DW-REQ-011.7.
"""

import json
from pathlib import Path

from deepwork.hooks.deepschema_write import deepschema_write_hook
from deepwork.hooks.wrapper import HookInput, NormalizedEvent, Platform


def _make_hook_input(
    file_path: str,
    cwd: str,
    tool_name: str = "write_file",
) -> HookInput:
    return HookInput(
        platform=Platform.CLAUDE,
        event=NormalizedEvent.AFTER_TOOL,
        tool_name=tool_name,
        tool_input={"file_path": file_path},
        cwd=cwd,
    )


def _write_name_required_schema(tmp_path: Path, slug: str, matcher: str) -> None:
    """Create a named DeepSchema under `.deepwork/schemas/<slug>/` whose
    `json_schema_path` requires a top-level `name` string. Used by the
    _validate_json_schema exercise tests below, which all share the same
    schema shape and differ only in the matcher glob.
    """
    schema_dir = tmp_path / ".deepwork" / "schemas" / slug
    schema_dir.mkdir(parents=True)
    (schema_dir / "test.schema.json").write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )
    (schema_dir / "deepschema.yml").write_text(
        f"matchers:\n  - '{matcher}'\n"
        "json_schema_path: 'test.schema.json'\n"
        "requirements:\n  r1: 'MUST conform'\n",
        encoding="utf-8",
    )


class TestDeepschemaWriteHook:
    def test_no_schemas_returns_empty(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        hook_input = _make_hook_input(str(tmp_path / "test.py"), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert result.context == ""
        assert result.decision == ""

    def test_injects_conformance_note(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # Create a named schema matching .py files
        schema_dir = tmp_path / ".deepwork" / "schemas" / "py_schema"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "matchers:\n  - '**/*.py'\nrequirements:\n  r1: 'MUST exist'\n",
            encoding="utf-8",
        )
        # Create the target file
        target = tmp_path / "src" / "app.py"
        target.parent.mkdir(parents=True)
        target.write_text("print('hello')", encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "must conform to the DeepSchema" in result.context

    def test_anonymous_schema_conformance_note(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # Create anonymous schema
        (tmp_path / ".deepschema.config.json.yml").write_text(
            "requirements:\n  r1: 'MUST be valid'\n",
            encoding="utf-8",
        )
        target = tmp_path / "config.json"
        target.write_text('{"key": "value"}', encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "must conform to the DeepSchema" in result.context

    def test_json_schema_validation_failure(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.3, DW-REQ-011.7.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        _write_name_required_schema(tmp_path, slug="json_test", matcher="**/*.json")
        target = tmp_path / "data.json"
        target.write_text('{"other": "field"}', encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "CRITICAL" in result.context
        assert "validation failed" in result.context.lower()

    def test_json_schema_validation_success(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        _write_name_required_schema(tmp_path, slug="json_test", matcher="**/*.json")
        target = tmp_path / "data.json"
        target.write_text('{"name": "valid"}', encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "must conform to the DeepSchema" in result.context
        assert "CRITICAL" not in result.context

    def test_json_schema_validation_of_yaml_file(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # YAML files validated against a JSON Schema should be parsed as YAML, not JSON.
        _write_name_required_schema(tmp_path, slug="yml_test", matcher="**/*.yml")
        target = tmp_path / "data.yml"
        target.write_text("name: valid\nother: field\n", encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "must conform to the DeepSchema" in result.context
        assert "CRITICAL" not in result.context

    def test_json_schema_validation_of_yaml_file_with_no_extension(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # Files like `.deepreview` whose `Path.suffix` is empty (the leading
        # dot is treated as a hidden-file marker, not an extension separator)
        # MUST still be parsed as YAML — not as JSON. Regression for the bug
        # where `.deepreview` files reported `File is not valid JSON:
        # Expecting value: line 1 column 1 (char 0)`.
        _write_name_required_schema(tmp_path, slug="dotfile_test", matcher="**/.myappconfig")
        target = tmp_path / ".myappconfig"
        target.write_text("name: valid\n", encoding="utf-8")
        # Sanity check: this is the case the old extension-based dispatch
        # missed — Path.suffix is empty for any dot-prefixed filename, so
        # the old code routed `.myappconfig`, `.deepreview`, etc. to
        # json.loads() and produced false-positive parse errors.
        assert target.suffix == ""

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "must conform to the DeepSchema" in result.context
        assert "CRITICAL" not in result.context
        assert "File is not valid JSON" not in result.context

    def test_json_schema_validation_of_invalid_yaml_file(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.3, DW-REQ-011.7.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # YAML files that fail JSON Schema validation should report errors.
        _write_name_required_schema(tmp_path, slug="yml_test", matcher="**/*.yml")
        target = tmp_path / "data.yml"
        target.write_text("other: field\n", encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "CRITICAL" in result.context

    def test_verification_command_failure(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.4, DW-REQ-011.7.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema_dir = tmp_path / ".deepwork" / "schemas" / "bash_test"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "matchers:\n  - '**/*.txt'\nverification_bash_command:\n  - 'grep required_word \"$1\"'\nrequirements:\n  r1: 'MUST contain required_word'\n",
            encoding="utf-8",
        )
        target = tmp_path / "test.txt"
        target.write_text("no matching content here", encoding="utf-8")

        hook_input = _make_hook_input(str(target), str(tmp_path))
        result = deepschema_write_hook(hook_input)
        assert "CRITICAL" in result.context

    def test_ignores_non_write_events(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        hook_input = HookInput(
            platform=Platform.CLAUDE,
            event=NormalizedEvent.BEFORE_TOOL,
            tool_name="write_file",
            tool_input={"file_path": "/some/file"},
            cwd="/tmp",
        )
        result = deepschema_write_hook(hook_input)
        assert result.context == ""

    def test_ignores_non_write_tools(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        hook_input = HookInput(
            platform=Platform.CLAUDE,
            event=NormalizedEvent.AFTER_TOOL,
            tool_name="shell",
            tool_input={"command": "echo hi"},
            cwd="/tmp",
        )
        result = deepschema_write_hook(hook_input)
        assert result.context == ""
