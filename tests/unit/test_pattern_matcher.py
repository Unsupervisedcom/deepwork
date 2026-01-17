"""Tests for pattern matching with variable extraction."""

import pytest

from deepwork.core.pattern_matcher import (
    PatternError,
    match_pattern,
    matches_any_pattern,
    matches_glob,
    resolve_pattern,
    validate_pattern,
)


class TestBasicGlobPatterns:
    """Tests for basic glob pattern matching (PM-1.1.x from test_scenarios.md)."""

    def test_exact_match(self) -> None:
        """PM-1.1.1: Exact match."""
        assert matches_glob("README.md", "README.md")

    def test_exact_no_match(self) -> None:
        """PM-1.1.2: Exact no match (case sensitive)."""
        assert not matches_glob("readme.md", "README.md")

    def test_single_wildcard(self) -> None:
        """PM-1.1.3: Single wildcard."""
        assert matches_glob("main.py", "*.py")

    def test_single_wildcard_nested(self) -> None:
        """PM-1.1.4: Single wildcard - fnmatch matches nested paths too.

        Note: Standard fnmatch does match across directory separators.
        Use **/*.py pattern to explicitly require directory prefixes.
        """
        # fnmatch's * matches any character including /
        # This is different from shell glob behavior
        assert matches_glob("src/main.py", "*.py")

    def test_double_wildcard(self) -> None:
        """PM-1.1.5: Double wildcard matches nested paths."""
        assert matches_glob("src/main.py", "**/*.py")

    def test_double_wildcard_deep(self) -> None:
        """PM-1.1.6: Double wildcard matches deeply nested paths."""
        assert matches_glob("src/a/b/c/main.py", "**/*.py")

    def test_double_wildcard_root(self) -> None:
        """PM-1.1.7: Double wildcard matches root-level files."""
        assert matches_glob("main.py", "**/*.py")

    def test_directory_prefix(self) -> None:
        """PM-1.1.8: Directory prefix matching."""
        assert matches_glob("src/foo.py", "src/**/*")

    def test_directory_prefix_deep(self) -> None:
        """PM-1.1.9: Directory prefix matching deeply nested."""
        assert matches_glob("src/a/b/c.py", "src/**/*")

    def test_directory_no_match(self) -> None:
        """PM-1.1.10: Directory prefix no match."""
        assert not matches_glob("lib/foo.py", "src/**/*")

    def test_brace_expansion_ts(self) -> None:
        """PM-1.1.11: Brace expansion - not supported by fnmatch.

        Note: Python's fnmatch doesn't support brace expansion.
        Use matches_any_pattern with multiple patterns instead.
        """
        # fnmatch doesn't support {a,b} syntax
        assert not matches_glob("app.ts", "*.{js,ts}")
        # Use matches_any_pattern for multiple extensions
        assert matches_any_pattern("app.ts", ["*.ts", "*.js"])

    def test_brace_expansion_js(self) -> None:
        """PM-1.1.12: Brace expansion - not supported by fnmatch."""
        assert not matches_glob("app.js", "*.{js,ts}")
        assert matches_any_pattern("app.js", ["*.ts", "*.js"])

    def test_brace_expansion_no_match(self) -> None:
        """PM-1.1.13: Brace expansion no match."""
        # Neither {a,b} syntax nor multiple patterns match
        assert not matches_glob("app.py", "*.{js,ts}")
        assert not matches_any_pattern("app.py", ["*.ts", "*.js"])


