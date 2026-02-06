# experts Expert Review

**PR**: #192 - feat: Add experts system for auto-improving domain knowledge
**Date**: 2026-02-01
**Reviewer**: experts expert

## Summary

This PR implements a well-structured experts system for DeepWork that enables auto-improving domain knowledge repositories. The architecture is clean and follows established patterns in the codebase: JSON schemas for validation, dataclasses for structured data, Jinja2 templates for generation, and Click CLI commands for interaction.

The implementation demonstrates thoughtful design decisions: folder name to expert name conversion (underscores/spaces to dashes), frontmatter-based markdown parsing for topics and learnings, sorted outputs by recency, and dynamic command embedding in generated agents (`$(deepwork topics ...)`) for always-current content. The test coverage is comprehensive with unit tests for schemas, parser, and generator, plus integration tests for the sync workflow.

## Issues Found

### Issue 1
- **File**: `src/deepwork/schemas/expert_schema.py`
- **Line(s)**: 11-20, 30-48, 58-73
- **Severity**: Minor
- **Issue**: The `discovery_description` has guidance to be "1-3 sentences" and `full_expertise` should be "~5 pages max", but there are no maxLength constraints in the schema to enforce or warn about this.
- **Suggestion**: Consider adding `maxLength` constraints or at least documenting the expected limits as schema comments. This would help users understand expectations without causing validation failures.

### Issue 2
- **File**: `src/deepwork/core/experts_parser.py`
- **Line(s)**: 374-379, 384-389
- **Severity**: Minor
- **Issue**: The `except ExpertParseError: raise` pattern is redundant - it catches and immediately re-raises. This works but is unnecessary code.
- **Suggestion**: Remove the try/except blocks entirely since `parse_topic_file` and `parse_learning_file` already raise `ExpertParseError` with appropriate messages.

### Issue 3
- **File**: `src/deepwork/schemas/expert_schema.py`
- **Line(s)**: 46
- **Severity**: Minor
- **Issue**: The date pattern `r"^\d{4}-\d{2}-\d{2}$"` allows invalid dates like "2025-13-45" or "2025-00-00". While PyYAML would fail to parse these as dates, if passed as strings they would pass schema validation.
- **Suggestion**: This is acceptable for now since the schema is primarily for structure validation, but consider adding a note or using ISO 8601 date validation if stricter validation is needed.

### Issue 4
- **File**: `src/deepwork/cli/experts.py`
- **Line(s)**: 111, 113-114, 148, 150-151
- **Severity**: Suggestion
- **Issue**: Success output uses `print()` while errors use `console.print()` with Rich formatting. This is intentional for `$(command)` embedding, but the comment explaining this could be more prominent.
- **Suggestion**: The comment "Print raw output (no Rich formatting) for use in $(command) embedding" is good. Consider adding a similar note to the docstring for clarity.

### Issue 5
- **File**: `src/deepwork/templates/claude/agent-expert.md.jinja`
- **Line(s)**: 14
- **Severity**: Minor
- **Issue**: The description escaping `replace('"', '\\"') | replace('\n', ' ')` handles quotes and newlines, but doesn't handle other YAML special characters like colons, leading special characters, or backslashes that could break YAML parsing.
- **Suggestion**: Consider using a YAML-safe escaping approach or test with edge cases containing `: `, `#`, `[`, `{`, etc. in discovery descriptions.

### Issue 6
- **File**: `src/deepwork/core/experts_generator.py`
- **Line(s)**: 80-90
- **Severity**: Minor
- **Issue**: The `get_agent_filename` method directly uses `expert_name` in the filename without validating it's filesystem-safe. While the folder name conversion should produce safe names, an expert with unusual characters could cause issues.
- **Suggestion**: Add validation or sanitization to ensure the expert name produces a valid filename, or document the assumption that folder names are already safe.

### Issue 7
- **File**: `src/deepwork/templates/claude/agent-expert.md.jinja`
- **Line(s)**: 25, 33
- **Severity**: Suggestion
- **Issue**: The dynamic embedding uses CLI commands that output formatted lists (name + keywords/summary), but the full topic/learning body content is not directly accessible to the agent without the agent reading the files.
- **Suggestion**: This is by design (dynamic loading), but consider documenting that agents should use the Read tool to access full topic/learning content when needed.

## Code Suggestions

### Suggestion 1: Simplify redundant exception handling in parser

**File**: `src/deepwork/core/experts_parser.py`

Before:
```python
for topic_file in topics_dir.glob("*.md"):
    try:
        topic = parse_topic_file(topic_file)
        topics.append(topic)
    except ExpertParseError:
        raise

# Parse learnings
learnings: list[Learning] = []
learnings_dir = expert_dir_path / "learnings"
if learnings_dir.exists() and learnings_dir.is_dir():
    for learning_file in learnings_dir.glob("*.md"):
        try:
            learning = parse_learning_file(learning_file)
            learnings.append(learning)
        except ExpertParseError:
            raise
```

After:
```python
for topic_file in topics_dir.glob("*.md"):
    topic = parse_topic_file(topic_file)
    topics.append(topic)

# Parse learnings
learnings: list[Learning] = []
learnings_dir = expert_dir_path / "learnings"
if learnings_dir.exists() and learnings_dir.is_dir():
    for learning_file in learnings_dir.glob("*.md"):
        learning = parse_learning_file(learning_file)
        learnings.append(learning)
```

### Suggestion 2: Add docstring clarification for raw output in CLI

**File**: `src/deepwork/cli/experts.py`

Before:
```python
def topics(expert: str, path: Path) -> None:
    """
    List topics for an expert.

    Returns a Markdown list of topics with names, file paths as links,
    and keywords, sorted by most-recently-updated.

    Example:
        deepwork topics --expert "rails-activejob"
    """
```

After:
```python
def topics(expert: str, path: Path) -> None:
    """
    List topics for an expert.

    Returns a Markdown list of topics with names, file paths as links,
    and keywords, sorted by most-recently-updated.

    Note: Output is printed without Rich formatting to support
    $(deepwork topics ...) command embedding in agent files.

    Example:
        deepwork topics --expert "rails-activejob"
    """
```

### Suggestion 3: Consider adding schema version field for future evolution

**File**: `src/deepwork/schemas/expert_schema.py`

Consider adding an optional `version` field to enable schema evolution:

```python
EXPERT_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["discovery_description", "full_expertise"],
    "properties": {
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+\.\d+$",
            "description": "Schema version for forward compatibility",
        },
        "discovery_description": {
            # ... existing
        },
        # ...
    },
    "additionalProperties": False,
}
```

## Approval Status

**APPROVED**: No blocking issues

The implementation is well-designed and follows the established patterns in the DeepWork codebase. The minor issues identified are suggestions for improvement rather than problems that need to be fixed before merging. The test coverage is thorough and the documentation (both in code and in the experts expert.yml) is comprehensive.

Key strengths:
- Clean separation of concerns (schema, parser, generator, CLI)
- Comprehensive test coverage across unit and integration tests
- Dynamic embedding design ensures agents always have current topics/learnings
- Self-documenting via the "experts" expert that teaches users how to create experts
- Follows existing codebase conventions (dataclasses, Jinja2, Click)
