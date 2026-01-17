"""Tests for rule definition parser."""

from pathlib import Path

import pytest

from deepwork.core.pattern_matcher import matches_any_pattern as matches_pattern
from deepwork.core.rules_parser import (
    DEFAULT_COMPARE_TO,
    DetectionMode,
    Rule,
    RulesParseError,
    evaluate_rules,
    evaluate_rule,
    load_rules_from_directory,
)


class TestMatchesPattern:
    """Tests for matches_pattern function."""

    def test_simple_glob_match(self) -> None:
        """Test simple glob pattern matching."""
        assert matches_pattern("file.py", ["*.py"])
        assert not matches_pattern("file.js", ["*.py"])

    def test_directory_glob_match(self) -> None:
        """Test directory pattern matching."""
        assert matches_pattern("src/file.py", ["src/*"])
        assert not matches_pattern("test/file.py", ["src/*"])

    def test_recursive_glob_match(self) -> None:
        """Test recursive ** pattern matching."""
        assert matches_pattern("src/deep/nested/file.py", ["src/**/*.py"])
        assert matches_pattern("src/file.py", ["src/**/*.py"])
        assert not matches_pattern("test/file.py", ["src/**/*.py"])

    def test_multiple_patterns(self) -> None:
        """Test matching against multiple patterns."""
        patterns = ["*.py", "*.js"]
        assert matches_pattern("file.py", patterns)
        assert matches_pattern("file.js", patterns)
        assert not matches_pattern("file.txt", patterns)

    def test_config_directory_pattern(self) -> None:
        """Test pattern like app/config/**/*."""
        assert matches_pattern("app/config/settings.py", ["app/config/**/*"])
        assert matches_pattern("app/config/nested/deep.yml", ["app/config/**/*"])
        assert not matches_pattern("app/other/file.py", ["app/config/**/*"])


