"""Tests for tool requirements discovery and inheritance."""

from pathlib import Path

import pytest
import yaml

from deepwork.tool_requirements.discovery import load_all_policies


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / ".deepwork" / "tool_requirements").mkdir(parents=True)
    return tmp_path


def _write_policy(project: Path, name: str, data: dict) -> Path:
    path = project / ".deepwork" / "tool_requirements" / f"{name}.yml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


class TestLoadAllPolicies:
    def test_no_policy_dir(self, tmp_path: Path) -> None:
        assert load_all_policies(tmp_path) == []

    def test_empty_dir(self, project: Path) -> None:
        assert load_all_policies(project) == []

    def test_single_policy(self, project: Path) -> None:
        _write_policy(project, "bash_safety", {
            "tools": ["shell"],
            "requirements": {"r1": {"rule": "MUST check"}},
        })
        policies = load_all_policies(project)
        assert len(policies) == 1
        assert policies[0].name == "bash_safety"

    def test_multiple_policies(self, project: Path) -> None:
        _write_policy(project, "bash_safety", {
            "tools": ["shell"],
            "requirements": {"r1": {"rule": "MUST check"}},
        })
        _write_policy(project, "write_safety", {
            "tools": ["write_file"],
            "requirements": {"r2": {"rule": "SHOULD verify"}},
        })
        policies = load_all_policies(project)
        assert len(policies) == 2
        names = {p.name for p in policies}
        assert names == {"bash_safety", "write_safety"}

    def test_bad_file_skipped(self, project: Path) -> None:
        _write_policy(project, "good", {
            "tools": ["shell"],
            "requirements": {"r1": {"rule": "MUST check"}},
        })
        # Write invalid YAML
        bad = project / ".deepwork" / "tool_requirements" / "bad.yml"
        bad.write_text("tools: !!invalid")

        policies = load_all_policies(project)
        assert len(policies) == 1
        assert policies[0].name == "good"


class TestInheritance:
    def test_extends_merges_requirements(self, project: Path) -> None:
        _write_policy(project, "parent", {
            "tools": ["shell"],
            "requirements": {
                "parent-req": {"rule": "MUST do parent thing"},
            },
        })
        _write_policy(project, "child", {
            "tools": ["shell"],
            "extends": ["parent"],
            "requirements": {
                "child-req": {"rule": "MUST do child thing"},
            },
        })
        policies = load_all_policies(project)
        child = next(p for p in policies if p.name == "child")
        assert "parent-req" in child.requirements
        assert "child-req" in child.requirements

    def test_child_overrides_parent(self, project: Path) -> None:
        _write_policy(project, "parent", {
            "tools": ["shell"],
            "requirements": {
                "shared": {"rule": "Parent version", "no_exception": True},
            },
        })
        _write_policy(project, "child", {
            "tools": ["shell"],
            "extends": ["parent"],
            "requirements": {
                "shared": {"rule": "Child version"},
            },
        })
        policies = load_all_policies(project)
        child = next(p for p in policies if p.name == "child")
        assert child.requirements["shared"].rule == "Child version"
        assert child.requirements["shared"].no_exception is False

    def test_unknown_parent_ignored(self, project: Path) -> None:
        _write_policy(project, "child", {
            "tools": ["shell"],
            "extends": ["nonexistent"],
            "requirements": {
                "r1": {"rule": "MUST check"},
            },
        })
        policies = load_all_policies(project)
        assert len(policies) == 1
        assert "r1" in policies[0].requirements
