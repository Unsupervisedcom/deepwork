"""LLM-based requirement evaluation for tool calls.

Provides an abstract interface for evaluating RFC 2119 requirements
against tool calls, with a concrete Haiku subprocess implementation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from deepwork.tool_requirements.config import Requirement

logger = logging.getLogger("deepwork.tool_requirements")

# Maximum characters of tool_input to include in the prompt
_MAX_INPUT_CHARS = 8000


@dataclass
class RequirementVerdict:
    """Result of evaluating a single requirement."""

    requirement_id: str
    passed: bool
    explanation: str


class RequirementEvaluator(ABC):
    """Abstract interface for requirement evaluation."""

    @abstractmethod
    async def evaluate(
        self,
        requirements: dict[str, Requirement],
        tool_name: str,
        tool_input: dict[str, Any],
        justifications: dict[str, str] | None = None,
    ) -> list[RequirementVerdict]:
        """Evaluate requirements against a tool call.

        Args:
            requirements: Requirements to check (id -> Requirement).
            tool_name: Normalized tool name.
            tool_input: Tool call parameters.
            justifications: Optional justifications for appealed requirements.

        Returns:
            List of verdicts, one per requirement.
        """
        ...


class HaikuSubprocessEvaluator(RequirementEvaluator):
    """Evaluates requirements using Claude Code subprocess with Haiku."""

    async def evaluate(
        self,
        requirements: dict[str, Requirement],
        tool_name: str,
        tool_input: dict[str, Any],
        justifications: dict[str, str] | None = None,
    ) -> list[RequirementVerdict]:
        if not requirements:
            return []

        prompt = _build_prompt(requirements, tool_name, tool_input, justifications)
        raw_result = await self._call_haiku(prompt)
        return _parse_result(raw_result, requirements)

    async def _call_haiku(self, prompt: str) -> str:
        """Call Claude Code in print mode with Haiku model."""
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--model",
            "haiku",
            "--output-format",
            "stream-json",
            "-p",
            prompt,
            "--max-turns",
            "1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Haiku subprocess failed (exit {proc.returncode}): {error_msg}")

        return stdout.decode("utf-8", errors="replace")


def _build_prompt(
    requirements: dict[str, Requirement],
    tool_name: str,
    tool_input: dict[str, Any],
    justifications: dict[str, str] | None = None,
) -> str:
    """Build the evaluation prompt for Haiku."""
    input_str = json.dumps(tool_input, indent=2, default=str)
    if len(input_str) > _MAX_INPUT_CHARS:
        half = _MAX_INPUT_CHARS // 2
        input_str = input_str[:half] + "\n... [truncated] ...\n" + input_str[-half:]

    req_lines = []
    for req_id, req in requirements.items():
        req_lines.append(f"- {req_id}: {req.rule}")

    parts = [
        "You are evaluating whether a tool call complies with a set of requirements.",
        "",
        f"Tool: {tool_name}",
        f"Tool Input:\n```json\n{input_str}\n```",
        "",
        "Requirements to check:",
        *req_lines,
    ]

    if justifications:
        parts.append("")
        parts.append("The agent has provided justifications for why certain requirements should pass:")
        for req_id, justification in justifications.items():
            parts.append(f"- {req_id}: {justification}")

    parts.extend([
        "",
        "For each requirement, determine if the tool call PASSES or FAILS.",
        "Consider RFC 2119 keywords:",
        "- MUST/MUST NOT: strict pass/fail — any violation is a failure",
        "- SHOULD/SHOULD NOT: fail only if the violation is clear and easily avoidable",
        "- MAY: always pass (informational only)",
        "",
        "If justifications are provided, consider them when making your determination.",
        "A good justification can override a SHOULD violation but not a MUST violation.",
        "",
        "Return ONLY a JSON array with no other text:",
        '[{"requirement_id": "...", "passed": true/false, "explanation": "..."}]',
    ])

    return "\n".join(parts)


def _parse_result(
    raw_output: str,
    requirements: dict[str, Requirement],
) -> list[RequirementVerdict]:
    """Parse Haiku's streaming JSON output into verdicts."""
    # stream-json format: one JSON object per line
    # We need to find the result message content
    result_text = ""
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                # Raw JSON array — use as-is
                result_text = line
                continue
            # stream-json emits objects with "type" field
            if obj.get("type") == "result":
                result_text = obj.get("result", "")
                break
            # Also check for assistant message content
            if obj.get("type") == "content":
                content = obj.get("content", "")
                if isinstance(content, str):
                    result_text = content
        except json.JSONDecodeError:
            continue

    if not result_text:
        # Fall back to trying to extract JSON from the raw output
        result_text = raw_output

    # Extract JSON array from the text
    verdicts = _extract_json_array(result_text)
    if verdicts is None:
        # If we can't parse, fail-closed: all requirements fail
        logger.warning("Could not parse evaluator output, failing all requirements")
        return [
            RequirementVerdict(
                requirement_id=req_id,
                passed=False,
                explanation="Failed to parse evaluator response",
            )
            for req_id in requirements
        ]

    result: list[RequirementVerdict] = []
    seen: set[str] = set()
    for item in verdicts:
        req_id = item.get("requirement_id", "")
        if req_id not in requirements or req_id in seen:
            continue
        seen.add(req_id)
        result.append(
            RequirementVerdict(
                requirement_id=req_id,
                passed=bool(item.get("passed", False)),
                explanation=str(item.get("explanation", "")),
            )
        )

    # Any requirements not in the response fail-closed
    for req_id in requirements:
        if req_id not in seen:
            result.append(
                RequirementVerdict(
                    requirement_id=req_id,
                    passed=False,
                    explanation="Requirement not evaluated by the evaluator",
                )
            )

    return result


def _extract_json_array(text: str) -> list[dict[str, Any]] | None:
    """Extract a JSON array from text that may contain surrounding prose."""
    # Try direct parse first
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to find [...] in the text
    start = text.find("[")
    if start == -1:
        return None

    # Find matching closing bracket
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(text[start : i + 1])
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    return None

    return None
