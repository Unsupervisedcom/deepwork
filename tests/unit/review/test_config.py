"""Tests for deepreview configuration parsing (deepwork.review.config)."""

from pathlib import Path

import pytest

from deepwork.review.config import ConfigError, ReviewRule, parse_deepreview_file


def _write_deepreview(path: Path, content: str) -> Path:
    """Write a .deepreview file and return its path."""
    filepath = path / ".deepreview"
    filepath.write_text(content, encoding="utf-8")
    return filepath


class TestParseDeepReviewFile:
    """Tests for parse_deepreview_file."""

    # REQ-001.1.1, REQ-001.1.2
    def test_parses_valid_yaml_with_single_rule(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
python_review:
  match:
    include:
      - "**/*.py"
  review:
    strategy: individual
    instructions: "Review this Python file."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert len(rules) == 1
        assert rules[0].name == "python_review"
        assert rules[0].include_patterns == ["**/*.py"]
        assert rules[0].strategy == "individual"
        assert rules[0].instructions == "Review this Python file."

    # REQ-001.1.2
    def test_parses_multiple_rules(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
rule_a:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Rule A"
rule_b:
  match:
    include: ["**/*.ts"]
  review:
    strategy: matches_together
    instructions: "Rule B"
""",
        )
        rules = parse_deepreview_file(filepath)
        assert len(rules) == 2
        names = {r.name for r in rules}
        assert names == {"rule_a", "rule_b"}

    # REQ-001.2.3
    def test_parses_exclude_patterns(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
    exclude: ["tests/**/*.py"]
  review:
    strategy: individual
    instructions: "Review it."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].exclude_patterns == ["tests/**/*.py"]

    # REQ-001.8.4
    def test_exclude_defaults_to_empty(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review it."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].exclude_patterns == []

    # REQ-001.3.2
    def test_parses_all_strategies(self, tmp_path: Path) -> None:
        for strategy in ("individual", "matches_together", "all_changed_files"):
            filepath = _write_deepreview(
                tmp_path,
                f"""
rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: {strategy}
    instructions: "Review."
""",
            )
            rules = parse_deepreview_file(filepath)
            assert rules[0].strategy == strategy

    # REQ-001.4.1, REQ-001.4.2
    def test_inline_instructions(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Check for bugs."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].instructions == "Check for bugs."

    # REQ-001.4.1, REQ-001.4.3, REQ-001.4.4
    def test_file_reference_instructions(self, tmp_path: Path) -> None:
        (tmp_path / "review_guide.md").write_text("# Review Guide\nCheck everything.", encoding="utf-8")
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions:
      file: review_guide.md
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].instructions == "# Review Guide\nCheck everything."

    # REQ-001.4.5
    def test_file_reference_not_found_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions:
      file: nonexistent.md
""",
        )
        with pytest.raises(ConfigError, match="Instructions file not found"):
            parse_deepreview_file(filepath)

    # REQ-001.5.1, REQ-001.5.3
    def test_parses_agent_config(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    agent:
      claude: security-expert
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].agent == {"claude": "security-expert"}

    # REQ-001.8.6
    def test_agent_defaults_to_none(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].agent is None

    # REQ-001.6.2, REQ-001.6.3
    def test_parses_additional_context(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    additional_context:
      all_changed_filenames: true
      unchanged_matching_files: true
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].all_changed_filenames is True
        assert rules[0].unchanged_matching_files is True

    # REQ-001.8.5
    def test_additional_context_defaults_to_false(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].all_changed_filenames is False
        assert rules[0].unchanged_matching_files is False

    # REQ-001.8.3
    def test_source_dir_set_to_parent(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].source_dir == tmp_path

    # REQ-001.7.4
    def test_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(tmp_path, "invalid: [yaml")
        with pytest.raises(ConfigError, match="Failed to parse"):
            parse_deepreview_file(filepath)

    # REQ-001.7.4
    def test_schema_validation_failure_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: invalid_strategy
    instructions: "Review."
""",
        )
        with pytest.raises(ConfigError, match="Schema validation failed"):
            parse_deepreview_file(filepath)

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(tmp_path, "")
        rules = parse_deepreview_file(filepath)
        assert rules == []

    def test_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        filepath = tmp_path / ".deepreview"
        with pytest.raises(ConfigError, match="File not found"):
            parse_deepreview_file(filepath)

    # REQ-001.8.4, REQ-001.8.5
    def test_source_file_is_set(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
python_review:
  match:
    include:
      - "**/*.py"
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].source_file == filepath

    def test_source_line_for_single_rule(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """python_review:
  match:
    include:
      - "**/*.py"
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].source_line == 1

    def test_source_line_for_multiple_rules(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """rule_a:
  match:
    include:
      - "**/*.py"
  review:
    strategy: individual
    instructions: "Review A."
rule_b:
  match:
    include:
      - "**/*.js"
  review:
    strategy: individual
    instructions: "Review B."
""",
        )
        rules = parse_deepreview_file(filepath)
        rule_map = {r.name: r for r in rules}
        assert rule_map["rule_a"].source_line == 1
        assert rule_map["rule_b"].source_line == 8
