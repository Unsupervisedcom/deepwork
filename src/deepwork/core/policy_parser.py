"""Policy definition parser (v2 - frontmatter markdown format)."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from deepwork.core.pattern_matcher import (
    has_variables,
    match_pattern,
    matches_any_pattern,
    resolve_pattern,
)
from deepwork.schemas.policy_schema import POLICY_FRONTMATTER_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class PolicyParseError(Exception):
    """Exception raised for policy parsing errors."""

    pass


class DetectionMode(Enum):
    """How the policy detects when to fire."""

    TRIGGER_SAFETY = "trigger_safety"  # Fire when trigger matches, safety doesn't
    SET = "set"  # Bidirectional file correspondence
    PAIR = "pair"  # Directional file correspondence


class ActionType(Enum):
    """What happens when the policy fires."""

    PROMPT = "prompt"  # Show instructions to agent (default)
    COMMAND = "command"  # Run an idempotent command


# Valid compare_to values
COMPARE_TO_VALUES = frozenset({"base", "default_tip", "prompt"})
DEFAULT_COMPARE_TO = "base"


@dataclass
class CommandAction:
    """Configuration for command action."""

    command: str  # Command template (supports {file}, {files}, {repo_root})
    run_for: str = "each_match"  # "each_match" or "all_matches"


@dataclass
class PairConfig:
    """Configuration for pair detection mode."""

    trigger: str  # Pattern that triggers
    expects: list[str]  # Patterns for expected corresponding files


@dataclass
class Policy:
    """Represents a single policy definition (v2 format)."""

    # Identity
    name: str  # Human-friendly name (displayed in promise tags)
    filename: str  # Filename without .md extension (used for queue)

    # Detection mode (exactly one must be set)
    detection_mode: DetectionMode
    triggers: list[str] = field(default_factory=list)  # For TRIGGER_SAFETY mode
    safety: list[str] = field(default_factory=list)  # For TRIGGER_SAFETY mode
    set_patterns: list[str] = field(default_factory=list)  # For SET mode
    pair_config: PairConfig | None = None  # For PAIR mode

    # Action type
    action_type: ActionType = ActionType.PROMPT
    instructions: str = ""  # For PROMPT action (markdown body)
    command_action: CommandAction | None = None  # For COMMAND action

    # Common options
    compare_to: str = DEFAULT_COMPARE_TO

    @classmethod
    def from_frontmatter(
        cls,
        frontmatter: dict[str, Any],
        markdown_body: str,
        filename: str,
    ) -> "Policy":
        """
        Create Policy from parsed frontmatter and markdown body.

        Args:
            frontmatter: Parsed YAML frontmatter
            markdown_body: Markdown content after frontmatter
            filename: Filename without .md extension

        Returns:
            Policy instance

        Raises:
            PolicyParseError: If validation fails
        """
        # Get name (required)
        name = frontmatter.get("name", "")
        if not name:
            raise PolicyParseError(f"Policy '{filename}' missing required 'name' field")

        # Determine detection mode
        has_trigger = "trigger" in frontmatter
        has_set = "set" in frontmatter
        has_pair = "pair" in frontmatter

        mode_count = sum([has_trigger, has_set, has_pair])
        if mode_count == 0:
            raise PolicyParseError(f"Policy '{name}' must have 'trigger', 'set', or 'pair'")
        if mode_count > 1:
            raise PolicyParseError(f"Policy '{name}' has multiple detection modes - use only one")

        # Parse based on detection mode
        detection_mode: DetectionMode
        triggers: list[str] = []
        safety: list[str] = []
        set_patterns: list[str] = []
        pair_config: PairConfig | None = None

        if has_trigger:
            detection_mode = DetectionMode.TRIGGER_SAFETY
            trigger = frontmatter["trigger"]
            triggers = [trigger] if isinstance(trigger, str) else list(trigger)
            safety_data = frontmatter.get("safety", [])
            safety = [safety_data] if isinstance(safety_data, str) else list(safety_data)

        elif has_set:
            detection_mode = DetectionMode.SET
            set_patterns = list(frontmatter["set"])
            if len(set_patterns) < 2:
                raise PolicyParseError(f"Policy '{name}' set requires at least 2 patterns")

        elif has_pair:
            detection_mode = DetectionMode.PAIR
            pair_data = frontmatter["pair"]
            expects = pair_data["expects"]
            expects_list = [expects] if isinstance(expects, str) else list(expects)
            pair_config = PairConfig(
                trigger=pair_data["trigger"],
                expects=expects_list,
            )

        # Determine action type
        action_type: ActionType
        command_action: CommandAction | None = None

        if "action" in frontmatter:
            action_type = ActionType.COMMAND
            action_data = frontmatter["action"]
            command_action = CommandAction(
                command=action_data["command"],
                run_for=action_data.get("run_for", "each_match"),
            )
        else:
            action_type = ActionType.PROMPT
            # Markdown body is the instructions
            if not markdown_body.strip():
                raise PolicyParseError(f"Policy '{name}' with prompt action requires markdown body")

        # Get compare_to
        compare_to = frontmatter.get("compare_to", DEFAULT_COMPARE_TO)

        return cls(
            name=name,
            filename=filename,
            detection_mode=detection_mode,
            triggers=triggers,
            safety=safety,
            set_patterns=set_patterns,
            pair_config=pair_config,
            action_type=action_type,
            instructions=markdown_body.strip(),
            command_action=command_action,
            compare_to=compare_to,
        )


def parse_frontmatter_file(filepath: Path) -> tuple[dict[str, Any], str]:
    """
    Parse a markdown file with YAML frontmatter.

    Args:
        filepath: Path to .md file

    Returns:
        Tuple of (frontmatter_dict, markdown_body)

    Raises:
        PolicyParseError: If parsing fails
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError as e:
        raise PolicyParseError(f"Failed to read policy file: {e}") from e

    # Split frontmatter from body
    if not content.startswith("---"):
        raise PolicyParseError(
            f"Policy file '{filepath.name}' must start with '---' frontmatter delimiter"
        )

    # Find end of frontmatter
    end_marker = content.find("\n---", 3)
    if end_marker == -1:
        raise PolicyParseError(
            f"Policy file '{filepath.name}' missing closing '---' frontmatter delimiter"
        )

    frontmatter_str = content[4:end_marker]  # Skip initial "---\n"
    markdown_body = content[end_marker + 4 :]  # Skip "\n---\n" or "\n---"

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise PolicyParseError(f"Invalid YAML frontmatter in '{filepath.name}': {e}") from e

    if frontmatter is None:
        frontmatter = {}

    if not isinstance(frontmatter, dict):
        raise PolicyParseError(
            f"Frontmatter in '{filepath.name}' must be a mapping, got {type(frontmatter).__name__}"
        )

    return frontmatter, markdown_body


