"""Tests for DeepSchema review bridge — synthetic ReviewRule generation."""

from pathlib import Path

from deepwork.deepschema.config import DeepSchema
from deepwork.deepschema.review_bridge import (
    _build_anonymous_instructions,
    _build_named_instructions,
    _build_requirements_body,
    _schema_to_review_rule,
    generate_review_rules,
)


def _named_schema(
    tmp_path: Path,
    name: str = "test_schema",
    matchers: list[str] | None = None,
    requirements: dict[str, str] | None = None,
    summary: str | None = "Test schema",
    instructions: str | None = "Handle with care",
) -> DeepSchema:
    source = tmp_path / ".deepwork" / "schemas" / name / "deepschema.yml"
    source.parent.mkdir(parents=True, exist_ok=True)
    return DeepSchema(
        name=name,
        schema_type="named",
        source_path=source,
        requirements=requirements or {"r1": "MUST be valid"},
        matchers=matchers or ["**/*.yml"],
        summary=summary,
        instructions=instructions,
    )


def _anonymous_schema(
    tmp_path: Path,
    target: str = "config.json",
    requirements: dict[str, str] | None = None,
) -> DeepSchema:
    source = tmp_path / f".deepschema.{target}.yml"
    return DeepSchema(
        name=target,
        schema_type="anonymous",
        source_path=source,
        requirements=requirements or {"r1": "MUST be valid"},
    )


class TestSchemaToReviewRule:
    def test_named_schema_produces_rule(self, tmp_path: Path) -> None:
        schema = _named_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.name == "test_schema DeepSchema Compliance"
        assert rule.strategy == "individual"
        assert rule.include_patterns == ["**/*.yml"]

    def test_anonymous_schema_produces_rule(self, tmp_path: Path) -> None:
        schema = _anonymous_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.name == "config.json DeepSchema Compliance"
        assert rule.strategy == "individual"
        assert rule.include_patterns == ["config.json"]

    def test_named_without_matchers_returns_none(self, tmp_path: Path) -> None:
        schema = _named_schema(tmp_path)
        schema.matchers = []
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is None

    def test_schema_without_requirements_returns_none(self, tmp_path: Path) -> None:
        schema = _named_schema(tmp_path)
        schema.requirements = {}
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is None

    def test_rule_source_file_points_to_schema(self, tmp_path: Path) -> None:
        schema = _named_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_file == schema.source_path

    def test_named_rule_source_dir_is_project_root(self, tmp_path: Path) -> None:
        """Named schemas use project-root-relative matchers, so source_dir must be project_root."""
        schema = _named_schema(tmp_path, matchers=[".deepwork/jobs/*/job.yml"])
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_dir == tmp_path

    def test_anonymous_rule_source_dir_is_schema_parent(self, tmp_path: Path) -> None:
        """Anonymous schemas match by filename in the same directory as the schema file."""
        schema = _anonymous_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_dir == schema.source_path.parent

    def test_named_rule_matchers_resolve_against_project_root(self, tmp_path: Path) -> None:
        """Matchers like '.deepwork/jobs/*/job.yml' must match files relative to project root."""
        from deepwork.review.matcher import match_rule

        schema = _named_schema(tmp_path, matchers=[".deepwork/jobs/*/job.yml"])
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None

        matched = match_rule([".deepwork/jobs/my_job/job.yml"], rule, tmp_path)
        assert matched == [".deepwork/jobs/my_job/job.yml"]

        not_matched = match_rule(["src/other/file.yml"], rule, tmp_path)
        assert not_matched == []


class TestAnonymousSchemaRuleOutsideProject:
    """Tests for _anonymous_schema_rule when target is outside project_root (lines 99-100)."""

    def test_returns_none_when_target_outside_project(self, tmp_path: Path) -> None:
        """Anonymous schema whose target resolves outside project_root returns None."""
        from deepwork.deepschema.review_bridge import _anonymous_schema_rule

        schema = DeepSchema(
            name="config.json",
            schema_type="anonymous",
            source_path=Path("/outside/.deepschema.config.json.yml"),
            requirements={"r1": "MUST be valid"},
        )
        rule = _anonymous_schema_rule(schema, tmp_path)
        assert rule is None


class TestBuildInstructions:
    def test_named_includes_summary_and_instructions(self, tmp_path: Path) -> None:
        schema = _named_schema(tmp_path, summary="YAML configs", instructions="Validate carefully")
        text = _build_named_instructions(schema)
        assert "test_schema" in text
        assert "YAML configs" in text
        assert "Validate carefully" in text
        assert "MUST be valid" in text

    def test_anonymous_is_simpler(self, tmp_path: Path) -> None:
        schema = _anonymous_schema(tmp_path)
        text = _build_anonymous_instructions(schema)
        assert "has requirements" in text
        assert "MUST be valid" in text

    def test_requirements_body_includes_rfc_guidance(self) -> None:
        body = _build_requirements_body({"r1": "MUST exist", "r2": "SHOULD be nice"})
        assert "fail reviews over anything that is MUST" in body
        assert "r1" in body
        assert "r2" in body


class TestGenerateReviewRules:
    def test_generates_from_named_schema(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "yml_files"
        schema_dir.mkdir(parents=True)
        (schema_dir / "deepschema.yml").write_text(
            "summary: 'YAML files'\nmatchers:\n  - '**/*.yml'\nrequirements:\n  r1: 'MUST exist'\n",
            encoding="utf-8",
        )
        rules, errors = generate_review_rules(tmp_path)
        rule_names = [r.name for r in rules]
        assert "yml_files DeepSchema Compliance" in rule_names
        assert len(errors) == 0

    def test_generates_from_anonymous_schema(self, tmp_path: Path) -> None:
        (tmp_path / ".deepschema.config.json.yml").write_text(
            "requirements:\n  r1: 'MUST be valid JSON'\n",
            encoding="utf-8",
        )
        rules, errors = generate_review_rules(tmp_path)
        rule_names = [r.name for r in rules]
        assert "config.json DeepSchema Compliance" in rule_names
