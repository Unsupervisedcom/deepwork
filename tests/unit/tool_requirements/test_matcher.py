"""Tests for tool requirements policy matching."""

from pathlib import Path

from deepwork.tool_requirements.config import Requirement, ToolPolicy
from deepwork.tool_requirements.matcher import match_policies, merge_requirements


def _policy(
    name: str = "test",
    tools: list[str] | None = None,
    match: dict[str, str] | None = None,
    requirements: dict[str, Requirement] | None = None,
) -> ToolPolicy:
    return ToolPolicy(
        name=name,
        source_path=Path(f"/fake/{name}.yml"),
        tools=tools or ["shell"],
        match=match or {},
        requirements=requirements or {"r1": Requirement(rule="MUST check")},
    )


class TestMatchPolicies:
    def test_matches_by_tool_name(self) -> None:
        policies = [_policy(tools=["shell"]), _policy(name="other", tools=["write_file"])]
        result = match_policies("shell", {"command": "ls"}, policies)
        assert len(result) == 1
        assert result[0].name == "test"

    def test_no_match_returns_empty(self) -> None:
        policies = [_policy(tools=["write_file"])]
        assert match_policies("shell", {"command": "ls"}, policies) == []

    def test_match_with_param_regex(self) -> None:
        policies = [_policy(tools=["shell"], match={"command": "rm "})]
        assert len(match_policies("shell", {"command": "rm -rf /"}, policies)) == 1
        assert len(match_policies("shell", {"command": "ls -la"}, policies)) == 0

    def test_match_requires_at_least_one_param_hit(self) -> None:
        policies = [_policy(tools=["shell"], match={"command": "rm", "extra": "foo"})]
        # command matches even though extra doesn't
        assert len(match_policies("shell", {"command": "rm file"}, policies)) == 1

    def test_match_no_params_present(self) -> None:
        policies = [_policy(tools=["shell"], match={"command": "rm"})]
        assert len(match_policies("shell", {}, policies)) == 0

    def test_no_match_dict_means_always_match(self) -> None:
        policies = [_policy(tools=["shell"], match={})]
        assert len(match_policies("shell", {"command": "anything"}, policies)) == 1

    def test_invalid_regex_skipped(self) -> None:
        policies = [_policy(tools=["shell"], match={"command": "[invalid"})]
        # Invalid regex is skipped, no match
        assert len(match_policies("shell", {"command": "test"}, policies)) == 0

    def test_multiple_tools_in_policy(self) -> None:
        policies = [_policy(tools=["shell", "write_file"])]
        assert len(match_policies("shell", {}, policies)) == 1
        assert len(match_policies("write_file", {}, policies)) == 1
        assert len(match_policies("read_file", {}, policies)) == 0


class TestMergeRequirements:
    def test_merge_distinct(self) -> None:
        p1 = _policy(name="a", requirements={"r1": Requirement(rule="Rule 1")})
        p2 = _policy(name="b", requirements={"r2": Requirement(rule="Rule 2")})
        merged = merge_requirements([p1, p2])
        assert set(merged.keys()) == {"r1", "r2"}

    def test_first_wins_on_conflict(self) -> None:
        p1 = _policy(name="a", requirements={"r1": Requirement(rule="First")})
        p2 = _policy(name="b", requirements={"r1": Requirement(rule="Second")})
        merged = merge_requirements([p1, p2])
        assert merged["r1"].rule == "First"

    def test_empty_policies(self) -> None:
        assert merge_requirements([]) == {}
