"""Policy definition parser."""

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from deepwork.schemas.policy_schema import POLICY_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class PolicyParseError(Exception):
    """Exception raised for policy parsing errors."""

    pass


# Valid compare_to values
COMPARE_TO_VALUES = frozenset({"base", "default_tip", "prompt"})
DEFAULT_COMPARE_TO = "base"


@dataclass
class Policy:
    """Represents a single policy definition."""

    name: str
    triggers: list[str]  # Normalized to list
    safety: list[str] = field(default_factory=list)  # Normalized to list, empty if not specified
    instructions: str = ""  # Resolved content (either inline or from file)
    compare_to: str = DEFAULT_COMPARE_TO  # What to compare against: base, default_tip, or prompt

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path | None = None) -> "Policy":
        """
        Create Policy from dictionary.

        Args:
            data: Parsed YAML data for a single policy
            base_dir: Base directory for resolving instructions_file paths

        Returns:
            Policy instance

        Raises:
            PolicyParseError: If instructions cannot be resolved
        """
        # Normalize trigger to list
        trigger = data["trigger"]
        triggers = [trigger] if isinstance(trigger, str) else list(trigger)

        # Normalize safety to list (empty if not present)
        safety_data = data.get("safety", [])
        safety = [safety_data] if isinstance(safety_data, str) else list(safety_data)

        # Resolve instructions
        if "instructions" in data:
            instructions = data["instructions"]
        elif "instructions_file" in data:
            if base_dir is None:
                raise PolicyParseError(
                    f"Policy '{data['name']}' uses instructions_file but no base_dir provided"
                )
            instructions_path = base_dir / data["instructions_file"]
            if not instructions_path.exists():
                raise PolicyParseError(
                    f"Policy '{data['name']}' instructions file not found: {instructions_path}"
                )
            try:
                instructions = instructions_path.read_text()
            except Exception as e:
                raise PolicyParseError(
                    f"Policy '{data['name']}' failed to read instructions file: {e}"
                ) from e
        else:
            # Schema should catch this, but be defensive
            raise PolicyParseError(
                f"Policy '{data['name']}' must have either 'instructions' or 'instructions_file'"
            )

        # Get compare_to (defaults to DEFAULT_COMPARE_TO)
        compare_to = data.get("compare_to", DEFAULT_COMPARE_TO)

        return cls(
            name=data["name"],
            triggers=triggers,
            safety=safety,
            instructions=instructions,
            compare_to=compare_to,
        )


def matches_pattern(file_path: str, patterns: list[str]) -> bool:
    """
    Check if a file path matches any of the given glob patterns.

    Args:
        file_path: File path to check (relative path)
        patterns: List of glob patterns to match against

    Returns:
        True if the file matches any pattern
    """
    for pattern in patterns:
        if _matches_glob(file_path, pattern):
            return True
    return False


def _matches_glob(file_path: str, pattern: str) -> bool:
    """
    Match a file path against a glob pattern, supporting ** for recursive matching.

    Args:
        file_path: File path to check
        pattern: Glob pattern (supports *, **, ?)

    Returns:
        True if matches
    """
    # Normalize path separators
    file_path = file_path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    # Handle ** patterns (recursive directory matching)
    if "**" in pattern:
        # Split pattern by **
        parts = pattern.split("**")

        if len(parts) == 2:
            prefix, suffix = parts[0], parts[1]

            # Remove leading/trailing slashes from suffix
            suffix = suffix.lstrip("/")

            # Check if prefix matches the start of the path
            if prefix:
                prefix = prefix.rstrip("/")
                if not file_path.startswith(prefix + "/") and file_path != prefix:
                    return False
                # Get the remaining path after prefix
                remaining = file_path[len(prefix) :].lstrip("/")
            else:
                remaining = file_path

            # If no suffix, any remaining path matches
            if not suffix:
                return True

            # Check if suffix matches the end of any remaining path segment
            # For pattern "src/**/*.py", suffix is "*.py"
            # We need to match *.py against the filename portion
            remaining_parts = remaining.split("/")
            for i in range(len(remaining_parts)):
                test_path = "/".join(remaining_parts[i:])
                if fnmatch(test_path, suffix):
                    return True
                # Also try just the filename
                if fnmatch(remaining_parts[-1], suffix):
                    return True

            return False

    # Simple pattern without **
    return fnmatch(file_path, pattern)


def evaluate_policy(policy: Policy, changed_files: list[str]) -> bool:
    """
    Evaluate whether a policy should fire based on changed files.

    A policy fires if:
    - At least one changed file matches a trigger pattern
    - AND no changed file matches a safety pattern

    Args:
        policy: Policy to evaluate
        changed_files: List of changed file paths (relative)

    Returns:
        True if the policy should fire
    """
    # Check if any trigger matches
    trigger_matched = False
    for file_path in changed_files:
        if matches_pattern(file_path, policy.triggers):
            trigger_matched = True
            break

    if not trigger_matched:
        return False

    # Check if any safety pattern matches
    if policy.safety:
        for file_path in changed_files:
            if matches_pattern(file_path, policy.safety):
                # Safety file was also changed, don't fire
                return False

    return True


def evaluate_policies(
    policies: list[Policy],
    changed_files: list[str],
    promised_policies: set[str] | None = None,
) -> list[Policy]:
    """
    Evaluate which policies should fire.

    Args:
        policies: List of policies to evaluate
        changed_files: List of changed file paths (relative)
        promised_policies: Set of policy names that have been marked as addressed
                          via <promise> tags (these are skipped)

    Returns:
        List of policies that should fire (trigger matches, no safety match, not promised)
    """
    if promised_policies is None:
        promised_policies = set()

    fired_policies = []
    for policy in policies:
        # Skip if already promised/addressed
        if policy.name in promised_policies:
            continue

        if evaluate_policy(policy, changed_files):
            fired_policies.append(policy)

    return fired_policies


def parse_policy_file(policy_path: Path | str, base_dir: Path | None = None) -> list[Policy]:
    """
    Parse policy definitions from a YAML file.

    Args:
        policy_path: Path to .deepwork.policy.yml file
        base_dir: Base directory for resolving instructions_file paths.
                  Defaults to the directory containing the policy file.

    Returns:
        List of parsed Policy objects

    Raises:
        PolicyParseError: If parsing fails or validation errors occur
    """
    policy_path = Path(policy_path)

    if not policy_path.exists():
        raise PolicyParseError(f"Policy file does not exist: {policy_path}")

    if not policy_path.is_file():
        raise PolicyParseError(f"Policy path is not a file: {policy_path}")

    # Default base_dir to policy file's directory
    if base_dir is None:
        base_dir = policy_path.parent

    # Load YAML (policies are stored as a list, not a dict)
    try:
        with open(policy_path, encoding="utf-8") as f:
            policy_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PolicyParseError(f"Failed to parse policy YAML: {e}") from e
    except OSError as e:
        raise PolicyParseError(f"Failed to read policy file: {e}") from e

    # Handle empty file or null content
    if policy_data is None:
        return []

    # Validate it's a list (schema expects array)
    if not isinstance(policy_data, list):
        raise PolicyParseError(
            f"Policy file must contain a list of policies, got {type(policy_data).__name__}"
        )

    # Validate against schema
    try:
        validate_against_schema(policy_data, POLICY_SCHEMA)
    except ValidationError as e:
        raise PolicyParseError(f"Policy definition validation failed: {e}") from e

    # Parse into dataclasses
    policies = []
    for policy_item in policy_data:
        policy = Policy.from_dict(policy_item, base_dir)
        policies.append(policy)

    return policies