class TestVariablePatterns:
    """Tests for variable pattern matching and extraction (PM-1.2.x)."""

    def test_single_var_path(self) -> None:
        """PM-1.2.1: Single variable captures nested path."""
        result = match_pattern("src/{path}.py", "src/foo/bar.py")
        assert result.matched
        assert result.variables == {"path": "foo/bar"}

    def test_single_var_name(self) -> None:
        """PM-1.2.2: Single variable name (non-path)."""
        result = match_pattern("src/{name}.py", "src/utils.py")
        assert result.matched
        assert result.variables == {"name": "utils"}

    def test_name_no_nested(self) -> None:
        """PM-1.2.3: {name} doesn't match nested paths (single segment)."""
        result = match_pattern("src/{name}.py", "src/foo/bar.py")
        # {name} only captures single segment, not nested paths
        assert not result.matched

    def test_two_variables(self) -> None:
        """PM-1.2.4: Two variables in pattern."""
        result = match_pattern("{dir}/{name}.py", "src/main.py")
        assert result.matched
        assert result.variables == {"dir": "src", "name": "main"}

    def test_prefix_and_suffix(self) -> None:
        """PM-1.2.5: Prefix and suffix around variable."""
        result = match_pattern("test_{name}_test.py", "test_foo_test.py")
        assert result.matched
        assert result.variables == {"name": "foo"}

    def test_nested_path_variable(self) -> None:
        """PM-1.2.6: Nested path in middle."""
        result = match_pattern("src/{path}/index.py", "src/a/b/index.py")
        assert result.matched
        assert result.variables == {"path": "a/b"}

    def test_explicit_multi_segment(self) -> None:
        """PM-1.2.7: Explicit {**mod} for multi-segment."""
        result = match_pattern("src/{**mod}/main.py", "src/a/b/c/main.py")
        assert result.matched
        assert result.variables == {"mod": "a/b/c"}

    def test_explicit_single_segment(self) -> None:
        """PM-1.2.8: Explicit {*name} for single segment."""
        result = match_pattern("src/{*name}.py", "src/utils.py")
        assert result.matched
        assert result.variables == {"name": "utils"}

    def test_mixed_explicit(self) -> None:
        """PM-1.2.9: Mixed explicit single and multi."""
        result = match_pattern("{*dir}/{**path}.py", "src/a/b/c.py")
        assert result.matched
        assert result.variables == {"dir": "src", "path": "a/b/c"}


class TestPatternResolution:
    """Tests for pattern resolution / substitution (PM-1.3.x)."""

    def test_simple_substitution(self) -> None:
        """PM-1.3.1: Simple variable substitution."""
        result = resolve_pattern("tests/{path}_test.py", {"path": "foo"})
        assert result == "tests/foo_test.py"

    def test_nested_path_substitution(self) -> None:
        """PM-1.3.2: Nested path substitution."""
        result = resolve_pattern("tests/{path}_test.py", {"path": "a/b/c"})
        assert result == "tests/a/b/c_test.py"

    def test_multiple_vars_substitution(self) -> None:
        """PM-1.3.3: Multiple variables substitution."""
        result = resolve_pattern("{dir}/test_{name}.py", {"dir": "tests", "name": "foo"})
        assert result == "tests/test_foo.py"


class TestPatternValidation:
    """Tests for pattern syntax validation (SV-8.3.x)."""

    def test_unclosed_brace(self) -> None:
        """SV-8.3.1: Unclosed brace."""
        with pytest.raises(PatternError, match="Unclosed brace|unclosed brace"):
            validate_pattern("src/{path.py")

    def test_empty_variable(self) -> None:
        """SV-8.3.2: Empty variable name."""
        with pytest.raises(PatternError, match="[Ee]mpty variable name"):
            validate_pattern("src/{}.py")

    def test_invalid_chars_in_var(self) -> None:
        """SV-8.3.3: Invalid characters in variable name."""
        with pytest.raises(PatternError, match="[Ii]nvalid"):
            validate_pattern("src/{path/name}.py")

    def test_duplicate_variable(self) -> None:
        """SV-8.3.4: Duplicate variable name."""
        with pytest.raises(PatternError, match="[Dd]uplicate"):
            validate_pattern("{path}/{path}.py")


class TestMatchesAnyPattern:
    """Tests for matches_any_pattern function."""

    def test_matches_first_pattern(self) -> None:
        """Match against first of multiple patterns."""
        assert matches_any_pattern("file.py", ["*.py", "*.js"])

    def test_matches_second_pattern(self) -> None:
        """Match against second of multiple patterns."""
        assert matches_any_pattern("file.js", ["*.py", "*.js"])

    def test_no_match(self) -> None:
        """No match in any pattern."""
        assert not matches_any_pattern("file.txt", ["*.py", "*.js"])

    def test_empty_patterns(self) -> None:
        """Empty patterns list never matches."""
        assert not matches_any_pattern("file.py", [])
