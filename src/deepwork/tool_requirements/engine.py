"""Tool Requirements Engine — orchestrates check and appeal flows.

This is the central coordinator: loads policies, matches them to tool calls,
evaluates requirements via the LLM evaluator, and manages the cache.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.tool_requirements.cache import ToolRequirementsCache
from deepwork.tool_requirements.config import Requirement
from deepwork.tool_requirements.discovery import load_all_policies
from deepwork.tool_requirements.evaluator import RequirementEvaluator
from deepwork.tool_requirements.matcher import match_policies, merge_requirements

logger = logging.getLogger("deepwork.tool_requirements")


@dataclass
class CheckResult:
    """Result of checking a tool call against policies."""

    allowed: bool
    reason: str
    failed_checks: list[str] = field(default_factory=list)


@dataclass
class AppealResult:
    """Result of an appeal attempt."""

    passed: bool
    reason: str
    no_exception_blocked: list[str] = field(default_factory=list)


class ToolRequirementsEngine:
    """Orchestrates tool requirement checking and appeals."""

    def __init__(
        self,
        project_root: Path,
        evaluator: RequirementEvaluator,
        cache: ToolRequirementsCache | None = None,
    ) -> None:
        self.project_root = project_root
        self.evaluator = evaluator
        self.cache = cache or ToolRequirementsCache()
        self._policies = load_all_policies(project_root)

    def reload_policies(self) -> None:
        """Reload policies from disk."""
        self._policies = load_all_policies(self.project_root)

    async def check(self, tool_name: str, tool_input: dict[str, Any]) -> CheckResult:
        """Check a tool call against all matching policies.

        Args:
            tool_name: Normalized tool name.
            tool_input: Tool call parameters.

        Returns:
            CheckResult with allowed=True if the call is permitted.
        """
        # Check cache first
        cache_key = self.cache.make_key(tool_name, tool_input)
        if self.cache.is_approved(cache_key):
            return CheckResult(allowed=True, reason="Previously approved (cached)")

        # Find matching policies
        matching = match_policies(tool_name, tool_input, self._policies)
        if not matching:
            return CheckResult(allowed=True, reason="No policies match this tool call")

        # Merge all requirements
        all_requirements = merge_requirements(matching)
        if not all_requirements:
            return CheckResult(allowed=True, reason="No requirements to check")

        # Evaluate
        verdicts = await self.evaluator.evaluate(all_requirements, tool_name, tool_input)
        failures = [v for v in verdicts if not v.passed]

        if not failures:
            self.cache.approve(cache_key)
            return CheckResult(allowed=True, reason="All requirements passed")

        # Build error message with ALL failures
        error_lines = ["Tool call blocked by the following policy violations:\n"]
        for failure in failures:
            req = all_requirements.get(failure.requirement_id)
            no_exc = ""
            if req and req.no_exception:
                no_exc = " [NO EXCEPTION - cannot be appealed]"
            error_lines.append(f"- **{failure.requirement_id}**{no_exc}: {failure.explanation}")

        error_lines.append(
            "\nTo appeal, call the `appeal_tool_requirement` MCP tool with:\n"
            "- `tool_name`: the tool that was blocked\n"
            "- `tool_input`: the exact tool_input that was blocked\n"
            "- `policy_justification`: a dict mapping each failed check name "
            "to your justification string"
        )

        return CheckResult(
            allowed=False,
            reason="\n".join(error_lines),
            failed_checks=[f.requirement_id for f in failures],
        )

    async def appeal(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        justifications: dict[str, str],
    ) -> AppealResult:
        """Appeal a tool requirement denial.

        Args:
            tool_name: Normalized tool name.
            tool_input: Tool call parameters.
            justifications: Failed check IDs mapped to justification strings.

        Returns:
            AppealResult with passed=True if the appeal succeeds.
        """
        if not justifications:
            return AppealResult(
                passed=False,
                reason="No justifications provided. Provide a justification for each failed check.",
            )

        # Find matching policies and merge requirements
        matching = match_policies(tool_name, tool_input, self._policies)
        all_requirements = merge_requirements(matching)

        # Check for no_exception rules
        no_exception_blocked: list[str] = []
        appealable: dict[str, Requirement] = {}

        for req_id in justifications:
            if req_id not in all_requirements:
                continue
            req = all_requirements[req_id]
            if req.no_exception:
                no_exception_blocked.append(req_id)
            else:
                appealable[req_id] = req

        if no_exception_blocked:
            return AppealResult(
                passed=False,
                reason=(
                    "Cannot appeal no_exception requirements: " + ", ".join(no_exception_blocked)
                ),
                no_exception_blocked=no_exception_blocked,
            )

        if not appealable:
            return AppealResult(
                passed=False,
                reason="No valid appealable requirements found in justifications.",
            )

        # Re-evaluate with justifications
        verdicts = await self.evaluator.evaluate(
            appealable, tool_name, tool_input, justifications=justifications
        )
        failures = [v for v in verdicts if not v.passed]

        if not failures:
            # Cache the approval so the retried tool call passes
            cache_key = self.cache.make_key(tool_name, tool_input)
            self.cache.approve(cache_key)
            return AppealResult(
                passed=True, reason="Appeal accepted — you may retry the tool call."
            )

        error_lines = ["Appeal denied. The following checks still fail:\n"]
        for failure in failures:
            error_lines.append(f"- **{failure.requirement_id}**: {failure.explanation}")

        return AppealResult(passed=False, reason="\n".join(error_lines))
