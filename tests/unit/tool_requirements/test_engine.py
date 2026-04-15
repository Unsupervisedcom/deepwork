"""Tests for tool requirements engine."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from deepwork.tool_requirements.config import Requirement
from deepwork.tool_requirements.engine import ToolRequirementsEngine
from deepwork.tool_requirements.evaluator import RequirementEvaluator, RequirementVerdict


class MockEvaluator(RequirementEvaluator):
    """Test evaluator that returns preconfigured verdicts."""

    def __init__(self, verdicts: list[RequirementVerdict] | None = None) -> None:
        self._verdicts = verdicts or []
        self.call_count = 0
        self.last_justifications: dict[str, str] | None = None

    async def evaluate(
        self,
        requirements: dict[str, Requirement],
        tool_name: str,
        tool_input: dict[str, Any],
        justifications: dict[str, str] | None = None,
    ) -> list[RequirementVerdict]:
        self.call_count += 1
        self.last_justifications = justifications
        if self._verdicts:
            return self._verdicts
        # Default: all pass
        return [RequirementVerdict(req_id, True, "OK") for req_id in requirements]


def _setup_project(tmp_path: Path, policies: dict[str, dict]) -> Path:
    policy_dir = tmp_path / ".deepwork" / "tool_requirements"
    policy_dir.mkdir(parents=True)
    for name, data in policies.items():
        (policy_dir / f"{name}.yml").write_text(yaml.safe_dump(data, sort_keys=False))
    return tmp_path


class TestEngineCheck:
    @pytest.mark.asyncio()
    async def test_no_policies_allows(self, tmp_path: Path) -> None:
        engine = ToolRequirementsEngine(tmp_path, MockEvaluator())
        result = await engine.check("shell", {"command": "ls"})
        assert result.allowed is True

    @pytest.mark.asyncio()
    async def test_no_matching_policies_allows(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "write_rules": {
                    "tools": ["write_file"],
                    "requirements": {"r1": {"rule": "MUST check"}},
                }
            },
        )
        engine = ToolRequirementsEngine(project, MockEvaluator())
        result = await engine.check("shell", {"command": "ls"})
        assert result.allowed is True

    @pytest.mark.asyncio()
    async def test_all_pass_allows_and_caches(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "bash_rules": {
                    "tools": ["shell"],
                    "requirements": {"r1": {"rule": "MUST check"}},
                }
            },
        )
        evaluator = MockEvaluator()
        engine = ToolRequirementsEngine(project, evaluator)

        result = await engine.check("shell", {"command": "ls"})
        assert result.allowed is True
        assert evaluator.call_count == 1

        # Second call should be cached
        result2 = await engine.check("shell", {"command": "ls"})
        assert result2.allowed is True
        assert evaluator.call_count == 1  # Not called again

    @pytest.mark.asyncio()
    async def test_failure_denies_with_all_errors(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {
                        "r1": {"rule": "MUST do A"},
                        "r2": {"rule": "MUST do B"},
                    },
                }
            },
        )
        evaluator = MockEvaluator(
            verdicts=[
                RequirementVerdict("r1", False, "Failed A"),
                RequirementVerdict("r2", False, "Failed B"),
            ]
        )
        engine = ToolRequirementsEngine(project, evaluator)

        result = await engine.check("shell", {"command": "bad"})
        assert result.allowed is False
        assert "r1" in result.reason
        assert "r2" in result.reason
        assert "Failed A" in result.reason
        assert "Failed B" in result.reason
        assert set(result.failed_checks) == {"r1", "r2"}

    @pytest.mark.asyncio()
    async def test_no_exception_label_in_error(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {
                        "r1": {"rule": "MUST check", "no_exception": True},
                    },
                }
            },
        )
        evaluator = MockEvaluator(
            verdicts=[
                RequirementVerdict("r1", False, "Blocked"),
            ]
        )
        engine = ToolRequirementsEngine(project, evaluator)

        result = await engine.check("shell", {"command": "bad"})
        assert "NO EXCEPTION" in result.reason


class TestEngineAppeal:
    @pytest.mark.asyncio()
    async def test_successful_appeal_caches(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {
                        "r1": {"rule": "SHOULD check"},
                    },
                }
            },
        )
        evaluator = MockEvaluator()  # All pass by default
        engine = ToolRequirementsEngine(project, evaluator)

        result = await engine.appeal(
            "shell",
            {"command": "rm file"},
            justifications={"r1": "It's a temp file"},
        )
        assert result.passed is True
        assert evaluator.last_justifications == {"r1": "It's a temp file"}

        # Should be cached now
        check = await engine.check("shell", {"command": "rm file"})
        assert check.allowed is True

    @pytest.mark.asyncio()
    async def test_no_exception_blocks_appeal(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {
                        "r1": {"rule": "MUST NOT", "no_exception": True},
                    },
                }
            },
        )
        engine = ToolRequirementsEngine(project, MockEvaluator())

        result = await engine.appeal(
            "shell",
            {"command": "bad"},
            justifications={"r1": "Please?"},
        )
        assert result.passed is False
        assert "no_exception" in result.reason.lower()
        assert "r1" in result.no_exception_blocked

    @pytest.mark.asyncio()
    async def test_empty_justifications_rejected(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {"r1": {"rule": "MUST check"}},
                }
            },
        )
        engine = ToolRequirementsEngine(project, MockEvaluator())

        result = await engine.appeal("shell", {"command": "bad"}, justifications={})
        assert result.passed is False

    @pytest.mark.asyncio()
    async def test_failed_appeal_not_cached(self, tmp_path: Path) -> None:
        project = _setup_project(
            tmp_path,
            {
                "rules": {
                    "tools": ["shell"],
                    "requirements": {"r1": {"rule": "MUST check"}},
                }
            },
        )
        evaluator = MockEvaluator(
            verdicts=[
                RequirementVerdict("r1", False, "Still bad"),
            ]
        )
        engine = ToolRequirementsEngine(project, evaluator)

        result = await engine.appeal(
            "shell",
            {"command": "bad"},
            justifications={"r1": "Please"},
        )
        assert result.passed is False

        # Should NOT be cached
        cache_key = engine.cache.make_key("shell", {"command": "bad"})
        assert not engine.cache.is_approved(cache_key)
