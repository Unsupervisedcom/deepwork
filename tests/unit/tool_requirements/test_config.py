"""Tests for tool requirements config parsing (DW-REQ-012.1)."""

from pathlib import Path

import pytest
import yaml

from deepwork.tool_requirements.config import (
    ToolRequirementsError,
    parse_policy_file,
)


@pytest.fixture()
def policy_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".deepwork" / "tool_requirements"
    d.mkdir(parents=True)
    return d


def _write_policy(path: Path, data: dict) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


class TestParsePolicy:
    def test_basic_policy(self, policy_dir: Path) -> None:
        data = {
            "summary": "Test policy",
            "tools": ["shell"],
            "requirements": {
                "no-rm-rf": {
                    "rule": "MUST NOT use rm -rf /",
                    "no_exception": True,
                },
                "prefer-safe": {
                    "rule": "SHOULD prefer safe alternatives",
                },
            },
        }
        path = _write_policy(policy_dir / "test.yml", data)
        policy = parse_policy_file(path)

        assert policy.name == "test"
        assert policy.summary == "Test policy"
        assert policy.tools == ["shell"]
        assert len(policy.requirements) == 2
        assert policy.requirements["no-rm-rf"].rule == "MUST NOT use rm -rf /"
        assert policy.requirements["no-rm-rf"].no_exception is True
        assert policy.requirements["prefer-safe"].no_exception is False

    def test_policy_with_match(self, policy_dir: Path) -> None:
        data = {
            "tools": ["shell"],
            "match": {"command": "rm "},
            "requirements": {"r1": {"rule": "MUST check"}},
        }
        path = _write_policy(policy_dir / "match.yml", data)
        policy = parse_policy_file(path)

        assert policy.match == {"command": "rm "}

    def test_policy_with_extends(self, policy_dir: Path) -> None:
        data = {
            "tools": ["shell"],
            "extends": ["common"],
            "requirements": {"r1": {"rule": "MUST check"}},
        }
        path = _write_policy(policy_dir / "child.yml", data)
        policy = parse_policy_file(path)

        assert policy.extends == ["common"]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ToolRequirementsError, match="File not found"):
            parse_policy_file(tmp_path / "nonexistent.yml")

    def test_empty_file_raises(self, policy_dir: Path) -> None:
        path = policy_dir / "empty.yml"
        path.write_text("")
        with pytest.raises(ToolRequirementsError, match="Empty policy"):
            parse_policy_file(path)

    def test_missing_required_fields_raises(self, policy_dir: Path) -> None:
        data = {"summary": "no tools or requirements"}
        path = _write_policy(policy_dir / "bad.yml", data)
        with pytest.raises(ToolRequirementsError, match="Schema validation failed"):
            parse_policy_file(path)

    def test_invalid_requirement_structure_raises(self, policy_dir: Path) -> None:
        data = {
            "tools": ["shell"],
            "requirements": {"r1": "just a string, not a dict"},
        }
        path = _write_policy(policy_dir / "bad2.yml", data)
        with pytest.raises(ToolRequirementsError, match="Schema validation failed"):
            parse_policy_file(path)

    def test_no_exception_defaults_false(self, policy_dir: Path) -> None:
        data = {
            "tools": ["write_file"],
            "requirements": {"r1": {"rule": "SHOULD do something"}},
        }
        path = _write_policy(policy_dir / "defaults.yml", data)
        policy = parse_policy_file(path)

        assert policy.requirements["r1"].no_exception is False

    def test_multiple_tools(self, policy_dir: Path) -> None:
        data = {
            "tools": ["shell", "write_file", "edit_file"],
            "requirements": {"r1": {"rule": "MUST check"}},
        }
        path = _write_policy(policy_dir / "multi.yml", data)
        policy = parse_policy_file(path)

        assert policy.tools == ["shell", "write_file", "edit_file"]
