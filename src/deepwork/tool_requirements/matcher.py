"""Matching logic for tool requirements policies.

Determines which policies apply to a given tool call based on
tool name and optional parameter-level regex filtering.
"""

from __future__ import annotations

import re
from typing import Any

from deepwork.tool_requirements.config import Requirement, ToolPolicy


def match_policies(
    tool_name: str,
    tool_input: dict[str, Any],
    policies: list[ToolPolicy],
) -> list[ToolPolicy]:
    """Find all policies that match a tool call.

    Matching is two-step:
    1. Tool name must be in the policy's tools list
    2. If the policy has a match dict, at least one parameter regex must match

    Args:
        tool_name: Normalized tool name (e.g., "shell", "write_file").
        tool_input: The tool's input parameters.
        policies: All loaded policies.

    Returns:
        List of matching policies.
    """
    matched: list[ToolPolicy] = []
    for policy in policies:
        if tool_name not in policy.tools:
            continue
        if policy.match and not _param_matches(tool_input, policy.match):
            continue
        matched.append(policy)
    return matched


def merge_requirements(policies: list[ToolPolicy]) -> dict[str, Requirement]:
    """Merge requirements from all matching policies.

    If the same requirement key appears in multiple policies, the first
    occurrence wins.

    Args:
        policies: List of matched policies.

    Returns:
        Merged requirements dict.
    """
    merged: dict[str, Requirement] = {}
    for policy in policies:
        for req_id, req in policy.requirements.items():
            if req_id not in merged:
                merged[req_id] = req
    return merged


def _param_matches(tool_input: dict[str, Any], match: dict[str, str]) -> bool:
    """Check if any parameter regex matches the tool input.

    Returns True if at least one match entry matches a tool input value.
    """
    for param_name, pattern in match.items():
        value = tool_input.get(param_name)
        if value is None:
            continue
        try:
            if re.search(pattern, str(value)):
                return True
        except re.error:
            continue
    return False
