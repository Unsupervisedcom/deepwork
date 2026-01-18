"""Tests for schema validation (SV-8.x from test_scenarios.md)."""

from pathlib import Path

import pytest

from deepwork.core.rules_parser import RulesParseError, parse_rule_file


class TestRequiredFields:
    """Tests for required field validation (SV-8.1.x)."""

    def test_missing_name(self, tmp_path: Path) -> None:
        """SV-8.1.1: Missing name field."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
trigger: "src/**/*"
compare_to: base
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError, match="name"):
            parse_rule_file(rule_file)

    def test_missing_detection_mode(self, tmp_path: Path) -> None:
        """SV-8.1.2: Missing trigger, set, or pair."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
compare_to: base
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)

    def test_missing_compare_to(self, tmp_path: Path) -> None:
        """SV-8.1.5: Missing compare_to field."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError, match="compare_to"):
            parse_rule_file(rule_file)

    def test_missing_markdown_body(self, tmp_path: Path) -> None:
        """SV-8.1.3: Missing markdown body (for prompt action)."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
compare_to: base
---
"""
        )

        with pytest.raises(RulesParseError, match="markdown body|instructions"):
            parse_rule_file(rule_file)

    def test_set_requires_two_patterns(self, tmp_path: Path) -> None:
        """SV-8.1.4: Set requires at least 2 patterns.

        Note: Schema validation catches this before rule parser.
        """
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
set:
  - src/{path}.py
compare_to: base
---
Instructions here.
"""
        )

        # Schema validation will fail due to minItems: 2
        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)


class TestMutuallyExclusiveFields:
    """Tests for mutually exclusive field validation (SV-8.2.x)."""

    def test_both_trigger_and_set(self, tmp_path: Path) -> None:
        """SV-8.2.1: Both trigger and set is invalid."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)

    def test_both_trigger_and_pair(self, tmp_path: Path) -> None:
        """SV-8.2.2: Both trigger and pair is invalid."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
pair:
  trigger: api/{path}.py
  expects: docs/{path}.md
compare_to: base
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)

    def test_all_detection_modes(self, tmp_path: Path) -> None:
        """SV-8.2.3: All three detection modes is invalid."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
set:
  - src/{path}.py
  - tests/{path}_test.py
pair:
  trigger: api/{path}.py
  expects: docs/{path}.md
compare_to: base
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)


class TestValueValidation:
    """Tests for value validation (SV-8.4.x)."""

    def test_invalid_compare_to(self, tmp_path: Path) -> None:
        """SV-8.4.1: Invalid compare_to value."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
compare_to: yesterday
---
Instructions here.
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)

    def test_invalid_run_for(self, tmp_path: Path) -> None:
        """SV-8.4.2: Invalid run_for value."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: first_match
compare_to: prompt
---
"""
        )

        with pytest.raises(RulesParseError):
            parse_rule_file(rule_file)


class TestValidRules:
    """Tests for valid rule parsing."""

    def test_valid_trigger_safety_rule(self, tmp_path: Path) -> None:
        """Valid trigger/safety rule parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
safety: README.md
compare_to: base
---
Please check the code.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.name == "Test Rule"
        assert rule.triggers == ["src/**/*"]
        assert rule.safety == ["README.md"]
        assert rule.compare_to == "base"

    def test_valid_set_rule(self, tmp_path: Path) -> None:
        """Valid set rule parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
Source and test should change together.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.name == "Source/Test Pairing"
        assert len(rule.set_patterns) == 2
        assert rule.compare_to == "base"

    def test_valid_pair_rule(self, tmp_path: Path) -> None:
        """Valid pair rule parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: API Documentation
pair:
  trigger: api/{module}.py
  expects: docs/api/{module}.md
compare_to: base
---
API changes need documentation.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.name == "API Documentation"
        assert rule.pair_config is not None
        assert rule.pair_config.trigger == "api/{module}.py"
        assert rule.pair_config.expects == ["docs/api/{module}.md"]
        assert rule.compare_to == "base"

    def test_valid_command_rule(self, tmp_path: Path) -> None:
        """Valid command rule parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
compare_to: prompt
---
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.name == "Format Python"
        assert rule.command_action is not None
        assert rule.command_action.command == "ruff format {file}"
        assert rule.command_action.run_for == "each_match"
        assert rule.compare_to == "prompt"

    def test_valid_compare_to_values(self, tmp_path: Path) -> None:
        """Valid compare_to values parse successfully."""
        for compare_to in ["base", "default_tip", "prompt"]:
            rule_file = tmp_path / "test.md"
            rule_file.write_text(
                f"""---
name: Test Rule
trigger: "src/**/*"
compare_to: {compare_to}
---
Instructions here.
"""
            )

            rule = parse_rule_file(rule_file)
            assert rule.compare_to == compare_to

    def test_multiple_triggers(self, tmp_path: Path) -> None:
        """Multiple triggers as array parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger:
  - src/**/*.py
  - lib/**/*.py
compare_to: base
---
Instructions here.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.triggers == ["src/**/*.py", "lib/**/*.py"]
        assert rule.compare_to == "base"

    def test_multiple_safety_patterns(self, tmp_path: Path) -> None:
        """Multiple safety patterns as array parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: src/**/*
safety:
  - README.md
  - CHANGELOG.md
compare_to: base
---
Instructions here.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.safety == ["README.md", "CHANGELOG.md"]
        assert rule.compare_to == "base"

    def test_multiple_expects(self, tmp_path: Path) -> None:
        """Multiple expects patterns parses successfully."""
        rule_file = tmp_path / "test.md"
        rule_file.write_text(
            """---
name: Test Rule
pair:
  trigger: api/{module}.py
  expects:
    - docs/api/{module}.md
    - openapi/{module}.yaml
compare_to: base
---
Instructions here.
"""
        )

        rule = parse_rule_file(rule_file)
        assert rule.pair_config is not None
        assert rule.pair_config.expects == ["docs/api/{module}.md", "openapi/{module}.yaml"]
        assert rule.compare_to == "base"
