# deepwork-jobs Expert Review

**PR**: #192 - feat: Add experts system for auto-improving domain knowledge
**Date**: 2026-02-01
**Reviewer**: deepwork-jobs expert

## Summary

The experts system is a well-designed addition to DeepWork that follows established patterns from the jobs system. The architecture cleanly separates concerns across schema definition (`expert_schema.py`), parsing (`experts_parser.py`), generation (`experts_generator.py`), and CLI (`experts.py`). The use of dynamic command embedding (`$(deepwork topics ...)`) in the generated agent template is an elegant solution for keeping expert agents up-to-date without regenerating them.

From a DeepWork Jobs perspective, this integration is solid. The experts system complements jobs by providing domain knowledge that can be leveraged during job execution. The sync command properly handles both jobs and experts, and the naming conventions (`dwe_` prefix for expert agents) avoid conflicts with job-generated skills.

## Issues Found

### Issue 1
- **File**: `src/deepwork/schemas/expert_schema.py`
- **Line(s)**: 22, 50, 75
- **Severity**: Minor
- **Issue**: The `additionalProperties: False` constraint on all three schemas is strict and may cause friction when evolving the schema. For example, if users want to add custom metadata fields to topics or learnings (like `author`, `tags`, or `priority`), they would get validation errors.
- **Suggestion**: Consider whether this strictness is intentional. If extensibility is desired, either remove `additionalProperties: False` or document clearly that custom fields are not supported. The jobs schema (`JOB_SCHEMA`) also uses `additionalProperties: False`, so this is consistent with existing patterns.

### Issue 2
- **File**: `src/deepwork/core/experts_parser.py`
- **Line(s)**: 377-379, 387-389
- **Severity**: Minor
- **Issue**: The exception handling for topic/learning parsing re-raises `ExpertParseError` with a bare `raise`. This works but loses context about which file caused the error. The error message is already set in `parse_topic_file`/`parse_learning_file`, but the pattern is unusual.
- **Suggestion**: Consider either removing the try/except entirely (letting errors propagate naturally) or adding file context to the error message.

### Issue 3
- **File**: `src/deepwork/core/experts_generator.py`
- **Line(s)**: 77-78
- **Severity**: Suggestion
- **Issue**: The `_build_expert_context` method includes `topics_count` and `learnings_count` but these are not used in the template (`agent-expert.md.jinja`). This is dead code that could confuse future maintainers.
- **Suggestion**: Either remove these unused context variables or add them to the template if there is a future use case (e.g., showing counts in agent description).

### Issue 4
- **File**: `src/deepwork/templates/claude/agent-expert.md.jinja`
- **Line(s)**: 14
- **Severity**: Minor
- **Issue**: The `truncate(200)` filter is applied after `replace('\n', ' ')`, which means the 200-character limit includes any spaces that replaced newlines. A multiline description might get truncated unexpectedly short if it has many newlines.
- **Suggestion**: This is likely acceptable behavior, but consider if `truncate(200, killwords=False, end='...')` would be better for cleaner truncation at word boundaries.

### Issue 5
- **File**: `src/deepwork/cli/sync.py`
- **Line(s)**: (expert agent generation section)
- **Severity**: Minor
- **Issue**: Expert agent generation is hardcoded to only run for Claude (`adapter.name == "claude"`). The comment says "agents live in .claude/agents/" but this should be abstracted through the adapter if/when other platforms support agents.
- **Suggestion**: Consider adding an `adapter.supports_agents` property or similar abstraction so this check is not a string comparison. However, this is acceptable for now given Claude is the only platform with agent support.

### Issue 6
- **File**: `src/deepwork/core/experts_parser.py`
- **Line(s)**: 61
- **Severity**: Minor
- **Issue**: The frontmatter regex pattern allows optional trailing content after the closing `---` on the same line, but then requires the closing `---` to be at the start of a line. This could cause parsing issues with edge cases.
- **Suggestion**: The current pattern works correctly for well-formed files. Consider adding a test case for edge cases like trailing whitespace after the closing `---`.

### Issue 7
- **File**: `src/deepwork/standard/experts/deepwork_jobs/expert.yml`
- **Line(s)**: 151
- **Severity**: Suggestion
- **Issue**: The expert documentation mentions "Claude Code currently only supports script hooks. Prompt hooks are parsed but not executed (documented limitation)." This is valuable but might become stale if prompt hooks are implemented.
- **Suggestion**: The learning file `prompt_hooks_not_executed.md` already exists in learnings/ which is the right approach. Consider referencing it or adding a note about checking current platform capabilities.

## Code Suggestions

### Suggestion 1: Remove unused context variables

**File**: `src/deepwork/core/experts_generator.py`

Before:
```python
def _build_expert_context(self, expert: ExpertDefinition) -> dict:
    return {
        "expert_name": expert.name,
        "discovery_description": expert.discovery_description,
        "full_expertise": expert.full_expertise,
        "topics_count": len(expert.topics),
        "learnings_count": len(expert.learnings),
    }
```

After:
```python
def _build_expert_context(self, expert: ExpertDefinition) -> dict:
    return {
        "expert_name": expert.name,
        "discovery_description": expert.discovery_description,
        "full_expertise": expert.full_expertise,
    }
```

### Suggestion 2: Simplify redundant exception handling

**File**: `src/deepwork/core/experts_parser.py`

Before:
```python
for topic_file in topics_dir.glob("*.md"):
    try:
        topic = parse_topic_file(topic_file)
        topics.append(topic)
    except ExpertParseError:
        raise
```

After:
```python
for topic_file in topics_dir.glob("*.md"):
    topic = parse_topic_file(topic_file)
    topics.append(topic)
```

The try/except here adds no value since it just re-raises. The `parse_topic_file` function already includes the filename in its error messages.

### Suggestion 3: Add platform abstraction for agent support

**File**: `src/deepwork/core/adapters.py` (add property to `AgentAdapter` base class):

```python
@property
def supports_agents(self) -> bool:
    """Whether this platform supports expert agents."""
    return False

# In ClaudeAdapter:
@property
def supports_agents(self) -> bool:
    return True
```

Then in `sync.py`:
```python
if experts and adapter.supports_agents:
```

## Approval Status

**APPROVED**: No blocking issues

The experts system is well-implemented and follows DeepWork's established patterns. The issues identified are minor improvements that do not block merging. The system correctly:

1. Defines clear schemas for expert, topic, and learning validation
2. Parses expert definitions including nested topics and learnings
3. Generates agent files with dynamic command embedding for up-to-date content
4. Integrates with the sync command to generate expert agents alongside job skills
5. Provides CLI commands (`deepwork topics`, `deepwork learnings`) for dynamic content retrieval
6. Has comprehensive test coverage across unit and integration tests

The architecture cleanly separates the experts system from jobs while allowing them to coexist and complement each other.
