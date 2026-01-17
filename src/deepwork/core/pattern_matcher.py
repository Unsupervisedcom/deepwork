"""Pattern matching with variable extraction for rule file correspondence."""

import re
from dataclasses import dataclass
from fnmatch import fnmatch


class PatternError(Exception):
    """Exception raised for invalid pattern syntax."""

    pass


@dataclass
class MatchResult:
    """Result of matching a file against a pattern."""

    matched: bool
    variables: dict[str, str]  # Captured variable values

    @classmethod
    def no_match(cls) -> "MatchResult":
        return cls(matched=False, variables={})

    @classmethod
    def match(cls, variables: dict[str, str] | None = None) -> "MatchResult":
        return cls(matched=True, variables=variables or {})


def validate_pattern(pattern: str) -> None:
    """
    Validate pattern syntax.

    Raises:
        PatternError: If pattern has invalid syntax
    """
    # Check for unbalanced braces
    brace_depth = 0
    for i, char in enumerate(pattern):
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
            if brace_depth < 0:
                raise PatternError(f"Unmatched closing brace at position {i}")

    if brace_depth > 0:
        raise PatternError("Unclosed brace in pattern")

    # Extract and validate variable names
    var_pattern = r"\{([^}]*)\}"
    seen_vars: set[str] = set()

    for match in re.finditer(var_pattern, pattern):
        var_name = match.group(1)

        # Check for empty variable name
        if not var_name:
            raise PatternError("Empty variable name in pattern")

        # Strip leading ** or * for validation
        clean_name = var_name.lstrip("*")
        if not clean_name:
            # Just {*} or {**} is valid
            continue

        # Check for invalid characters in variable name
        if "/" in clean_name or "\\" in clean_name:
            raise PatternError(f"Invalid character in variable name: {var_name}")

        # Check for duplicates (use clean name for comparison)
        if clean_name in seen_vars:
            raise PatternError(f"Duplicate variable: {clean_name}")
        seen_vars.add(clean_name)


def pattern_to_regex(pattern: str) -> tuple[str, list[str]]:
    """
    Convert a pattern with {var} placeholders to a regex.

    Variables:
    - {path} or {**name} - Matches multiple path segments (.+)
    - {name} or {*name} - Matches single path segment ([^/]+)

    Args:
        pattern: Pattern string like "src/{path}.py"

    Returns:
        Tuple of (regex_pattern, list_of_variable_names)

    Raises:
        PatternError: If pattern has invalid syntax
    """
    validate_pattern(pattern)

    # Normalize path separators
    pattern = pattern.replace("\\", "/")

    result: list[str] = []
    var_names: list[str] = []
    pos = 0

    # Parse pattern segments
    while pos < len(pattern):
        # Look for next variable
        brace_start = pattern.find("{", pos)

        if brace_start == -1:
            # No more variables, escape the rest
            result.append(re.escape(pattern[pos:]))
            break

        # Escape literal part before variable
        if brace_start > pos:
            result.append(re.escape(pattern[pos:brace_start]))

        # Find end of variable
        brace_end = pattern.find("}", brace_start)
        if brace_end == -1:
            raise PatternError("Unclosed brace in pattern")

        var_spec = pattern[brace_start + 1 : brace_end]

        # Determine variable type and name
        if var_spec.startswith("**"):
            # Explicit multi-segment: {**name}
            var_name = var_spec[2:] or "path"
            regex_part = "(?P<{}>.+)".format(re.escape(var_name))
        elif var_spec.startswith("*"):
            # Explicit single-segment: {*name}
            var_name = var_spec[1:] or "name"
            regex_part = "(?P<{}>[^/]+)".format(re.escape(var_name))
        elif var_spec == "path":
            # Conventional multi-segment
            var_name = "path"
            regex_part = "(?P<path>.+)"
        else:
            # Default single-segment (including custom names)
            var_name = var_spec
            regex_part = "(?P<{}>[^/]+)".format(re.escape(var_name))

        result.append(regex_part)
        var_names.append(var_name)
        pos = brace_end + 1

    return "^" + "".join(result) + "$", var_names


def match_pattern(pattern: str, filepath: str) -> MatchResult:
    """
    Match a filepath against a pattern, extracting variables.

    Args:
        pattern: Pattern with {var} placeholders
        filepath: File path to match

    Returns:
        MatchResult with matched=True and captured variables, or matched=False
    """
    # Normalize path separators
    filepath = filepath.replace("\\", "/")

    try:
        regex, _ = pattern_to_regex(pattern)
    except PatternError:
        return MatchResult.no_match()

    match = re.fullmatch(regex, filepath)
    if match:
        return MatchResult.match(match.groupdict())
    return MatchResult.no_match()


def resolve_pattern(pattern: str, variables: dict[str, str]) -> str:
    """
    Substitute variables into a pattern to generate a filepath.

    Args:
        pattern: Pattern with {var} placeholders
        variables: Dict of variable name -> value

    Returns:
        Resolved filepath string
    """
    result = pattern
    for name, value in variables.items():
        # Handle both {name} and {*name} / {**name} forms
        result = result.replace(f"{{{name}}}", value)
        result = result.replace(f"{{*{name}}}", value)
        result = result.replace(f"{{**{name}}}", value)
    return result


def matches_glob(file_path: str, pattern: str) -> bool:
    """
    Match a file path against a glob pattern, supporting ** for recursive matching.

    This is for simple glob patterns without variable capture.

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


def matches_any_pattern(file_path: str, patterns: list[str]) -> bool:
    """
    Check if a file path matches any of the given glob patterns.

    Args:
        file_path: File path to check (relative path)
        patterns: List of glob patterns to match against

    Returns:
        True if the file matches any pattern
    """
    for pattern in patterns:
        if matches_glob(file_path, pattern):
            return True
    return False


def has_variables(pattern: str) -> bool:
    """Check if a pattern contains variable placeholders."""
    return "{" in pattern and "}" in pattern
