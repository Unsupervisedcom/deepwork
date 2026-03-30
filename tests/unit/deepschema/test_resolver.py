"""Tests for DeepSchema parent inheritance resolution."""

from pathlib import Path

import pytest

from deepwork.deepschema.config import DeepSchema, DeepSchemaError
from deepwork.deepschema.resolver import resolve_all, resolve_inheritance


def _schema(
    name: str,
    requirements: dict[str, str] | None = None,
    parents: list[str] | None = None,
    json_schema_path: str | None = None,
    verification_cmds: list[str] | None = None,
) -> DeepSchema:
    return DeepSchema(
        name=name,
        schema_type="named",
        source_path=Path(f"/fake/{name}/deepschema.yml"),
        requirements=requirements or {},
        parent_deep_schemas=parents or [],
        json_schema_path=json_schema_path,
        verification_bash_command=verification_cmds or [],
    )


class TestResolveInheritance:
    def test_no_parents_returns_unchanged(self) -> None:
        schema = _schema("child", requirements={"r1": "MUST exist"})
        named = {"child": schema}
        result = resolve_inheritance(schema, named)
        assert result.requirements == {"r1": "MUST exist"}

    def test_inherits_parent_requirements(self) -> None:
        parent = _schema("parent", requirements={"p1": "MUST be valid"})
        child = _schema("child", requirements={"c1": "SHOULD be nice"}, parents=["parent"])
        named = {"parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.requirements == {"p1": "MUST be valid", "c1": "SHOULD be nice"}

    def test_child_overrides_parent_requirements(self) -> None:
        parent = _schema("parent", requirements={"shared": "MUST do X"})
        child = _schema("child", requirements={"shared": "MUST do Y"}, parents=["parent"])
        named = {"parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.requirements["shared"] == "MUST do Y"

    def test_inherits_json_schema_path(self) -> None:
        parent = _schema("parent", json_schema_path="schema.json")
        child = _schema("child", parents=["parent"])
        named = {"parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.json_schema_path == "schema.json"

    def test_child_json_schema_overrides_parent(self) -> None:
        parent = _schema("parent", json_schema_path="parent.json")
        child = _schema("child", json_schema_path="child.json", parents=["parent"])
        named = {"parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.json_schema_path == "child.json"

    def test_appends_verification_commands(self) -> None:
        parent = _schema("parent", verification_cmds=["lint $1"])
        child = _schema("child", verification_cmds=["validate $1"], parents=["parent"])
        named = {"parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.verification_bash_command == ["lint $1", "validate $1"]

    def test_detects_circular_reference(self) -> None:
        a = _schema("a", parents=["b"])
        b = _schema("b", parents=["a"])
        named = {"a": a, "b": b}
        with pytest.raises(DeepSchemaError, match="Circular parent reference"):
            resolve_inheritance(a, named)

    def test_missing_parent_raises_error(self) -> None:
        child = _schema("child", parents=["nonexistent"])
        named = {"child": child}
        with pytest.raises(DeepSchemaError, match="unknown parent"):
            resolve_inheritance(child, named)

    def test_multi_level_inheritance(self) -> None:
        grandparent = _schema("gp", requirements={"gp_req": "MUST be A"})
        parent = _schema("parent", requirements={"p_req": "MUST be B"}, parents=["gp"])
        child = _schema("child", requirements={"c_req": "MUST be C"}, parents=["parent"])
        named = {"gp": grandparent, "parent": parent, "child": child}
        result = resolve_inheritance(child, named)
        assert result.requirements == {
            "gp_req": "MUST be A",
            "p_req": "MUST be B",
            "c_req": "MUST be C",
        }


class TestResolveAll:
    def test_resolves_all_schemas(self) -> None:
        parent = _schema("parent", requirements={"p1": "MUST be valid"})
        child = _schema("child", requirements={"c1": "SHOULD be nice"}, parents=["parent"])
        anon = DeepSchema(
            name="config.json",
            schema_type="anonymous",
            source_path=Path("/fake/.deepschema.config.json.yml"),
            requirements={"r1": "MUST exist"},
        )
        resolved, errors = resolve_all([parent, child, anon])
        assert len(resolved) == 3
        assert len(errors) == 0
        # Child should have merged requirements
        child_resolved = next(s for s in resolved if s.name == "child")
        assert "p1" in child_resolved.requirements
        assert "c1" in child_resolved.requirements

    def test_collects_resolution_errors(self) -> None:
        child = _schema("child", parents=["missing"])
        resolved, errors = resolve_all([child])
        assert len(errors) == 1
        assert "missing" in errors[0]