def parse_policy_file_v2(filepath: Path) -> Policy:
    """
    Parse a single policy from a frontmatter markdown file.

    Args:
        filepath: Path to .md file in .deepwork/policies/

    Returns:
        Parsed Policy object

    Raises:
        PolicyParseError: If parsing or validation fails
    """
    if not filepath.exists():
        raise PolicyParseError(f"Policy file does not exist: {filepath}")

    if not filepath.is_file():
        raise PolicyParseError(f"Policy path is not a file: {filepath}")

    frontmatter, markdown_body = parse_frontmatter_file(filepath)

    # Validate against schema
    try:
        validate_against_schema(frontmatter, POLICY_FRONTMATTER_SCHEMA)
    except ValidationError as e:
        raise PolicyParseError(f"Policy '{filepath.name}' validation failed: {e}") from e

    # Create Policy object
    filename = filepath.stem  # filename without .md extension
    return Policy.from_frontmatter(frontmatter, markdown_body, filename)


def load_policies_from_directory(policies_dir: Path) -> list[Policy]:
    """
    Load all policies from a directory.

    Args:
        policies_dir: Path to .deepwork/policies/ directory

    Returns:
        List of parsed Policy objects (sorted by filename)

    Raises:
        PolicyParseError: If any policy file fails to parse
    """
    if not policies_dir.exists():
        return []

    if not policies_dir.is_dir():
        raise PolicyParseError(f"Policies path is not a directory: {policies_dir}")

    policies = []
    for filepath in sorted(policies_dir.glob("*.md")):
        policy = parse_policy_file_v2(filepath)
        policies.append(policy)

    return policies


# =============================================================================
# Evaluation Logic
# =============================================================================


def evaluate_trigger_safety(
    policy: Policy,
    changed_files: list[str],
) -> bool:
    """
    Evaluate a trigger/safety mode policy.

    Returns True if policy should fire:
    - At least one changed file matches a trigger pattern
    - AND no changed file matches a safety pattern
    """
    # Check if any trigger matches
    trigger_matched = False
    for file_path in changed_files:
        if matches_any_pattern(file_path, policy.triggers):
            trigger_matched = True
            break

    if not trigger_matched:
        return False

    # Check if any safety pattern matches
    if policy.safety:
        for file_path in changed_files:
            if matches_any_pattern(file_path, policy.safety):
                return False

    return True