class TestEvaluateRule:
    """Tests for evaluate_rule function."""

    def test_fires_when_trigger_matches(self) -> None:
        """Test rule fires when trigger matches."""
        rule = Rule(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["src/main.py", "README.md"]

        result = evaluate_rule(rule, changed_files)
        assert result.should_fire is True

    def test_does_not_fire_when_no_trigger_match(self) -> None:
        """Test rule doesn't fire when no trigger matches."""
        rule = Rule(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["test/main.py", "README.md"]

        result = evaluate_rule(rule, changed_files)
        assert result.should_fire is False

    def test_does_not_fire_when_safety_matches(self) -> None:
        """Test rule doesn't fire when safety file is also changed."""
        rule = Rule(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "docs/install_guide.md"]

        result = evaluate_rule(rule, changed_files)
        assert result.should_fire is False

    def test_fires_when_trigger_matches_but_safety_doesnt(self) -> None:
        """Test rule fires when trigger matches but safety doesn't."""
        rule = Rule(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "app/main.py"]

        result = evaluate_rule(rule, changed_files)
        assert result.should_fire is True

    def test_multiple_safety_patterns(self) -> None:
        """Test rule with multiple safety patterns."""
        rule = Rule(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/auth/**/*"],
            safety=["SECURITY.md", "docs/security_review.md"],
            instructions="Security review",
        )

        # Should not fire if any safety file is changed
        result1 = evaluate_rule(rule, ["src/auth/login.py", "SECURITY.md"])
        assert result1.should_fire is False
        result2 = evaluate_rule(rule, ["src/auth/login.py", "docs/security_review.md"])
        assert result2.should_fire is False

        # Should fire if no safety files changed
        result3 = evaluate_rule(rule, ["src/auth/login.py"])
        assert result3.should_fire is True


class TestEvaluateRules:
    """Tests for evaluate_rules function."""

    def test_returns_fired_rules(self) -> None:
        """Test that evaluate_rules returns all fired rules."""
        rules = [
            Rule(
                name="Rule 1",
                filename="rule1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Rule(
                name="Rule 2",
                filename="rule2",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["test/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py", "test/test_main.py"]

        fired = evaluate_rules(rules, changed_files)

        assert len(fired) == 2
        assert fired[0].rule.name == "Rule 1"
        assert fired[1].rule.name == "Rule 2"

    def test_skips_promised_rules(self) -> None:
        """Test that promised rules are skipped."""
        rules = [
            Rule(
                name="Rule 1",
                filename="rule1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Rule(
                name="Rule 2",
                filename="rule2",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py"]
        promised = {"Rule 1"}

        fired = evaluate_rules(rules, changed_files, promised)

        assert len(fired) == 1
        assert fired[0].rule.name == "Rule 2"

    def test_returns_empty_when_no_rules_fire(self) -> None:
        """Test returns empty list when no rules fire."""
        rules = [
            Rule(
                name="Rule 1",
                filename="rule1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
        ]
        changed_files = ["test/test_main.py"]

        fired = evaluate_rules(rules, changed_files)

        assert len(fired) == 0


class TestLoadRulesFromDirectory:
    """Tests for load_rules_from_directory function."""

    def test_loads_rules_from_directory(self, temp_dir: Path) -> None:
        """Test loading rules from a directory."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        # Create a rule file
        rule_file = rules_dir / "test-rule.md"
        rule_file.write_text(
            """---
name: Test Rule
trigger: "src/**/*"
---
Please check the source files.
"""
        )

        rules = load_rules_from_directory(rules_dir)

        assert len(rules) == 1
        assert rules[0].name == "Test Rule"
        assert rules[0].triggers == ["src/**/*"]
        assert rules[0].detection_mode == DetectionMode.TRIGGER_SAFETY
        assert "check the source files" in rules[0].instructions

    def test_loads_multiple_rules(self, temp_dir: Path) -> None:
        """Test loading multiple rules."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        # Create rule files
        (rules_dir / "rule1.md").write_text(
            """---
name: Rule 1
trigger: "src/**/*"
---
Instructions for rule 1.
"""
        )
        (rules_dir / "rule2.md").write_text(
            """---
name: Rule 2
trigger: "test/**/*"
---
Instructions for rule 2.
"""
        )

        rules = load_rules_from_directory(rules_dir)

        assert len(rules) == 2
        names = {r.name for r in rules}
        assert names == {"Rule 1", "Rule 2"}

    def test_returns_empty_for_empty_directory(self, temp_dir: Path) -> None:
        """Test that empty directory returns empty list."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        rules = load_rules_from_directory(rules_dir)

        assert rules == []

    def test_returns_empty_for_nonexistent_directory(self, temp_dir: Path) -> None:
        """Test that nonexistent directory returns empty list."""
        rules_dir = temp_dir / "nonexistent"

        rules = load_rules_from_directory(rules_dir)

        assert rules == []

    def test_loads_rule_with_set_detection_mode(self, temp_dir: Path) -> None:
        """Test loading a rule with set detection mode."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        rule_file = rules_dir / "source-test-pairing.md"
        rule_file.write_text(
            """---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test files should change together.
"""
        )

        rules = load_rules_from_directory(rules_dir)

        assert len(rules) == 1
        assert rules[0].name == "Source/Test Pairing"
        assert rules[0].detection_mode == DetectionMode.SET
        assert rules[0].set_patterns == ["src/{path}.py", "tests/{path}_test.py"]

    def test_loads_rule_with_pair_detection_mode(self, temp_dir: Path) -> None:
        """Test loading a rule with pair detection mode."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        rule_file = rules_dir / "api-docs.md"
        rule_file.write_text(
            """---
name: API Documentation
pair:
  trigger: src/api/{name}.py
  expects: docs/api/{name}.md
---
API code requires documentation.
"""
        )

        rules = load_rules_from_directory(rules_dir)

        assert len(rules) == 1
        assert rules[0].name == "API Documentation"
        assert rules[0].detection_mode == DetectionMode.PAIR
        assert rules[0].pair_config is not None
        assert rules[0].pair_config.trigger == "src/api/{name}.py"
        assert rules[0].pair_config.expects == ["docs/api/{name}.md"]

    def test_loads_rule_with_command_action(self, temp_dir: Path) -> None:
        """Test loading a rule with command action."""
        rules_dir = temp_dir / "rules"
        rules_dir.mkdir()

        rule_file = rules_dir / "format-python.md"
        rule_file.write_text(
            """---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
---
"""
        )

        rules = load_rules_from_directory(rules_dir)

        assert len(rules) == 1
        assert rules[0].name == "Format Python"
        from deepwork.core.rules_parser import ActionType

        assert rules[0].action_type == ActionType.COMMAND
        assert rules[0].command_action is not None
        assert rules[0].command_action.command == "ruff format {file}"
        assert rules[0].command_action.run_for == "each_match"
