"""Tests for policy definition parser."""

from pathlib import Path

import pytest

from deepwork.core.policy_parser import (
    DEFAULT_COMPARE_TO,
    Policy,
    PolicyParseError,
    evaluate_policies,
    evaluate_policy,
    matches_pattern,
    parse_policy_file,
)


class TestPolicy:
    """Tests for Policy dataclass."""

    def test_from_dict_with_inline_instructions(self) -> None:
        """Test creating policy from dict with inline instructions."""
        data = {
            "name": "Test Policy",
            "trigger": "src/**/*",
            "safety": "docs/readme.md",
            "instructions": "Do something",
        }
        policy = Policy.from_dict(data)

        assert policy.name == "Test Policy"
        assert policy.triggers == ["src/**/*"]
        assert policy.safety == ["docs/readme.md"]
        assert policy.instructions == "Do something"

    def test_from_dict_normalizes_trigger_string_to_list(self) -> None:
        """Test that trigger string is normalized to list."""
        data = {
            "name": "Test",
            "trigger": "*.py",
            "instructions": "Check it",
        }
        policy = Policy.from_dict(data)

        assert policy.triggers == ["*.py"]

    def test_from_dict_preserves_trigger_list(self) -> None:
        """Test that trigger list is preserved."""
        data = {
            "name": "Test",
            "trigger": ["*.py", "*.js"],
            "instructions": "Check it",
        }
        policy = Policy.from_dict(data)

        assert policy.triggers == ["*.py", "*.js"]

    def test_from_dict_normalizes_safety_string_to_list(self) -> None:
        """Test that safety string is normalized to list."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "safety": "docs/README.md",
            "instructions": "Check it",
        }
        policy = Policy.from_dict(data)

        assert policy.safety == ["docs/README.md"]

    def test_from_dict_safety_defaults_to_empty_list(self) -> None:
        """Test that missing safety defaults to empty list."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "instructions": "Check it",
        }
        policy = Policy.from_dict(data)

        assert policy.safety == []

    def test_from_dict_with_instructions_file(self, temp_dir: Path) -> None:
        """Test creating policy from dict with instructions_file."""
        # Create instructions file
        instructions_file = temp_dir / "instructions.md"
        instructions_file.write_text("# Instructions\nDo this and that.")

        data = {
            "name": "Test Policy",
            "trigger": "src/*",
            "instructions_file": "instructions.md",
        }
        policy = Policy.from_dict(data, base_dir=temp_dir)

        assert policy.instructions == "# Instructions\nDo this and that."

    def test_from_dict_instructions_file_not_found(self, temp_dir: Path) -> None:
        """Test error when instructions_file doesn't exist."""
        data = {
            "name": "Test Policy",
            "trigger": "src/*",
            "instructions_file": "nonexistent.md",
        }

        with pytest.raises(PolicyParseError, match="instructions file not found"):
            Policy.from_dict(data, base_dir=temp_dir)

    def test_from_dict_instructions_file_without_base_dir(self) -> None:
        """Test error when instructions_file used without base_dir."""
        data = {
            "name": "Test Policy",
            "trigger": "src/*",
            "instructions_file": "instructions.md",
        }

        with pytest.raises(PolicyParseError, match="no base_dir provided"):
            Policy.from_dict(data, base_dir=None)

    def test_from_dict_compare_to_defaults_to_base(self) -> None:
        """Test that compare_to defaults to 'base'."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "instructions": "Check it",
        }
        policy = Policy.from_dict(data)

        assert policy.compare_to == DEFAULT_COMPARE_TO
        assert policy.compare_to == "base"

    def test_from_dict_compare_to_explicit_base(self) -> None:
        """Test explicit compare_to: base."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "instructions": "Check it",
            "compare_to": "base",
        }
        policy = Policy.from_dict(data)

        assert policy.compare_to == "base"

    def test_from_dict_compare_to_default_tip(self) -> None:
        """Test compare_to: default_tip."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "instructions": "Check it",
            "compare_to": "default_tip",
        }
        policy = Policy.from_dict(data)

        assert policy.compare_to == "default_tip"

    def test_from_dict_compare_to_prompt(self) -> None:
        """Test compare_to: prompt."""
        data = {
            "name": "Test",
            "trigger": "src/*",
            "instructions": "Check it",
            "compare_to": "prompt",
        }
        policy = Policy.from_dict(data)

        assert policy.compare_to == "prompt"


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
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["src/main.py", "README.md"]

        assert evaluate_policy(policy, changed_files) is True

    def test_does_not_fire_when_no_trigger_match(self) -> None:
        """Test policy doesn't fire when no trigger matches."""
        policy = Policy(
            name="Test",
            triggers=["src/**/*.py"],
            safety=[],
            instructions="Check it",
        )
        changed_files = ["test/main.py", "README.md"]

        assert evaluate_policy(policy, changed_files) is False

    def test_does_not_fire_when_safety_matches(self) -> None:
        """Test policy doesn't fire when safety file is also changed."""
        policy = Policy(
            name="Test",
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "docs/install_guide.md"]

        assert evaluate_policy(policy, changed_files) is False

    def test_fires_when_trigger_matches_but_safety_doesnt(self) -> None:
        """Test policy fires when trigger matches but safety doesn't."""
        policy = Policy(
            name="Test",
            triggers=["app/config/**/*"],
            safety=["docs/install_guide.md"],
            instructions="Update docs",
        )
        changed_files = ["app/config/settings.py", "app/main.py"]

        assert evaluate_policy(policy, changed_files) is True

    def test_multiple_safety_patterns(self) -> None:
        """Test policy with multiple safety patterns."""
        policy = Policy(
            name="Test",
            triggers=["src/auth/**/*"],
            safety=["SECURITY.md", "docs/security_review.md"],
            instructions="Security review",
        )

        # Should not fire if any safety file is changed
        assert evaluate_policy(policy, ["src/auth/login.py", "SECURITY.md"]) is False
        assert evaluate_policy(policy, ["src/auth/login.py", "docs/security_review.md"]) is False

        # Should fire if no safety files changed
        assert evaluate_policy(policy, ["src/auth/login.py"]) is True