def evaluate_set_correspondence(
    policy: Policy,
    changed_files: list[str],
) -> tuple[bool, list[str], list[str]]:
    """
    Evaluate a set (bidirectional correspondence) policy.

    Returns:
        Tuple of (should_fire, trigger_files, missing_files)
        - should_fire: True if correspondence is incomplete
        - trigger_files: Files that triggered (matched a pattern)
        - missing_files: Expected files that didn't change
    """
    trigger_files: list[str] = []
    missing_files: list[str] = []
    changed_set = set(changed_files)

    for file_path in changed_files:
        # Check each pattern in the set
        for pattern in policy.set_patterns:
            result = match_pattern(pattern, file_path)
            if result.matched:
                trigger_files.append(file_path)

                # Check if all other corresponding files also changed
                for other_pattern in policy.set_patterns:
                    if other_pattern == pattern:
                        continue

                    if has_variables(other_pattern):
                        expected = resolve_pattern(other_pattern, result.variables)
                    else:
                        expected = other_pattern

                    if expected not in changed_set:
                        if expected not in missing_files:
                            missing_files.append(expected)

                break  # Only match one pattern per file

    # Policy fires if there are trigger files with missing correspondences
    should_fire = len(trigger_files) > 0 and len(missing_files) > 0
    return should_fire, trigger_files, missing_files


def evaluate_pair_correspondence(
    policy: Policy,
    changed_files: list[str],
) -> tuple[bool, list[str], list[str]]:
    """
    Evaluate a pair (directional correspondence) policy.

    Only trigger-side changes require corresponding expected files.
    Expected-side changes alone do not trigger.

    Returns:
        Tuple of (should_fire, trigger_files, missing_files)
    """
    if policy.pair_config is None:
        return False, [], []

    trigger_files: list[str] = []
    missing_files: list[str] = []
    changed_set = set(changed_files)

    trigger_pattern = policy.pair_config.trigger
    expects_patterns = policy.pair_config.expects

    for file_path in changed_files:
        # Only check trigger pattern (directional)
        result = match_pattern(trigger_pattern, file_path)
        if result.matched:
            trigger_files.append(file_path)

            # Check if all expected files also changed
            for expects_pattern in expects_patterns:
                if has_variables(expects_pattern):
                    expected = resolve_pattern(expects_pattern, result.variables)
                else:
                    expected = expects_pattern

                if expected not in changed_set:
                    if expected not in missing_files:
                        missing_files.append(expected)

    should_fire = len(trigger_files) > 0 and len(missing_files) > 0
    return should_fire, trigger_files, missing_files


@dataclass
class PolicyEvaluationResult:
    """Result of evaluating a single policy."""

    policy: Policy
    should_fire: bool
    trigger_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)  # For set/pair modes


def evaluate_policy(policy: Policy, changed_files: list[str]) -> PolicyEvaluationResult:
    """
    Evaluate whether a policy should fire based on changed files.

    Args:
        policy: Policy to evaluate
        changed_files: List of changed file paths (relative)

    Returns:
        PolicyEvaluationResult with evaluation details
    """
    if policy.detection_mode == DetectionMode.TRIGGER_SAFETY:
        should_fire = evaluate_trigger_safety(policy, changed_files)
        trigger_files = (
            [f for f in changed_files if matches_any_pattern(f, policy.triggers)]
            if should_fire
            else []
        )
        return PolicyEvaluationResult(
            policy=policy,
            should_fire=should_fire,
            trigger_files=trigger_files,
        )

    elif policy.detection_mode == DetectionMode.SET:
        should_fire, trigger_files, missing_files = evaluate_set_correspondence(
            policy, changed_files
        )
        return PolicyEvaluationResult(
            policy=policy,
            should_fire=should_fire,
            trigger_files=trigger_files,
            missing_files=missing_files,
        )

    elif policy.detection_mode == DetectionMode.PAIR:
        should_fire, trigger_files, missing_files = evaluate_pair_correspondence(
            policy, changed_files
        )
        return PolicyEvaluationResult(
            policy=policy,
            should_fire=should_fire,
            trigger_files=trigger_files,
            missing_files=missing_files,
        )

    return PolicyEvaluationResult(policy=policy, should_fire=False)


def evaluate_policies(
    policies: list[Policy],
    changed_files: list[str],
    promised_policies: set[str] | None = None,
) -> list[PolicyEvaluationResult]:
    """
    Evaluate which policies should fire.

    Args:
        policies: List of policies to evaluate
        changed_files: List of changed file paths (relative)
        promised_policies: Set of policy names that have been marked as addressed
                          via <promise> tags (case-insensitive)

    Returns:
        List of PolicyEvaluationResult for policies that should fire
    """
    if promised_policies is None:
        promised_policies = set()

    # Normalize promised names for case-insensitive comparison
    promised_lower = {name.lower() for name in promised_policies}

    results = []
    for policy in policies:
        # Skip if already promised/addressed (case-insensitive)
        if policy.name.lower() in promised_lower:
            continue

        result = evaluate_policy(policy, changed_files)
        if result.should_fire:
            results.append(result)

    return results
