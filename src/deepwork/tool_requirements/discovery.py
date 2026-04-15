"""Discovery and loading for tool requirements policy files.

Scans .deepwork/tool_requirements/ for YAML policy files, parses them,
and resolves inheritance via the extends field.
"""

from __future__ import annotations

import logging
from pathlib import Path

from deepwork.tool_requirements.config import (
    Requirement,
    ToolPolicy,
    ToolRequirementsError,
    parse_policy_file,
)

logger = logging.getLogger("deepwork.tool_requirements")


def load_all_policies(project_root: Path) -> list[ToolPolicy]:
    """Load all tool requirement policies from the project.

    Scans .deepwork/tool_requirements/ for *.yml files, parses each,
    and resolves inheritance. Skips files that fail to parse (logged as warnings).

    Args:
        project_root: Path to the project root directory.

    Returns:
        List of parsed and inheritance-resolved ToolPolicy objects.
    """
    policy_dir = project_root / ".deepwork" / "tool_requirements"
    if not policy_dir.is_dir():
        return []

    policies: list[ToolPolicy] = []
    for yml_path in sorted(policy_dir.glob("*.yml")):
        try:
            policy = parse_policy_file(yml_path)
            policies.append(policy)
        except ToolRequirementsError as e:
            logger.warning("Skipping policy %s: %s", yml_path.name, e)

    if policies:
        policies = _resolve_inheritance(policies)

    return policies


def _resolve_inheritance(policies: list[ToolPolicy]) -> list[ToolPolicy]:
    """Resolve extends inheritance for all policies.

    Parent requirements are merged into children. Child requirements
    override parent requirements on key conflict.

    Args:
        policies: List of parsed policies.

    Returns:
        List of policies with inherited requirements merged in.
    """
    by_name: dict[str, ToolPolicy] = {p.name: p for p in policies}
    resolved: dict[str, ToolPolicy] = {}

    def resolve(name: str, visited: set[str]) -> ToolPolicy:
        if name in resolved:
            return resolved[name]

        if name not in by_name:
            logger.warning("Policy '%s' extends unknown policy '%s'", name, name)
            return by_name.get(name, ToolPolicy(name=name, source_path=Path()))

        policy = by_name[name]

        if name in visited:
            logger.warning("Circular inheritance detected for policy '%s'", name)
            return policy

        visited.add(name)

        # Merge parent requirements (parent first, child overrides)
        merged_requirements: dict[str, Requirement] = {}
        for parent_name in policy.extends:
            if parent_name not in by_name:
                logger.warning(
                    "Policy '%s' extends unknown policy '%s'", policy.name, parent_name
                )
                continue
            parent = resolve(parent_name, visited)
            merged_requirements.update(parent.requirements)

        # Child requirements override parent
        merged_requirements.update(policy.requirements)
        policy.requirements = merged_requirements

        resolved[name] = policy
        return policy

    for policy in policies:
        resolve(policy.name, set())

    return policies