class TestEvaluatePolicies:
    """Tests for evaluate_policies function."""

    def test_returns_fired_policies(self) -> None:
        """Test that evaluate_policies returns all fired policies."""
        policies = [
            Policy(
                name="Policy 1",
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Policy(
                name="Policy 2",
                triggers=["test/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py", "test/test_main.py"]

        fired = evaluate_policies(policies, changed_files)

        assert len(fired) == 2
        assert fired[0].name == "Policy 1"
        assert fired[1].name == "Policy 2"

    def test_skips_promised_policies(self) -> None:
        """Test that promised policies are skipped."""
        policies = [
            Policy(
                name="Policy 1",
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
            Policy(
                name="Policy 2",
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 2",
            ),
        ]
        changed_files = ["src/main.py"]
        promised = {"Policy 1"}

        fired = evaluate_policies(policies, changed_files, promised)

        assert len(fired) == 1
        assert fired[0].name == "Policy 2"

    def test_returns_empty_when_no_policies_fire(self) -> None:
        """Test returns empty list when no policies fire."""
        policies = [
            Policy(
                name="Policy 1",
                triggers=["src/**/*"],
                safety=[],
                instructions="Do 1",
            ),
        ]
        changed_files = ["test/test_main.py"]

        fired = evaluate_policies(policies, changed_files)

        assert len(fired) == 0


class TestParsePolicyFile:
    """Tests for parse_policy_file function."""

    def test_parses_valid_policy_file(self, fixtures_dir: Path) -> None:
        """Test parsing a valid policy file."""
        policy_file = fixtures_dir / "policies" / "valid_policy.yml"
        policies = parse_policy_file(policy_file)

        assert len(policies) == 1
        assert policies[0].name == "Update install guide on config changes"
        assert policies[0].triggers == ["app/config/**/*"]
        assert policies[0].safety == ["docs/install_guide.md"]
        assert "Configuration files have changed" in policies[0].instructions

    def test_parses_multiple_policies(self, fixtures_dir: Path) -> None:
        """Test parsing a file with multiple policies."""
        policy_file = fixtures_dir / "policies" / "multiple_policies.yml"
        policies = parse_policy_file(policy_file)

        assert len(policies) == 3
        assert policies[0].name == "Update install guide on config changes"
        assert policies[1].name == "Security review for auth changes"
        assert policies[2].name == "API documentation update"

        # Check that arrays are parsed correctly
        assert policies[1].triggers == ["src/auth/**/*", "src/security/**/*"]
        assert policies[1].safety == ["SECURITY.md", "docs/security_review.md"]

    def test_parses_policy_with_instructions_file(self, fixtures_dir: Path) -> None:
        """Test parsing a policy with instructions_file."""
        policy_file = fixtures_dir / "policies" / "policy_with_instructions_file.yml"
        policies = parse_policy_file(policy_file)

        assert len(policies) == 1
        assert "Security Review Required" in policies[0].instructions
        assert "hardcoded credentials" in policies[0].instructions

    def test_empty_policy_file_returns_empty_list(self, fixtures_dir: Path) -> None:
        """Test that empty policy file returns empty list."""
        policy_file = fixtures_dir / "policies" / "empty_policy.yml"
        policies = parse_policy_file(policy_file)

        assert policies == []

    def test_raises_for_missing_trigger(self, fixtures_dir: Path) -> None:
        """Test error when policy is missing trigger."""
        policy_file = fixtures_dir / "policies" / "invalid_missing_trigger.yml"

        with pytest.raises(PolicyParseError, match="validation failed"):
            parse_policy_file(policy_file)

    def test_raises_for_missing_instructions(self, fixtures_dir: Path) -> None:
        """Test error when policy is missing both instructions and instructions_file."""
        policy_file = fixtures_dir / "policies" / "invalid_missing_instructions.yml"

        with pytest.raises(PolicyParseError, match="validation failed"):
            parse_policy_file(policy_file)

    def test_raises_for_nonexistent_file(self, temp_dir: Path) -> None:
        """Test error when policy file doesn't exist."""
        policy_file = temp_dir / "nonexistent.yml"

        with pytest.raises(PolicyParseError, match="does not exist"):
            parse_policy_file(policy_file)

    def test_raises_for_directory_path(self, temp_dir: Path) -> None:
        """Test error when path is a directory."""
        with pytest.raises(PolicyParseError, match="is not a file"):
            parse_policy_file(temp_dir)
