"""Tests for DeepSchema review bridge — synthetic ReviewRule generation.

Validates requirements: DW-REQ-011.6, DW-REQ-011.8.
"""

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
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1, DW-REQ-011.8.2, DW-REQ-011.8.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _named_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.name == "test_schema DeepSchema Compliance"
        assert rule.strategy == "individual"
        assert rule.include_patterns == ["**/*.yml"]

    def test_anonymous_schema_produces_rule(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1, DW-REQ-011.8.2, DW-REQ-011.8.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _anonymous_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.name == "config.json DeepSchema Compliance"
        assert rule.strategy == "individual"
        assert rule.include_patterns == ["config.json"]

    def test_named_without_matchers_returns_none(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _named_schema(tmp_path)
        schema.matchers = []
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is None

    def test_schema_without_requirements_returns_none(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _named_schema(tmp_path)
        schema.requirements = {}
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is None

    def test_rule_source_file_points_to_schema(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _named_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_file == schema.source_path

    def test_named_rule_source_dir_is_project_root(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Named schemas use project-root-relative matchers, so source_dir must be project_root."""
        schema = _named_schema(tmp_path, matchers=[".deepwork/jobs/*/job.yml"])
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_dir == tmp_path

    def test_anonymous_rule_source_dir_is_schema_parent(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Anonymous schemas match by filename in the same directory as the schema file."""
        schema = _anonymous_schema(tmp_path)
        rule = _schema_to_review_rule(schema, tmp_path)
        assert rule is not None
        assert rule.source_dir == schema.source_path.parent

    def test_named_rule_matchers_resolve_against_project_root(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.6.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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
    """Tests for _anonymous_schema_rule when target is outside project_root."""

    def test_returns_none_when_target_outside_project(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _named_schema(tmp_path, summary="YAML configs", instructions="Validate carefully")
        text = _build_named_instructions(schema)
        assert "test_schema" in text
        assert "YAML configs" in text
        assert "Validate carefully" in text
        assert "MUST be valid" in text

    def test_anonymous_is_simpler(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        schema = _anonymous_schema(tmp_path)
        text = _build_anonymous_instructions(schema)
        assert "has requirements" in text
        assert "MUST be valid" in text

    def test_requirements_body_includes_rfc_guidance(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        body = _build_requirements_body({"r1": "MUST exist", "r2": "SHOULD be nice"})
        assert "fail reviews over anything that is MUST" in body
        assert "r1" in body
        assert "r2" in body


class TestGenerateReviewRules:
    def test_generates_from_named_schema(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.8.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        (tmp_path / ".deepschema.config.json.yml").write_text(
            "requirements:\n  r1: 'MUST be valid JSON'\n",
            encoding="utf-8",
        )
        rules, errors = generate_review_rules(tmp_path)
        rule_names = [r.name for r in rules]
        assert "config.json DeepSchema Compliance" in rule_names


class TestCollectReferenceFiles:
    """Tests for _collect_reference_files populating reference_files."""

    def _write_schema_yaml(self, schema_dir: Path, body: str) -> Path:
        schema_dir.mkdir(parents=True, exist_ok=True)
        path = schema_dir / "deepschema.yml"
        path.write_text(body, encoding="utf-8")
        return path

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.11.1, DW-REQ-011.11.2,
    # DW-REQ-011.11.3, DW-REQ-011.11.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_references_and_json_schema_populate_refs_examples_listed(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "thing"
        self._write_schema_yaml(
            schema_dir,
            """
summary: "x"
matchers: ["**/*.yml"]
json_schema_path: "thing.schema.json"
examples:
  - path: "example.yml"
    description: "an example"
references:
  - path: "../guide.md"
    description: "guide"
requirements:
  r1: "MUST be valid"
""",
        )
        (schema_dir / "example.yml").write_text("k: v")
        (schema_dir / "thing.schema.json").write_text("{}")
        (schema_dir.parent / "guide.md").write_text("# guide")

        rules, errors = generate_review_rules(tmp_path)
        rule = next(r for r in rules if r.name == "thing DeepSchema Compliance")
        # Examples are NOT in reference_files (they are listed in instructions only).
        labels = {r.relative_label for r in rule.reference_files}
        assert labels == {"../guide.md", "thing.schema.json"}
        by_label = {r.relative_label: r for r in rule.reference_files}
        assert by_label["../guide.md"].path == (schema_dir.parent / "guide.md").resolve()
        assert by_label["thing.schema.json"].path == (schema_dir / "thing.schema.json").resolve()
        # Examples listed in the rule's instructions text.
        assert "Example files available for reference" in rule.instructions
        assert "`example.yml`" in rule.instructions
        assert "an example" in rule.instructions
        assert errors == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.11.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_reference_file_surfaces_error(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "thing"
        self._write_schema_yaml(
            schema_dir,
            """
summary: "x"
matchers: ["**/*.yml"]
references:
  - path: "missing.md"
    description: "nope"
requirements:
  r1: "MUST be valid"
""",
        )
        rules, errors = generate_review_rules(tmp_path)
        rule = next(r for r in rules if r.name == "thing DeepSchema Compliance")
        assert rule.reference_files == []
        assert any("missing.md" in e for e in errors)

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-011.11.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_url_references_are_skipped(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / ".deepwork" / "schemas" / "thing"
        self._write_schema_yaml(
            schema_dir,
            """
summary: "x"
matchers: ["**/*.yml"]
references:
  - path: "https://www.ietf.org/rfc/rfc2119.txt"
    description: "RFC 2119"
requirements:
  r1: "MUST be valid"
""",
        )
        rules, errors = generate_review_rules(tmp_path)
        rule = next(r for r in rules if r.name == "thing DeepSchema Compliance")
        assert rule.reference_files == []
        assert not any("rfc2119" in e for e in errors)
