"""Tests for deepreview configuration parsing (deepwork.review.config).

Validates requirements: REVIEW-REQ-001, REVIEW-REQ-001.1, REVIEW-REQ-001.2,
REVIEW-REQ-001.3, REVIEW-REQ-001.4, REVIEW-REQ-001.5, REVIEW-REQ-001.6,
REVIEW-REQ-001.7, REVIEW-REQ-001.8.
"""

from pathlib import Path
from typing import Any

import pytest

from deepwork.review.config import ConfigError, parse_deepreview_file
from deepwork.review.schema import get_schema_path


def _write_deepreview(path: Path, content: str) -> Path:
    """Write a .deepreview file and return its path."""
    filepath = path / ".deepreview"
    filepath.write_text(content, encoding="utf-8")
    return filepath


class TestParseDeepReviewFile:
    """Tests for parse_deepreview_file."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.1.1, REVIEW-REQ-001.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_valid_yaml_with_single_rule(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
python_review:
  description: "Review Python files."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_multiple_rules(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
rule_a:
  description: "Rule A description."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Rule A"
rule_b:
  description: "Rule B description."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_exclude_patterns(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_exclude_defaults_to_empty(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review it."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].exclude_patterns == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_all_strategies(self, tmp_path: Path) -> None:
        for strategy in ("individual", "matches_together", "all_changed_files"):
            filepath = _write_deepreview(
                tmp_path,
                f"""
rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: {strategy}
    instructions: "Review."
""",
            )
            rules = parse_deepreview_file(filepath)
            assert rules[0].strategy == strategy

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.4.1, REVIEW-REQ-001.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_inline_instructions(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Check for bugs."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].instructions == "Check for bugs."

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.4.1, REVIEW-REQ-001.4.3, REVIEW-REQ-001.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_file_reference_instructions(self, tmp_path: Path) -> None:
        (tmp_path / "review_guide.md").write_text(
            "# Review Guide\nCheck everything.", encoding="utf-8"
        )
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.4.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_file_reference_not_found_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.5.1, REVIEW-REQ-001.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_agent_config(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_defaults_to_none(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].agent is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.6.2, REVIEW-REQ-001.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parses_additional_context(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_additional_context_defaults_to_false(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_source_dir_set_to_parent(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review."
""",
        )
        rules = parse_deepreview_file(filepath)
        assert rules[0].source_dir == tmp_path

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(tmp_path, "invalid: [yaml")
        with pytest.raises(ConfigError, match="Failed to parse"):
            parse_deepreview_file(filepath)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_schema_validation_failure_raises_error(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.1.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        filepath = _write_deepreview(tmp_path, "")
        rules = parse_deepreview_file(filepath)
        assert rules == []

    def test_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.7.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        filepath = tmp_path / ".deepreview"
        with pytest.raises(ConfigError, match="File not found"):
            parse_deepreview_file(filepath)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.4, REVIEW-REQ-001.8.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_source_file_is_set(self, tmp_path: Path) -> None:
        filepath = _write_deepreview(
            tmp_path,
            """
python_review:
  description: "Test rule."
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        filepath = _write_deepreview(
            tmp_path,
            """python_review:
  description: "Test rule."
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
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        filepath = _write_deepreview(
            tmp_path,
            """rule_a:
  description: "Rule A."
  match:
    include:
      - "**/*.py"
  review:
    strategy: individual
    instructions: "Review A."
rule_b:
  description: "Rule B."
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
        assert rule_map["rule_b"].source_line == 9

    def test_file_reference_read_error_raises_config_error(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.4.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """OSError reading an instructions file raises ConfigError."""
        from unittest.mock import patch

        # Create the file so the "not found" check passes
        instructions_file = tmp_path / "review_guide.md"
        instructions_file.write_text("content")

        filepath = _write_deepreview(
            tmp_path,
            """
my_rule:
  description: "Test rule."
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions:
      file: review_guide.md
""",
        )

        # Make the file unreadable by patching Path.read_text
        original_read_text = Path.read_text

        def mock_read_text(self_path: Path, *args: Any, **kwargs: Any) -> str:
            if self_path.name == "review_guide.md":
                raise OSError("Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        with patch.object(Path, "read_text", mock_read_text):
            with pytest.raises(ConfigError, match="Failed to read instructions file"):
                parse_deepreview_file(filepath)


class TestGetSchemaPath:
    """Tests for get_schema_path."""

    def test_returns_path_to_json_schema(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.7.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """get_schema_path returns a Path to the deepreview_schema.json file."""
        path = get_schema_path()
        assert path.name == "deepreview_schema.json"
        assert path.exists()


class TestFindRuleLineNumbers:
    """Tests for _find_rule_line_numbers edge cases."""

    def test_returns_empty_on_os_error(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.8.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """OSError reading .deepreview file returns empty dict."""
        from unittest.mock import patch

        from deepwork.review.config import _find_rule_line_numbers

        filepath = tmp_path / ".deepreview"
        filepath.write_text("rule_a:\n  key: value\n")

        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            result = _find_rule_line_numbers(filepath)
        assert result == {}
