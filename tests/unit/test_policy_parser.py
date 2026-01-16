"""Tests for policy definition parser."""

from pathlib import Path

import pytest

from deepwork.core.pattern_matcher import matches_any_pattern as matches_pattern
from deepwork.core.policy_parser import (
    DEFAULT_COMPARE_TO,
    DetectionMode,
    Policy,
    PolicyParseError,
    evaluate_policies,
    evaluate_policy,
    load_policies_from_directory,
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


class TestEvaluatePolicy:
    """Tests for evaluate_policy function."""

    def test_fires_when_trigger_matches(self) -> None:
        """Test policy fires when trigger matches."""
        policy = Policy(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["src/main.py", "README.md"]

        result = evaluate_policy(policy, changed_files)
        assert result.should_fire is True

    def test_does_not_fire_when_no_trigger_match(self) -> None:
        """Test policy doesn't fire when no trigger matches."""
        policy = Policy(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["test/main.py", "README.md"]

        result = evaluate_policy(policy, changed_files)
        assert result.should_fire is False

    def test_does_not_fire_when_safety_matches(self) -> None:
        """Test policy doesn't fire when safety file is also changed."""
        policy = Policy(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "docs/install_guide.md"]

        result = evaluate_policy(policy, changed_files)
        assert result.should_fire is False

    def test_fires_when_trigger_matches_but_safety_doesnt(self) -> None:
        """Test policy fires when trigger matches but safety doesn't."""
        policy = Policy(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "app/main.py"]

        result = evaluate_policy(policy, changed_files)
        assert result.should_fire is True

    def test_multiple_safety_patterns(self) -> None:
        """Test policy with multiple safety patterns."""
        policy = Policy(
            name="Test",
            filename="test",
            detection_mode=DetectionMode.TRIGGER_SAFETY,
            triggers=["src/auth/**/*"],
            safety=["SECURITY.md", "docs/security_review.md"],
            instructions="Security review",
        )

        # Should not fire if any safety file is changed
        result1 = evaluate_policy(policy, ["src/auth/login.py", "SECURITY.md"])
        assert result1.should_fire is False
        result2 = evaluate_policy(policy, ["src/auth/login.py", "docs/security_review.md"])
        assert result2.should_fire is False

        # Should fire if no safety files changed
        result3 = evaluate_policy(policy, ["src/auth/login.py"])
        assert result3.should_fire is True


class TestEvaluatePolicies:
    """Tests for evaluate_policies function."""

    def test_returns_fired_policies(self) -> None:
        """Test that evaluate_policies returns all fired policies."""
        policies = [
            Policy(
                name="Policy 1",
                filename="policy1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Policy(
                name="Policy 2",
                filename="policy2",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["test/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py", "test/test_main.py"]

        fired = evaluate_policies(policies, changed_files)

        assert len(fired) == 2
        assert fired[0].policy.name == "Policy 1"
        assert fired[1].policy.name == "Policy 2"

    def test_skips_promised_policies(self) -> None:
        """Test that promised policies are skipped."""
        policies = [
            Policy(
                name="Policy 1",
                filename="policy1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Policy(
                name="Policy 2",
                filename="policy2",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py"]
        promised = {"Policy 1"}

        fired = evaluate_policies(policies, changed_files, promised)

        assert len(fired) == 1
        assert fired[0].policy.name == "Policy 2"

    def test_returns_empty_when_no_policies_fire(self) -> None:
        """Test returns empty list when no policies fire."""
        policies = [
            Policy(
                name="Policy 1",
                filename="policy1",
                detection_mode=DetectionMode.TRIGGER_SAFETY,
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
        ]
        changed_files = ["test/test_main.py"]

        fired = evaluate_policies(policies, changed_files)

        assert len(fired) == 0


class TestLoadPoliciesFromDirectory:
    """Tests for load_policies_from_directory function."""

    def test_loads_policies_from_directory(self, temp_dir: Path) -> None:
        """Test loading policies from a directory."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        # Create a policy file
        policy_file = policies_dir / "test-policy.md"
        policy_file.write_text(
            """---
name: Test Policy
trigger: "src/**/*"
---
Please check the source files.
"""
        )

        policies = load_policies_from_directory(policies_dir)

        assert len(policies) == 1
        assert policies[0].name == "Test Policy"
        assert policies[0].triggers == ["src/**/*"]
        assert policies[0].detection_mode == DetectionMode.TRIGGER_SAFETY
        assert "check the source files" in policies[0].instructions

    def test_loads_multiple_policies(self, temp_dir: Path) -> None:
        """Test loading multiple policies."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        # Create policy files
        (policies_dir / "policy1.md").write_text(
            """---
name: Policy 1
trigger: "src/**/*"
---
Instructions for policy 1.
"""
        )
        (policies_dir / "policy2.md").write_text(
            """---
name: Policy 2
trigger: "test/**/*"
---
Instructions for policy 2.
"""
        )

        policies = load_policies_from_directory(policies_dir)

        assert len(policies) == 2
        names = {p.name for p in policies}
        assert names == {"Policy 1", "Policy 2"}

    def test_returns_empty_for_empty_directory(self, temp_dir: Path) -> None:
        """Test that empty directory returns empty list."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        policies = load_policies_from_directory(policies_dir)

        assert policies == []

    def test_returns_empty_for_nonexistent_directory(self, temp_dir: Path) -> None:
        """Test that nonexistent directory returns empty list."""
        policies_dir = temp_dir / "nonexistent"

        policies = load_policies_from_directory(policies_dir)

        assert policies == []

    def test_loads_policy_with_set_detection_mode(self, temp_dir: Path) -> None:
        """Test loading a policy with set detection mode."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        policy_file = policies_dir / "source-test-pairing.md"
        policy_file.write_text(
            """---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test files should change together.
"""
        )

        policies = load_policies_from_directory(policies_dir)

        assert len(policies) == 1
        assert policies[0].name == "Source/Test Pairing"
        assert policies[0].detection_mode == DetectionMode.SET
        assert policies[0].set_patterns == ["src/{path}.py", "tests/{path}_test.py"]

    def test_loads_policy_with_pair_detection_mode(self, temp_dir: Path) -> None:
        """Test loading a policy with pair detection mode."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        policy_file = policies_dir / "api-docs.md"
        policy_file.write_text(
            """---
name: API Documentation
pair:
  trigger: src/api/{name}.py
  expects: docs/api/{name}.md
---
API code requires documentation.
"""
        )

        policies = load_policies_from_directory(policies_dir)

        assert len(policies) == 1
        assert policies[0].name == "API Documentation"
        assert policies[0].detection_mode == DetectionMode.PAIR
        assert policies[0].pair_config is not None
        assert policies[0].pair_config.trigger == "src/api/{name}.py"
        assert policies[0].pair_config.expects == ["docs/api/{name}.md"]

    def test_loads_policy_with_command_action(self, temp_dir: Path) -> None:
        """Test loading a policy with command action."""
        policies_dir = temp_dir / "policies"
        policies_dir.mkdir()

        policy_file = policies_dir / "format-python.md"
        policy_file.write_text(
            """---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
---
"""
        )

        policies = load_policies_from_directory(policies_dir)

        assert len(policies) == 1
        assert policies[0].name == "Format Python"
        from deepwork.core.policy_parser import ActionType

        assert policies[0].action_type == ActionType.COMMAND
        assert policies[0].command_action is not None
        assert policies[0].command_action.command == "ruff format {file}"
        assert policies[0].command_action.run_for == "each_match"
